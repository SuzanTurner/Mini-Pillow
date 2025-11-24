# minipil/cli.py (top)
import typer
from pathlib import Path

from minipil.session import SESSION
from minipil.parser import parse_nl
from minipil.core import (
    resize_preserve_aspect, crop_to_ratio, pad_to_size,
    to_grayscale, save_image_bytes,
    # new effect functions — make sure these exist in minipil/core.py
    invert_image, blur_image, sharpen_image,
    adjust_brightness, adjust_contrast, adjust_saturation,
    rotate_image, flip_horizontal, flip_vertical,
)


app = typer.Typer(help="minipil — lightweight image edits via CLI + simple NL commands")

@app.command()
def connect(path: Path):
    """
    Connect to an image file (absolute or relative path). Persists session to disk.
    """
    if not path.exists():
        typer.echo(f"File not found: {path}")
        raise typer.Exit(code=1)

    try:
        img = SESSION.connect(path)   # loads image and persists session
    except Exception as e:
        typer.echo(f"Failed to connect: {e}")
        raise typer.Exit(code=1)

    typer.echo(f"Connected to: {path.name} ({img.size[0]}x{img.size[1]}, format={SESSION.format})")


@app.command(name="do")
def do(text: str = typer.Argument(..., help='Natural language instruction, e.g. "size 100kb and ratio 1:0.8"')):
    """
    Perform NLP-based image edits on the connected image.
    """
    if not SESSION.is_connected():
        typer.echo("No image connected. Run `minipil connect <file>` first.")
        raise typer.Exit(code=1)

    actions = parse_nl(text)
    img = SESSION.img

    # 1) crop to ratio
    if "ratio" in actions:
        a, b = actions["ratio"]
        img = crop_to_ratio(img, a, b)
        typer.echo(f"Applied ratio crop {a}:{b} -> {img.size[0]}x{img.size[1]}")

    # 2) exact pixel resize
    if "pixels" in actions:
        w, h = actions["pixels"]
        img = resize_preserve_aspect(img, target_w=w, target_h=h)
        typer.echo(f"Resized to exact pixels {w}x{h}")

    # 3) width/height resize (only if pixels not used)
    elif "resize_w" in actions or "resize_h" in actions:
        w = actions.get("resize_w")
        h = actions.get("resize_h")
        img = resize_preserve_aspect(img, target_w=w, target_h=h)
        typer.echo(f"Resized to {img.size[0]}x{img.size[1]} (preserving aspect)")

    # 4) grayscale / bnw
    if actions.get("bnw"):
        img = to_grayscale(img)
        typer.echo("Converted to black & white (grayscale)")

    SESSION.img = img
    SESSION._last_actions = actions
    # Persist last actions (so save in a separate process can reapply)
    # try:
    #     SESSION._save_to_disk()
    # except Exception:
    #     pass
    # typer.echo("Edit applied. Use `minipil save [filename]` to write output.")

    # inside do(...) after applying edits and storing SESSION.img

    # append actions to history (so multiple do commands are cumulative)
    if not hasattr(SESSION, "_actions_history"):
        SESSION._actions_history = []

    # only append non-empty action dicts (defensive)
    if actions:
        SESSION._actions_history.append(actions)

    # persist to disk so save in other process can reapply entire history
    try:
        SESSION._save_to_disk()
    except Exception:
        pass

    typer.echo("Edit applied. Use `minipil save [filename]` to write output.")




@app.command()
def save(out: str = typer.Argument(None, help="Output filename (defaults to minipil.png)")):
    """
    Save the currently edited image. Re-load the original file and replay the full
    actions history (SESSION._actions_history) in order, then write output.
    """
    if not SESSION.path:
        typer.echo("No image connected. Nothing to save.")
        raise typer.Exit(code=1)

    # Load base image from disk (do NOT rely on in-memory SESSION.img which may be stale)
    try:
        base_img = SESSION.load_image()
    except Exception as e:
        typer.echo(f"Failed to open connected image: {e}")
        raise typer.Exit(code=1)

    # Replay full history
    history = getattr(SESSION, "_actions_history", []) or []
    img = base_img

    for actions in history:
        # crop/resize order same as do()
        if "ratio" in actions:
            a, b = actions["ratio"]
            img = crop_to_ratio(img, a, b)

        if "pixels" in actions:
            w, h = actions["pixels"]
            img = resize_preserve_aspect(img, target_w=w, target_h=h)
        elif "resize_w" in actions or "resize_h" in actions:
            w = actions.get("resize_w")
            h = actions.get("resize_h")
            img = resize_preserve_aspect(img, target_w=w, target_h=h)

        if actions.get("bnw"):
            img = to_grayscale(img)

        # additional effects
        if actions.get("invert"):
            img = invert_image(img)
        if "blur" in actions:
            img = blur_image(img, radius=float(actions.get("blur", 2.0)))
        if "sharpen" in actions:
            sval = actions.get("sharpen")
            if isinstance(sval, bool):
                img = sharpen_image(img)
            else:
                img = sharpen_image(img, radius=float(sval))
        if "brightness" in actions:
            img = adjust_brightness(img, float(actions["brightness"]))
        if "contrast" in actions:
            img = adjust_contrast(img, float(actions["contrast"]))
        if "saturation" in actions:
            img = adjust_saturation(img, float(actions["saturation"]))
        if "rotate" in actions:
            img = rotate_image(img, float(actions["rotate"]), expand=True)
        if actions.get("flip_h"):
            img = flip_horizontal(img)
        if actions.get("flip_v"):
            img = flip_vertical(img)

    # Determine final format/target_bytes: last action that specifies them wins
    fmt = None
    target_bytes = None
    for a in history:
        if a.get("format"):
            fmt = a.get("format")
        if a.get("target_bytes"):
            target_bytes = a.get("target_bytes")

    # allow CLI out argument to override format
    outname = out or "minipil.png"
    if "." in outname and not fmt:
        fmt = outname.split(".")[-1].lower()
    if "." not in outname and fmt:
        outname = outname + "." + fmt

    try:
        size = save_image_bytes(img, outname, fmt=fmt, target_bytes=target_bytes)
    except Exception as e:
        typer.echo(f"Save failed: {e}")
        raise typer.Exit(code=1)

    typer.echo(f"Saved -> {outname} ({size} bytes)")



@app.command("clear-session")
def clear_session():
    """
    Clear persisted session (remove saved connected path).
    """
    SESSION.clear()
    typer.echo("Session cleared.")


@app.command("history")
def history():
    h = getattr(SESSION, "_actions_history", []) or []
    if not h:
        typer.echo("No actions in session history.")
        return
    for i, a in enumerate(h, start=1):
        typer.echo(f"{i}: {a}")

@app.command("undo")
def undo():
    h = getattr(SESSION, "_actions_history", []) or []
    if not h:
        typer.echo("Nothing to undo.")
        return
    removed = h.pop()  # remove last action
    SESSION._actions_history = h
    try:
        SESSION._save_to_disk()
    except Exception:
        pass
    typer.echo(f"Undid last action: {removed}")
