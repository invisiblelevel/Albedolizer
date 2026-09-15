from PIL import Image, ImageFilter

img = Image.open("env.png").convert("RGB")
# Сильное размытие — детали HDRI исчезают
blurred = img.filter(ImageFilter.GaussianBlur(radius=40))
blurred.save("env_blur.png")
print("OK: env_blur.png создан")