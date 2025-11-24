from pathlib import Path
from PIL import Image, ImageOps
import io

class Session:
    def __init__(self):
        self.path = None         # Path of connected file
        self.img = None          # PIL Image object
        self.format = None       # current format (e.g., "PNG", "JPEG")
    
    def connect(self, path: Path):
        # load, apply exif transpose to respect orientation
        img = Image.open(path)
        img = ImageOps.exif_transpose(img).convert("RGB")
        self.path = Path(path)
        self.img = img
        self.format = img.format or "PNG"
        return img

    def is_connected(self):
        return self.img is not None

SESSION = Session()
