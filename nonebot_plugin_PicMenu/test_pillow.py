from PIL import Image, ImageDraw, ImageFont

# Test creating a simple image
img = Image.new('RGBA', (200, 200), (255, 255, 255, 0))
draw = ImageDraw.Draw(img)

# Test font methods
font = ImageFont.truetype('SIMYOU.TTF', 20)
text = "Hello World"

# Test getbbox and getlength
bbox = font.getbbox(text)
width = font.getlength(text)

print(f"Text bounding box: {bbox}")
print(f"Text width: {width}")

# Test resize with Resampling.LANCZOS
img_resized = img.resize((100, 100), Image.Resampling.LANCZOS)
print(f"Resized image size: {img_resized.size}")

print("All tests passed!")
