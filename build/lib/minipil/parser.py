import re
from typing import Dict, Any

UNIT_MULTIPLIER = {"kb": 1024, "mb": 1024*1024}

def _parse_size_token(tok: str):
    m = re.match(r"(\d+(?:\.\d+)?)\s*(kb|mb)?", tok, re.I)
    if not m:
        return None
    val = float(m.group(1))
    unit = m.group(2).lower() if m.group(2) else None
    if unit:
        return int(val * UNIT_MULTIPLIER[unit])
    # treat as bytes if no unit
    return int(val)

def parse_nl(text: str) -> Dict[str, Any]:
    """
    Parse a free-text command and return actions/options.
    Returns dict with keys: pixels, ratio, target_bytes, format, bnw, resize_w/resize_h
    """
    t = text.lower()
    actions = {}

    # pixels like "413x531" or "pixels 413x531"
    m = re.search(r"(\b|\s)(\d{2,5})\s*[x×\*]\s*(\d{2,5})(\b|\s)", t)
    if m:
        actions["pixels"] = (int(m.group(2)), int(m.group(3)))

    # ratio like "1:0.8" or "5:4"
    m = re.search(r"(\d+(?:\.\d+)?)\s*[:/x]\s*(\d+(?:\.\d+)?)", t)
    if m:
        # if pixels were matched, avoid overwriting that exact pixel parse
        if "pixels" not in actions:
            try:
                a = float(m.group(1)); b = float(m.group(2))
                actions["ratio"] = (a, b)
            except:
                pass

    # size like "size 400kb" or "target 100 kb"
    m = re.search(r"(size|target|max)\s*(?:is|=|to)?\s*(\d+(?:\.\d+)?\s*(?:kb|mb)?)", t)
    if m:
        sz = _parse_size_token(m.group(2))
        if sz:
            actions["target_bytes"] = sz
    else:
        # alternative "400kb" alone
        m2 = re.search(r"\b(\d+(?:\.\d+)?\s*(?:kb|mb))\b", t)
        if m2:
            sz = _parse_size_token(m2.group(1))
            if sz:
                actions["target_bytes"] = sz

    # format
    m = re.search(r"\b(png|jpeg|jpg|webp)\b", t)
    if m:
        actions["format"] = m.group(1).lower()

    # bnw / grayscale
    if re.search(r"\b(bnw|bw|grayscale|black and white|black-and-white)\b", t):
        actions["bnw"] = True

    # width/height mentions (e.g., width 300, height 400)
    m = re.search(r"width\s*(?:is|=|to)?\s*(\d{2,5})", t)
    if m:
        actions["resize_w"] = int(m.group(1))
    m = re.search(r"height\s*(?:is|=|to)?\s*(\d{2,5})", t)
    if m:
        actions["resize_h"] = int(m.group(1))

    return actions
