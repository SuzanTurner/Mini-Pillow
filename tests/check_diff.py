# check_diff.py
from PIL import Image, ImageChops
from pathlib import Path
import hashlib

orig = Path(r"D:\Yadh\OpenSource\minipillow\image.png")
out = Path(r"D:\Yadh\OpenSource\minipillow\minipil.png")

if not orig.exists():
    print("Original image.png not found.")
    raise SystemExit(1)
if not out.exists():
    print("minipil.png not found.")
    raise SystemExit(1)

a = Image.open(orig).convert("RGB")
b = Image.open(out).convert("RGB")

print("orig mode,size:", a.mode, a.size)
print("out  mode,size:", b.mode, b.size)

# MD5 quick check
def md5(p):
    h = hashlib.md5()
    h.update(p.read_bytes())
    return h.hexdigest()
print("md5(orig):", md5(orig))
print("md5(out) :", md5(out))

diff = ImageChops.difference(a, b)
bbox = diff.getbbox()
if bbox is None:
    print("Images are IDENTICAL (no pixel differences).")
else:
    nonzero = sum(1 for px in diff.getdata() if px != (0,0,0))
    print("Images differ. diff bbox:", bbox, "nonzero pixels:", nonzero)
    diff.save("debug_diff.png")
    print("Saved debug_diff.png for inspection.")
