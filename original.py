from PIL import Image

img = Image.open(r"C:\Users\Yadhnika Wakde\Pictures\Screenshots\Sign.png")

img = img.resize((580, 180))
img = img.convert("RGB")  

img.save("Sign.jpg", "JPEG")