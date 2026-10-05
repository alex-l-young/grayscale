"""Generate icon.png and icon.icns: a rounded square of stepped gray values."""
from PIL import Image, ImageDraw

SIZE = 1024


def build():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (40, 40, SIZE - 40, SIZE - 40), radius=200, fill=255)
    bands = Image.new("RGBA", (SIZE, SIZE))
    d = ImageDraw.Draw(bands)
    n = 5
    for i in range(n):
        g = round(i * 255 / (n - 1))
        d.rectangle((0, i * SIZE // n, SIZE, (i + 1) * SIZE // n), fill=(g, g, g, 255))
    img.paste(bands, (0, 0), mask)
    return img


if __name__ == "__main__":
    icon = build()
    icon.save("icon.png")
    icon.save("icon.icns")
