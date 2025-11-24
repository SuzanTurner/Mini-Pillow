# minipil/session.py
from pathlib import Path
from PIL import Image, ImageOps
import json
import os
from typing import Optional

# inside minipil/session.py (only the relevant parts shown)

# Session file location
_SESSION_DIR = Path.home() / ".minipil"
_SESSION_FILE = _SESSION_DIR / "session.json"

class Session:
    def __init__(self):
        self.path: Optional[Path] = None
        self.img: Optional[Image.Image] = None
        self.format: Optional[str] = None
        self._last_actions: dict = {}
        self._load_from_disk()

    def _save_to_disk(self):
        try:
            if not _SESSION_DIR.exists():
                _SESSION_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                "path": str(self.path) if self.path else None,
                "last_actions": getattr(self, "_last_actions", {}) or {}
            }
            with open(_SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _load_from_disk(self):
        try:
            if _SESSION_FILE.exists():
                with open(_SESSION_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                p = data.get("path")
                if p:
                    p = Path(p)
                    if p.exists():
                        self.path = p
                        self.format = p.suffix.replace(".", "").upper() or None
                self._last_actions = data.get("last_actions", {}) or {}
        except Exception:
            self.path = None
            self.img = None
            self.format = None
            self._last_actions = {}


    def load_image(self):
        """
        Actually open the image file and set self.img and self.format.
        Call this before operating on the image.
        """
        if not self.path:
            raise FileNotFoundError("No session path set")
        # Open and normalize orientation and mode
        img = Image.open(self.path)
        img = ImageOps.exif_transpose(img).convert("RGB")
        self.img = img
        self.format = img.format or (self.path.suffix.replace(".", "").upper() or "PNG")
        return img

    def connect(self, path: Path):
        """
        Connect to a new image and persist session to disk.
        Path can be relative; it will be stored as absolute path.
        """
        p = Path(path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"File not found: {p}")
        self.path = p
        # load image now so CLI can show details immediately
        self.load_image()
        self._save_to_disk()
        return self.img

    def is_connected(self) -> bool:
        """
        Consider connected if a valid path exists. If img is None, attempt to load it.
        """
        if self.path and self.path.exists():
            # ensure self.img is loaded in this process
            if self.img is None:
                try:
                    self.load_image()
                except Exception:
                    # if loading fails, treat as not connected
                    return False
            return True
        return False

    def clear(self):
        """
        Clear session both in memory and on disk.
        """
        self.path = None
        self.img = None
        self.format = None
        try:
            if _SESSION_FILE.exists():
                _SESSION_FILE.unlink()
        except Exception:
            pass

# a single shared Session instance imported by your CLI modules
SESSION = Session()
