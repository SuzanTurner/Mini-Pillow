from PIL import Image
from pathlib import Path
import sys

p = Path(r"D:\Yadh\OpenSource\minipillow\dwinky.jpg")
if not p.exists():
    print("File not found:", p)
    sys.exit(1)

img = Image.open(p).convert("RGB")
w,h = img.size
# sample pixels: top-left, center, bottom-right
samples = [(0,0), (w//2, h//2), (w-1,h-1)]
same = 0
total = 0
for y in range(0,h, max(1,h//20)):    # sample ~20 rows
    for x in range(0,w, max(1,w//20)): # sample ~20 cols
        r,g,b = img.getpixel((x,y))
        total += 1
        if r==g==b:
            same += 1

print("size:", img.size, "mode:", img.mode)
print("sample pixels equal R==G==B:", same, "/", total, f"({same/total:.2%})")
for s in samples:
    print("sample", s, "=", img.getpixel(s))
