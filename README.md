# minipil
## A mini-Pillow, natural-language image editor for your terminal.

minipil is a lightweight command-line tool that performs image editing using simple natural-language instructions.
Resize, crop, compress, rotate, adjust brightness/contrast, convert to B&W, invert, blur, sharpen — all with one command.

> No ML Models required

Ideal for exam photo requirements (GATE, passport photos, govt forms), quick batch edits, or automation scripts.

### Installation
```
pip install minipil
```
#### 1. Connect an image
```
minipil connect image.png
```

#### 2. Apply edits (natural language)
```
minipil do "convert to bnw and resize to 400x500"
```

#### 3. Save result
```
minipil save output.jpg
```


#### If no filename is given:
```
minipil save
```
##### → saves as minipil.png in the current directory

### Current minipil supports:

1. Grayscale (BNW)
```
minipil do "convert to bnw"
minipil do "make it grayscale"
minipil do "black and white"
```
2. Invert
  ```
minipil do "invert"
minipil do "invert colors"
```

3. Blur
  ```
minipil do "blur 2"
minipil do "blur 4"
minipil do "gaussian blur 3.5"
```

4. Sharpen
```
minipil do "sharpen"
minipil do "sharpen 2"
minipil do "sharpen 3.5"
```


5. Brightness
```
minipil do "brightness +20%"
minipil do "increase brightness 15%"
minipil do "darken 10%"
minipil do "brightness -5%"
```

6. Contrast
```
minipil do "contrast +25%"
minipil do "increase contrast 10%"
minipil do "decrease contrast 30%"
```

7. Saturation
```
minipil do "saturation +40%"
minipil do "boost color 30%"
minipil do "desaturate 20%"
```

8. Rotation
```
minipil do "rotate 90"
minipil do "rotate 180"
minipil do "rotate -45"
```

9. Flip horizontal/vertical
```
minipil do "flip horizontal"
minipil do "flip h"
```
10. Exact pixel resize
```
minipil do "400x600"
minipil do "resize to 300x300"
minipil do "make it 1024x768"
```

11. Resize by width/height
```
minipil do "width 300"
minipil do "height 500"
minipil do "resize to width 600"
```

12. Aspect ratio crop
```
minipil do "ratio 1:1"
minipil do "crop to 3:2"
minipil do "ratio 4:5"
```

13. File size compression
```
minipil do "compress to 250kb"
minipil do "size 150kb"
minipil do "target 300kb"
minipil do "100kb"
```

14. Format conversion
```
minipil do "convert to jpeg"
minipil do "convert to png"
minipil save output.jpg
minipil save image.webp
```

15. Chained multi-action commands
```
minipil do "invert and blur 3 and rotate 90"
minipil do "convert to bnw, ratio 4:5, compress to 200kb"
minipil do "resize to 400x500 and brightness +20% and sharpen 2"
minipil do "saturation +40% and contrast -10% and flip horizontal"
```

### Folder Structure
```

minipil/

 ├── cli.py          # CLI commands (connect, do, save)
 ├── core.py         # All image-processing functions
 ├── parser.py       # NL command parser
 ├── session.py      # Persistent session manager
 └── __init__.py
tests/
docs/
setup.py
README.md
```


### Contributing

Contributions are very welcome!
open issues for:
- batch processing
- smarter NLP

---
#### Created by - Yadhnika Wakde
> With love and ```--force```
