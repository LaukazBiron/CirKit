from PIL import Image, ImageDraw, ImageFont
import os, zipfile, pathlib

BASE = pathlib.Path(__file__).resolve().parents[2]  # .../src
OUT_DIR = BASE / "ui" / "assets" / "icons"
ZIP_PATH = pathlib.Path(__file__).with_name("cirkit_icons.zip")
OUT_DIR.mkdir(parents=True, exist_ok=True)

try:
    FONT = ImageFont.truetype("DejaVuSans.ttf", 18)
except Exception:
    FONT = ImageFont.load_default()

ACCENT = (30,144,255,255)
WHITE  = (255,255,255,255)

def text_center(draw, box_w, box_h, text, font, fill):
    # Pillow 10: usar textbbox
    bbox = draw.textbbox((0,0), text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    x = (box_w - tw)//2
    y = (box_h - th)//2
    draw.text((x,y), text, font=font, fill=fill)

def save_icon(name, draw_fn):
    im = Image.new("RGBA", (96,96), (0,0,0,0))
    d  = ImageDraw.Draw(im)
    draw_fn(d, im.size)
    p = OUT_DIR / f"{name}.png"
    im.save(p)
    return p

def text_icon(txt):
    def fn(d, size):
        w,h = size
        d.rounded_rectangle([10,10,w-10,h-10], radius=14, outline=WHITE, width=6)
        text_center(d, w, h, txt, FONT, WHITE)
    return fn

def app_icon(d, size):
    w,h = size
    d.rounded_rectangle([8,8,w-8,h-8], radius=18, outline=ACCENT, width=6)
    d.line([20,h//2, 40,h//2], fill=WHITE, width=6)
    d.line([42,h//2-14, 42,h//2+14], fill=WHITE, width=6)
    d.line([48,h//2-6, 48,h//2+6], fill=WHITE, width=6)
    x=56; y=h//2; pts=[x,y]
    for i in range(5):
        x+=8; pts+=[x, y-10 if i%2==0 else y+10]
        x+=8; pts+=[x, y]
    d.line(pts, fill=ACCENT, width=6)

def rotate(d,size):
    w,h=size; d.arc([14,14,w-14,h-14], 45, 315, fill=WHITE, width=6)
    d.polygon([(w-22,26),(w-12,34),(w-30,36)], fill=ACCENT)

def trash(d,size):
    w,h=size; d.rectangle([26,30,w-26,h-20], outline=WHITE, width=6)
    d.rectangle([30,18,w-30,30], fill=WHITE)

def resistor(d,size):
    w,h=size; y=h//2
    d.line([16,y,28,y], fill=WHITE, width=6)
    x=28; pts=[x,y]
    for i in range(5):
        x+=8; pts+=[x, y-10 if i%2==0 else y+10]
        x+=8; pts+=[x, y]
    d.line(pts, fill=ACCENT, width=6)
    d.line([x,y, w-16,y], fill=WHITE, width=6)

def vsource(d,size):
    w,h=size
    d.line([w//2,16,w//2,h-16], fill=WHITE, width=6)
    d.ellipse([w//2-18,h//2-18,w//2+18,h//2+18], outline=WHITE, width=6)
    d.line([w//2-8,h//2,w//2+8,h//2], fill=ACCENT, width=6)
    d.line([w//2,h//2-8,w//2,h//2+8], fill=ACCENT, width=6)

def diode(d,size):
    w,h=size; y=h//2
    d.line([16,y,30,y], fill=WHITE, width=6)
    d.polygon([(30,y-14),(30,y+14),(52,y)], outline=WHITE, fill=None)
    d.line([56,y-14,56,y+14], fill=WHITE, width=6)
    d.line([56,y,w-16,y], fill=WHITE, width=6)

def node(d,size):
    w,h=size; d.ellipse([w//2-10,h//2-10,w//2+10,h//2+10], fill=ACCENT, outline=WHITE, width=4)

def wire(d,size):
    w,h=size; d.line([16,h-24, 40,h-24, 40,24, 76,24], fill=ACCENT, width=6)

def gnd(d,size):
    w,h=size; y=h//2+8
    d.line([w//2-20,y,w//2+20,y], fill=WHITE, width=6)
    d.line([w//2-14,y+10,w//2+14,y+10], fill=WHITE, width=4)
    d.line([w//2-8,y+18,w//2+8,y+18], fill=WHITE, width=4)

icons = {
    "app_icon": app_icon, "rotate": rotate, "trash": trash,
    "open": text_icon("OPEN"), "save": text_icon("SAVE"),
    "pdf": text_icon("PDF"), "help": text_icon("?"),
    "select": text_icon("SEL"),
    "resistor": resistor, "vsource": vsource, "diode": diode,
    "node": node, "wire": wire, "gnd": gnd,
}

paths = [save_icon(n, fn) for n, fn in icons.items()]

with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
    for p in paths:
        arc = pathlib.Path("assets") / "icons" / p.name
        zf.write(p, arcname=str(arc))

print("OK ->", ZIP_PATH)
