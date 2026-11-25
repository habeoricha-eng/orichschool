"""Génère les icônes PWA (à lancer une seule fois) : python make_icons.py"""
from PIL import Image, ImageDraw

for size in (192, 512):
    img = Image.new("RGB", (size, size), "#0F1226")
    d = ImageDraw.Draw(img)
    # Dégradé diagonal doux
    for i in range(size):
        c = (int(90 + 60 * i / size), int(92 + 40 * i / size), 255)
        d.line([(i, 0), (0, i)], fill=c, width=2)
    m = size // 5
    d.rounded_rectangle([m, m, size - m, size - m], radius=size // 6, fill="#0F1226")
    d.ellipse([size * .38, size * .38, size * .62, size * .62], fill="#8B8CFF")
    img.save(f"static/icon-{size}.png")
print("Icônes créées dans static/")