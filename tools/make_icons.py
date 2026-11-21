# 作成：2026-11-21
# 目的：PWA のアイコン（app/icons/*.png）を生成する。濃い背景に「・－」
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "app" / "icons"
BG = (17, 18, 20)
FG = (76, 141, 255)


# 1 辺 size px のアイコンを描く
def make(size):
    img = Image.new("RGB", (size, size), BG)
    d = ImageDraw.Draw(img)
    u = size / 16  # 1 単位
    cy = size / 2
    # 短点（丸）と長点（角丸の棒）
    d.ellipse([3 * u, cy - 1.3 * u, 5.6 * u, cy + 1.3 * u], fill=FG)
    d.rounded_rectangle([7 * u, cy - 1.3 * u, 13 * u, cy + 1.3 * u], radius=1.3 * u, fill=FG)
    return img


OUT.mkdir(parents=True, exist_ok=True)
for name, size in (("icon-192.png", 192), ("icon-512.png", 512), ("apple-touch-icon.png", 180)):
    make(size).save(OUT / name)
    print("saved", OUT / name)
