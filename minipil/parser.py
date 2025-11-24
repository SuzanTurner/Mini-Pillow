# minipil/parser.py
import re
from typing import Dict, Any

UNIT_MULTIPLIER = {"kb": 1024, "mb": 1024 * 1024}

def _parse_size_token(tok: str):
    """
    Parse tokens like "400kb", "2.5mb" or plain numbers.
    If unit missing, treat plain number as KB (user expectation).
    """
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*(kb|mb)?\s*$", tok, re.I)
    if not m:
        return None
    val = float(m.group(1))
    unit = m.group(2).lower() if m.group(2) else None
    if unit:
        return int(val * UNIT_MULTIPLIER[unit])
    # treat bare number as KB
    return int(val * UNIT_MULTIPLIER["kb"])

def parse_nl(text: str) -> Dict[str, Any]:
    """
    Parse a free-text command and return a dictionary of actions.
    Keys can include: pixels, ratio, target_bytes, format, bnw, resize_w, resize_h
    """
    t = (text or "").lower()
    actions: Dict[str, Any] = {}

    # explicit grayscale commands
    if re.search(r"\b(convert|make|to)\s+(bnw|bw|grayscale|black and white|black-and-white)\b", t):
        actions["bnw"] = True
    elif re.search(r"\b(bnw|bw|grayscale|black and white|black-and-white)\b", t):
        actions["bnw"] = True

    # pixels like "413x531"
    m = re.search(r"\b(\d{2,5})\s*[x×\*]\s*(\d{2,5})\b", t)
    if m:
        actions["pixels"] = (int(m.group(1)), int(m.group(2)))

    # ratio like "1:0.8" (require colon to avoid collision with pixels)
    m = re.search(r"\b(\d+(?:\.\d+)?)\s*[:]\s*(\d+(?:\.\d+)?)\b", t)
    if m and "pixels" not in actions:
        try:
            a = float(m.group(1)); b = float(m.group(2))
            actions["ratio"] = (a, b)
        except ValueError:
            pass

    # size like "size 400kb" or plain "400kb" or "100" (treated as KB)
    m = re.search(r"(?:size|target|max)\s*(?:is|=|to)?\s*(\d+(?:\.\d+)?\s*(?:kb|mb)?)", t)
    if m:
        sz = _parse_size_token(m.group(1))
        if sz:
            actions["target_bytes"] = sz
    else:
        m2 = re.search(r"\b(\d+(?:\.\d+)?\s*(?:kb|mb)?)\b", t)
        if m2:
            sz = _parse_size_token(m2.group(1))
            if sz:
                actions["target_bytes"] = sz

    # format
    m = re.search(r"\b(png|jpeg|jpg|webp)\b", t)
    if m:
        actions["format"] = m.group(1).lower()

    # width/height mentions
    m = re.search(r"\bwidth\s*(?:is|=|to)?\s*(\d{2,5})\b", t)
    if m:
        actions["resize_w"] = int(m.group(1))
    m = re.search(r"\bheight\s*(?:is|=|to)?\s*(\d{2,5})\b", t)
    if m:
        actions["resize_h"] = int(m.group(1))

    # inside parse_nl (after existing matches), add:

    # invert
    if re.search(r"\binvert\b", t):
        actions["invert"] = True

    # blur: "blur 3" or "blur 2.5" or "gaussian blur 3"
    m = re.search(r"\b(?:blur|gaussian blur)\s*(?:radius\s*)?(\d+(?:\.\d+)?)\b", t)
    if m:
        actions["blur"] = float(m.group(1))

    # sharpen: "sharpen" or "sharpen 2"
    m = re.search(r"\bsharpen(?:\s*(\d+(?:\.\d+)?))?\b", t)
    if m:
        if m.group(1):
            actions["sharpen"] = float(m.group(1))
        else:
            actions["sharpen"] = True

    # brightness: "+20%", "brightness +20%", "increase brightness 20%"
    m = re.search(r"\b(?:brightness|bright|brighten|darken|increase brightness|decrease brightness)\b.*?([+-]?\d+(?:\.\d+)?%?)", t)
    if m:
        token = m.group(1)
        if token.endswith('%'):
            percent = float(token.rstrip('%'))
        else:
            percent = float(token)
        # heuristics: "darken" or negative sign implies negative percent
        if re.search(r"\b(darken|decrease)\b", t) and percent > 0:
            percent = -abs(percent)
        actions["brightness"] = percent

    # contrast
    m = re.search(r"\b(?:contrast|increase contrast|decrease contrast)\b.*?([+-]?\d+(?:\.\d+)?%?)", t)
    if m:
        token = m.group(1)
        percent = float(token.rstrip('%'))
        if re.search(r"\b(decrease)\b", t) and percent > 0:
            percent = -abs(percent)
        actions["contrast"] = percent

    # saturation/color boost
    m = re.search(r"\b(?:saturation|saturate|color|colorize|boost color)\b.*?([+-]?\d+(?:\.\d+)?%?)", t)
    if m:
        token = m.group(1)
        percent = float(token.rstrip('%'))
        if re.search(r"\b(decrease|desaturate)\b", t) and percent > 0:
            percent = -abs(percent)
        actions["saturation"] = percent

    # rotate degrees
    m = re.search(r"\brotate\s*([+-]?\d+(?:\.\d+)?)\b", t)
    if m:
        actions["rotate"] = float(m.group(1))

    # flip
    if re.search(r"\bflip\s*(?:horizontal|h)\b", t):
        actions["flip_h"] = True
    if re.search(r"\bflip\s*(?:vertical|v)\b", t):
        actions["flip_v"] = True


    return actions
