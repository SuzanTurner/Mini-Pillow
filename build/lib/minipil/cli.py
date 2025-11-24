import typer
from pathlib import Path
from minipil.session import SESSION
from minipil.parser import parse_nl
from minipil.core import (
    resize_preserve_aspect, crop_to_ratio, pad_to_size,
    to_grayscale, save_image_bytes
)

app = typer.Typer()

@app.command()
def connect(path: Path):
    """
    Connect to an image file in current directory or given path.
    """
    if not path.exists():
        typer.echo(f"File not found: {path}")
        raise typer.Exit(code=1)
    img = SESSION.connect(path)
    typer.echo(f"Connected to: {path.name} ({img.size[0]}x{img.size[1]}, format={SESSION.format})")

@app.command(name="do")
def do(text: str = typer.Argument(..., help="Natural language instruction, e.g. \"size 100kb and ratio 1:0.8\"")):
    """
    Perform NLP-based image edits on the connected image.
    """
    if not SESSION.is_connected():
        typer.echo("No image connected. Run `minipil connect <file>` first.")
        raise typer.Exit(code=1)

    actions = parse_nl(text)
    img = SESSION.img

    # apply operations in a reasonable order
    # 1) crop to ratio
    if "ratio" in actions:
        a,b = actions["ratio"]
        img = crop_to_ratio(img, a, b)
        typer.echo(f"Applied ratio crop {a}:{b} -> {img.size[0]}x{img.size[1]}")

    # 2) exact pixel resize
    if "pixels" in actions:
        w,h = actions["pixels"]
        img = resize_preserve_aspect(img, target_w=w, target_h=h)
        typer.echo(f"Resized to exact pixels {w}x{h}")

    # 3) width/height resize
    elif "resize_w" in actions or "resize_h" in actions:
        w = actions.get("resize_w")
        h = actions.get("resize_h")
        img = resize_preserve_aspect(img, target_w=w, target_h=h)
        typer.echo(f"Resized to {img.size[0]}x{img.size[1]} (preserving aspect)")

    # 4) grayscale/bnw
    if actions.get("bnw"):
        img = to_grayscale(img)
        typer.echo("Converted to black & white (grayscale)")

    # capture parsed options for save (keeps in session.meta)
    SESSION.img = img
    # attach last-parsed options so save can use target_bytes/format by default if user doesn't pass
    SESSION._last_actions = actions
    typer.echo("Edit applied. Use `minipil save [filename]` to write output.")

@app.command()
def save(out: str = typer.Argument(None, help="Output filename (defaults to minipil.png)")):
    """
    Save the currently edited image. Defaults to minipil.png if filename not provided.
    Uses format/size parsed from last `do` if present.
    """
    if not SESSION.is_connected():
        typer.echo("No image connected. Nothing to save.")
        raise typer.Exit(code=1)
    outname = out or "minipil.png"
    actions = getattr(SESSION, "_last_actions", {}) or {}
    fmt = actions.get("format")
    target_bytes = actions.get("target_bytes")

    # derive format from filename if not given
    if "." in outname and not fmt:
        fmt = outname.split(".")[-1].lower()

    # ensure extension matches format
    if "." not in outname and fmt:
        outname = outname + "." + fmt

    size = save_image_bytes(SESSION.img, outname, fmt=fmt, target_bytes=target_bytes)
    typer.echo(f"Saved -> {outname} ({size} bytes)")
