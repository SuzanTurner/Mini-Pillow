# minipil/core.py
from PIL import Image, ImageOps, ImageEnhance
import io
import os
from typing import Tuple, Optional

UNIT_MULTIPLIER = {"kb": 1024, "mb": 1024 * 1024}


def resize_preserve_aspect(img: Image.Image, target_w: int = None, target_h: int = None) -> Image.Image:
    w, h = img.size
    if target_w and target_h:
        return img.resize((target_w, target_h), Image.LANCZOS)
    if target_w:
        new_h = int(h * (target_w / w))
        return img.resize((target_w, new_h), Image.LANCZOS)
    if target_h:
        new_w = int(w * (target_h / h))
        return img.resize((new_w, target_h), Image.LANCZOS)
    return img


def crop_to_ratio(img: Image.Image, rw: float, rh: float, face_box=None) -> Image.Image:
    # center crop to target ratio rw:rh
    w, h = img.size
    target_ratio = rw / rh
    current_ratio = w / h
    if current_ratio > target_ratio:
        # too wide -> crop width
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        box = (left, 0, left + new_w, h)
    else:
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        box = (0, top, w, top + new_h)
    return img.crop(box)


def pad_to_size(img: Image.Image, target_w: int, target_h: int, color=(255, 255, 255)) -> Image.Image:
    out = Image.new("RGB", (target_w, target_h), color)
    w, h = img.size
    left = (target_w - w) // 2
    top = (target_h - h) // 2
    out.paste(img, (left, top))
    return out


def to_grayscale(img: Image.Image) -> Image.Image:
    """
    Deterministic grayscale conversion: convert to luminance (L), then back to RGB.
    """
    return img.convert("RGB").convert("L").convert("RGB")


def compress_to_target_bytes(img: Image.Image, fmt: str, target_bytes: int, min_q=10, max_q=95) -> bytes:
    """
    Binary-search quality for JPEG/WEBP to reach <= target_bytes if possible.
    Returns bytes of image to write. If cannot reach target, returns best effort at min_q.
    """
    fmt_upper = (fmt or "JPEG").upper()
    if fmt_upper == "JPG":
        fmt_upper = "JPEG"

    # For formats that don't accept a 'quality' param (e.g., PNG), just return default bytes.
    if fmt_upper not in ("JPEG", "WEBP"):
        buf = io.BytesIO()
        img.save(buf, format=fmt_upper)
        return buf.getvalue()

    lo, hi = min_q, max_q
    best = None
    best_size = None

    while lo <= hi:
        mid = (lo + hi) // 2
        buf = io.BytesIO()
        save_kwargs = {"format": fmt_upper, "quality": mid}
        # allow optimization for JPEG
        if fmt_upper == "JPEG":
            save_kwargs["optimize"] = True
        # For WebP Pillow uses 'quality' as well.
        img.save(buf, **save_kwargs)
        size = buf.tell()
        if size <= target_bytes:
            best = buf.getvalue()
            best_size = size
            lo = mid + 1  # try a higher quality (still within budget)
        else:
            hi = mid - 1

    if best is not None:
        return best

    # fallback: save at min_q (lowest quality)
    buf = io.BytesIO()
    save_kwargs = {"format": fmt_upper, "quality": min_q}
    if fmt_upper == "JPEG":
        save_kwargs["optimize"] = True
    img.save(buf, **save_kwargs)
    return buf.getvalue()


def save_image_bytes(img: Image.Image, out_path: str, fmt: Optional[str] = None, target_bytes: Optional[int] = None) -> int:
    """
    Save an Image to disk. If target_bytes is given and format supports lossy
    compression (JPEG/WebP), perform binary-search quality compression.
    If target_bytes is requested but format is PNG/other, auto-convert to JPEG
    to honor the size target (documented behavior).
    Returns number of bytes written.
    """
    # Determine format from provided fmt or file extension
    if fmt:
        fmt = fmt.upper()
    else:
        if "." in out_path:
            fmt = out_path.rsplit(".", 1)[1].upper()
        else:
            fmt = "PNG"  # default

    if fmt == "JPG":
        fmt = "JPEG"

    # If user requested target size but chosen format is PNG or other lossless,
    # auto-convert to JPEG so target_bytes can be respected.
    if target_bytes and fmt not in ("JPEG", "WEBP"):
        fmt = "JPEG"

    if target_bytes and fmt in ("JPEG", "WEBP"):
        data = compress_to_target_bytes(img, fmt, target_bytes)
        with open(out_path, "wb") as f:
            f.write(data)
        return os.path.getsize(out_path)
    else:
        # For PNG and other formats use reasonable defaults.
        save_kwargs = {"format": fmt}
        if fmt == "PNG":
            # PNG options
            save_kwargs["optimize"] = True
            # Pillow uses 'compress_level' 0-9
            save_kwargs["compress_level"] = 6
        img.save(out_path, **save_kwargs)
        return os.path.getsize(out_path)
    
# add these imports at top of core.py
from PIL import ImageFilter, ImageChops, ImageEnhance, ImageOps

# ---------- new image-op helpers ----------

def invert_image(img: Image.Image) -> Image.Image:
    """Invert colors (works on RGB)."""
    # ensure mode where inversion makes sense
    if img.mode != "RGB":
        img = img.convert("RGB")
    return ImageChops.invert(img)

def blur_image(img: Image.Image, radius: float = 2.0) -> Image.Image:
    """Gaussian blur with given radius (float)."""
    return img.filter(ImageFilter.GaussianBlur(radius))

def sharpen_image(img: Image.Image, radius: float = 2, percent: int = 150, threshold: int = 3) -> Image.Image:
    """
    Use UnsharpMask for sharpening (Pillow). Defaults reasonable.
    radius: blur radius for mask
    percent: strength factor
    threshold: threshold
    """
    return img.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))

def adjust_brightness(img: Image.Image, percent: float) -> Image.Image:
    """percent is like +20 or -10 (± percentage). Convert to Pillow factor."""
    factor = 1.0 + (percent / 100.0)
    return ImageEnhance.Brightness(img).enhance(factor)

def adjust_contrast(img: Image.Image, percent: float) -> Image.Image:
    factor = 1.0 + (percent / 100.0)
    return ImageEnhance.Contrast(img).enhance(factor)

def adjust_saturation(img: Image.Image, percent: float) -> Image.Image:
    factor = 1.0 + (percent / 100.0)
    return ImageEnhance.Color(img).enhance(factor)

def rotate_image(img: Image.Image, degrees: float, expand: bool = False) -> Image.Image:
    """Rotate (degrees). expand=True will resize canvas to fit."""
    return img.rotate(-degrees, expand=expand)  # negative for clockwise human expectation

def flip_horizontal(img: Image.Image) -> Image.Image:
    return img.transpose(Image.FLIP_LEFT_RIGHT)

def flip_vertical(img: Image.Image) -> Image.Image:
    return img.transpose(Image.FLIP_TOP_BOTTOM)

