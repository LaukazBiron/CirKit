from PIL import Image
from pathlib import Path

BASE = Path(__file__).resolve().parents[2] / "src"/ "ui" / "kivy" / "icons"
src_png = BASE / "app_icon.png"
dst_ico = BASE / "app_icon.ico"

sizes = [16, 24, 32, 48, 64, 128, 256]  # tamaños recomendados Windows
im = Image.open(src_png).convert("RGBA")
im.save(dst_ico, sizes=[(s, s) for s in sizes])
print(f"Generado: {dst_ico}")
