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
    try:
        SESSION._save_to_disk()
    except Exception:
        pass
    typer.echo("Edit applied. Use `minipil save [filename]` to write output.")



@app.command()
def save(out: str = typer.Argument(None, help="Output filename (defaults to minipil.png)")):
    """
    Save the currently edited image. If edits were applied in a different process,
    re-load the original file and reapply last actions before writing.
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

    # Reapply last actions if any (this mirrors the 'do' steps)
    actions = getattr(SESSION, "_last_actions", {}) or {}
    img = base_img

    # apply same sequence as in `do`
    if "ratio" in actions:
        a,b = actions["ratio"]
        img = crop_to_ratio(img, a, b)

    if "pixels" in actions:
        w,h = actions["pixels"]
        img = resize_preserve_aspect(img, target_w=w, target_h=h)
    elif "resize_w" in actions or "resize_h" in actions:
        w = actions.get("resize_w")
        h = actions.get("resize_h")
        img = resize_preserve_aspect(img, target_w=w, target_h=h)

    if actions.get("bnw"):
        img = to_grayscale(img)


        # --- additional effects ---
    # invert
    if actions.get("invert"):
        img = invert_image(img)
        typer.echo("Inverted colors")

    # blur
    if "blur" in actions:
        radius = float(actions.get("blur", 2.0))
        img = blur_image(img, radius=radius)
        typer.echo(f"Applied blur radius {radius}")

    # sharpen
    if "sharpen" in actions:
        sval = actions.get("sharpen")
        if isinstance(sval, bool):
            img = sharpen_image(img)
            typer.echo("Applied sharpen (default)")
        else:
            img = sharpen_image(img, radius=float(sval))
            typer.echo(f"Applied sharpen radius {sval}")

    # brightness
    if "brightness" in actions:
        pct = float(actions["brightness"])
        img = adjust_brightness(img, pct)
        typer.echo(f"Adjusted brightness {pct:+.1f}%")

    # contrast
    if "contrast" in actions:
        pct = float(actions["contrast"])
        img = adjust_contrast(img, pct)
        typer.echo(f"Adjusted contrast {pct:+.1f}%")

    # saturation
    if "saturation" in actions:
        pct = float(actions["saturation"])
        img = adjust_saturation(img, pct)
        typer.echo(f"Adjusted saturation {pct:+.1f}%")

    # rotate
    if "rotate" in actions:
        deg = float(actions["rotate"])
        img = rotate_image(img, deg, expand=True)
        typer.echo(f"Rotated {deg} degrees")

    # flip
    if actions.get("flip_h"):
        img = flip_horizontal(img)
        typer.echo("Flipped horizontally")
    if actions.get("flip_v"):
        img = flip_vertical(img)
        typer.echo("Flipped vertically")


    # Now save
    outname = out or "minipil.png"
    fmt = actions.get("format")
    target_bytes = actions.get("target_bytes")

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
