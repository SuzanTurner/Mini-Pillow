from PIL import Image, ImageOps, ImageEnhance
import io
import os
from typing import Tuple

def resize_preserve_aspect(img: Image.Image, target_w: int=None, target_h: int=None) -> Image.Image:
    w,h = img.size
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
    w,h = img.size
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

def pad_to_size(img: Image.Image, target_w: int, target_h: int, color=(255,255,255)) -> Image.Image:
    out = Image.new("RGB", (target_w, target_h), color)
    w,h = img.size
    left = (target_w - w) // 2
    top = (target_h - h) // 2
    out.paste(img, (left, top))
    return out

def to_grayscale(img: Image.Image) -> Image.Image:
    return ImageOps.grayscale(img).convert("RGB")

def compress_to_target_bytes(img: Image.Image, fmt: str, target_bytes: int, min_q=10, max_q=95) -> bytes:
    """
    Binary-search quality for JPEG/WEBP to reach <= target_bytes if possible.
    Returns bytes of image to write.
    If cannot reach target, returns best effort at min_q.
    """
    fmt_upper = fmt.upper()
    if fmt_upper not in ("JPEG","JPG","WEBP"):
        # Lossless formats like PNG can't be reliably compressed via quality param.
        # For PNG: return default save bytes (no quality).
        buf = io.BytesIO()
        img.save(buf, format=fmt_upper)
        return buf.getvalue()

    lo, hi = min_q, max_q
    best = None
    best_size = None
    while lo <= hi:
        mid = (lo + hi) // 2
        buf = io.BytesIO()
        save_kwargs = {"format": fmt_upper}
        # Pillow uses 'quality' only for JPEG; for WebP use 'quality' too.
        save_kwargs["quality"] = mid
        # allow optimization for JPEG
        if fmt_upper in ("JPEG","JPG"):
            save_kwargs["optimize"] = True
        img.save(buf, **save_kwargs)
        size = buf.tell()
        if size <= target_bytes:
            best = buf.getvalue()
            best_size = size
            lo = mid + 1  # try higher quality
        else:
            hi = mid - 1
    if best is not None:
        return best
    # fallback: save at min_q (lowest quality)
    buf = io.BytesIO()
    save_kwargs = {"format": fmt_upper, "quality": min_q}
    if fmt_upper in ("JPEG","JPG"):
        save_kwargs["optimize"] = True
    img.save(buf, **save_kwargs)
    return buf.getvalue()

def save_image_bytes(img: Image.Image, out_path: str, fmt: str=None, target_bytes: int=None):
    fmt = (fmt or out_path.split('.')[-1]).upper()
    if fmt == "JPG":
        fmt = "JPEG"
    if target_bytes:
        data = compress_to_target_bytes(img, fmt, target_bytes)
        with open(out_path, "wb") as f:
            f.write(data)
        return os.path.getsize(out_path)
    else:
        img.save(out_path, format=fmt)
        return os.path.getsize(out_path)
