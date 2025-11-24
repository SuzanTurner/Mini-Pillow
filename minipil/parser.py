
import re
from typing import Dict, Any

UNIT_MULTIPLIER = {"kb": 1024, "mb": 1024 * 1024}

def _parse_size_token(tok: str):
    m = re.match(r"^\s*([+-]?\d+(?:\.\d+)?)\s*(kb|mb)?\s*$", tok, re.I)
    if not m:
        return None
    val = float(m.group(1))
    unit = m.group(2).lower() if m.group(2) else None
    if unit:
        return int(val * UNIT_MULTIPLIER[unit])
    # treat bare number as KB (user-friendly)
    return int(val * UNIT_MULTIPLIER["kb"])


def _norm(text: str) -> str:
    """Lowercase and normalize common punctuation/words for easier matching."""
    t = text.lower()
    # normalize some synonyms and remove redundant words
    t = t.replace("degrees", "degree")
    t = t.replace("deg.", "degree")
    t = t.replace("degrees.", "degree")
    t = re.sub(r"[,\;]+", " ", t)             # comma/semicolon -> space (split into clauses)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def parse_nl(text: str) -> Dict[str, Any]:
    """
    Rule-based NL parser. Returns dict with keys:
    pixels, ratio, target_bytes, format, bnw, resize_w, resize_h,
    invert, blur, sharpen, brightness, contrast, saturation, rotate, flip_h, flip_v
    """
    t = _norm(text or "")
    actions: Dict[str, Any] = {}

    # split into small clauses by "and" / "then" / "after" or punctuation
    clauses = re.split(r"\band\b|\bthen\b|\bafter\b|\b,\b", t)

    for clause in clauses:
        clause = clause.strip()
        if not clause:
            continue

        # ----- grayscale / bnw -----
        if re.search(r"\b(convert|make|to)\s+(bnw|bw|grayscale|black and white|black-and-white)\b", clause) \
           or re.search(r"\b(bnw|bw|grayscale|black and white|black-and-white)\b", clause):
            actions["bnw"] = True
            continue

        # ----- invert -----
        if re.search(r"\binvert\b", clause):
            actions["invert"] = True
            continue

        # ----- rotate: many natural forms -----
        # matches: "rotate 75", "rotate by 75", "rotate image by 75 degree", "rotate 75 degree"
        m = re.search(r"\brotate\b(?:\s+(?:image|it|the image|the photo))?(?:\s*(?:by)?)\s*([+-]?\d+(?:\.\d+)?)\s*(?:degree)?\b", clause)
        if m:
            actions["rotate"] = float(m.group(1))
            continue
        # also allow "75 degrees" or "rotate 90deg"
        m2 = re.search(r"\b([+-]?\d+(?:\.\d+)?)\s*(?:degree|deg)\b", clause)
        if m2 and "rotate" not in actions:
            # be conservative: only set rotate if clause includes rotate keyword OR clause is short
            if "rotate" in clause or len(clause.split()) <= 3:
                actions["rotate"] = float(m2.group(1))
                continue

        # ----- blur -----
        m = re.search(r"\b(?:blur|gaussian blur)\b(?:\s*(?:radius|r)?)\s*([0-9]*\.?[0-9]+)?", clause)
        if m:
            if m.group(1):
                actions["blur"] = float(m.group(1))
            else:
                actions["blur"] = 2.0
            continue

        # ----- sharpen -----
        m = re.search(r"\bsharpen(?:\s*(?:amount|radius)?)?\s*([0-9]*\.?[0-9]+)?", clause)
        if m:
            if m.group(1):
                actions["sharpen"] = float(m.group(1))
            else:
                actions["sharpen"] = True
            continue

        # ----- brightness (handles "brighten / darken / brightness +20% / +20") -----
        m = re.search(r"\b(?:brightness|brighten|darken|increase brightness|decrease brightness)\b.*?([+-]?\d+(?:\.\d+)?%?)", clause)
        if m:
            token = m.group(1)
            pct = float(token.rstrip("%"))
            # darken/ decrease imply negative
            if re.search(r"\b(darken|decrease)\b", clause) and pct > 0:
                pct = -abs(pct)
            actions["brightness"] = pct
            continue
        # shorthand "brighten 20%" or "brighten by 20%"
        m = re.search(r"\bbrighten\b(?:\s*by)?\s*([+-]?\d+(?:\.\d+)?%?)", clause)
        if m:
            actions["brightness"] = float(m.group(1).rstrip("%"))
            continue

        # ----- contrast -----
        m = re.search(r"\b(?:contrast|increase contrast|decrease contrast)\b.*?([+-]?\d+(?:\.\d+)?%?)", clause)
        if m:
            token = m.group(1)
            pct = float(token.rstrip("%"))
            if re.search(r"\b(decrease)\b", clause) and pct > 0:
                pct = -abs(pct)
            actions["contrast"] = pct
            continue

        # ----- saturation -----
        m = re.search(r"\b(?:saturation|saturate|desaturate|color|boost color)\b.*?([+-]?\d+(?:\.\d+)?%?)", clause)
        if m:
            pct = float(m.group(1).rstrip("%"))
            if re.search(r"\b(desaturate|decrease)\b", clause) and pct > 0:
                pct = -abs(pct)
            actions["saturation"] = pct
            continue

        # ----- flip -----
        if re.search(r"\bflip\b.*\bhorizontal\b|\bflip h\b", clause):
            actions["flip_h"] = True
            continue
        if re.search(r"\bflip\b.*\bvertical\b|\bflip v\b", clause):
            actions["flip_v"] = True
            continue

        # ----- pixels exact (e.g., "400x600" or "resize to 400x600")
        m = re.search(r"\b(\d{2,5})\s*[x×\*]\s*(\d{2,5})\b", clause)
        if m:
            actions["pixels"] = (int(m.group(1)), int(m.group(2)))
            continue

        # ----- width / height single
        m = re.search(r"\bwidth\s*(?:is|=|to|:)?\s*(\d{2,5})\b", clause)
        if m:
            actions["resize_w"] = int(m.group(1))
            continue
        m = re.search(r"\bheight\s*(?:is|=|to|:)?\s*(\d{2,5})\b", clause)
        if m:
            actions["resize_h"] = int(m.group(1))
            continue

        # ----- ratio (require colon to avoid pixels collision)
        m = re.search(r"\b(\d+(?:\.\d+)?)\s*[:]\s*(\d+(?:\.\d+)?)\b", clause)
        if m and "pixels" not in actions:
            actions["ratio"] = (float(m.group(1)), float(m.group(2)))
            continue

        # ----- size / compress
        m = re.search(r"\b(?:size|compress|target|max)\b.*?([0-9]+(?:\.[0-9]+)?\s*(?:kb|mb)?)", clause)
        if m:
            sz = _parse_size_token(m.group(1))
            if sz:
                actions["target_bytes"] = sz
            continue
        # bare size token like "250kb"
        m = re.search(r"\b([0-9]+(?:\.[0-9]+)?\s*(?:kb|mb)?)\b", clause)
        if m and "target_bytes" not in actions:
            sz = _parse_size_token(m.group(1))
            if sz:
                actions["target_bytes"] = sz
            continue

        # ----- format
        m = re.search(r"\b(png|jpeg|jpg|webp)\b", clause)
        if m:
            actions["format"] = m.group(1).lower()
            continue

        # fallback: simple patterns like "invert the image" handled above,
        # otherwise ignore this clause

    return actions

