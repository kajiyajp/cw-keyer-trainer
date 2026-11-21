# 作成：2026-11-21
# 目的：XIAO RP2040 とタクトスイッチ・ブザー・OLED の配線図（docs/wiring.png）を生成する
from PIL import Image, ImageDraw, ImageFont

W, H = 1500, 1100
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)

FONT = "C:/Windows/Fonts/meiryo.ttc"
f_title = ImageFont.truetype(FONT, 34)
f_big = ImageFont.truetype(FONT, 22)
f_mid = ImageFont.truetype(FONT, 19)
f_small = ImageFont.truetype(FONT, 16)

GND_C = (40, 40, 40)
COL = {"D0": (220, 50, 50), "D1": (30, 110, 220), "D2": (230, 140, 0), "D3": (40, 160, 80),
       "D4": (140, 60, 200), "D5": (0, 160, 170), "D6": (200, 60, 150), "3V3": (210, 30, 30)}


# ピンの y 座標（上から i 番目）
def pin_y(i):
    return 250 + i * 90


# 線を引く（太さ付き）
def wire(points, color, width=5):
    d.line(points, fill=color, width=width, joint="curve")


# 接続点の黒丸
def dot(x, y, color=GND_C, r=7):
    d.ellipse([x - r, y - r, x + r, y + r], fill=color)


# タクトスイッチ記号（x1〜x2 の間、高さ y）
def switch(x1, x2, y, color, label):
    wire([(x1, y), (x1 + 25, y)], color)
    wire([(x2 - 25, y), (x2, y)], color)
    for x in (x1 + 25, x2 - 25):
        d.ellipse([x - 7, y - 7, x + 7, y + 7], outline="black", width=3, fill="white")
    d.line([(x1 + 30, y - 6), (x2 - 30, y - 26)], fill="black", width=4)   # レバー
    d.line([((x1 + x2) / 2, y - 18), ((x1 + x2) / 2, y - 40)], fill="black", width=3)  # 押しボタン
    d.line([((x1 + x2) / 2 - 14, y - 40), ((x1 + x2) / 2 + 14, y - 40)], fill="black", width=3)
    d.text(((x1 + x2) / 2, y + 14), label, font=f_mid, fill="black", anchor="mt")


# 圧電ブザー記号
def buzzer(x1, x2, y, color, label):
    cx = (x1 + x2) / 2
    wire([(x1, y), (cx - 30, y)], GND_C)
    wire([(cx + 30, y), (x2, y)], color)
    d.ellipse([cx - 30, y - 30, cx + 30, y + 30], outline="black", width=4, fill=(255, 245, 220))
    d.text((cx, y), "BZ", font=f_mid, fill="black", anchor="mm")
    d.text((cx + 38, y - 30), "+", font=f_big, fill=color, anchor="mm")
    d.text((cx - 38, y - 30), "−", font=f_big, fill=GND_C, anchor="mm")
    d.text((cx + 36, y + 30), label, font=f_mid, fill="black", anchor="lt")


d.text((W / 2, 30), "CW Keyer Trainer 配線図（XIAO RP2040・上から見た図）", font=f_title, fill="black", anchor="mt")

# ---- XIAO 本体 ----
BX1, BX2, BY1, BY2 = 600, 830, 190, 850
d.rounded_rectangle([BX1, BY1, BX2, BY2], radius=24, fill=(30, 90, 60), outline="black", width=4)
d.rounded_rectangle([BX1 + 70, BY1 - 30, BX2 - 70, BY1 + 30], radius=10, fill=(190, 190, 190), outline="black", width=3)
d.text(((BX1 + BX2) / 2, BY1), "USB-C", font=f_small, fill="black", anchor="mm")
d.text(((BX1 + BX2) / 2, (BY1 + BY2) / 2), "XIAO\nRP2040", font=f_big, fill="white", anchor="mm", align="center")

left = ["D0", "D1", "D2", "D3", "D4/SDA", "D5/SCL", "D6"]
right = ["5V", "GND", "3V3", "D10", "D9", "D8", "D7"]
for i, name in enumerate(left):
    y = pin_y(i)
    d.rectangle([BX1 - 12, y - 12, BX1 + 12, y + 12], fill=(230, 190, 60), outline="black", width=2)
    d.text((BX1 + 22, y), name, font=f_mid, fill="white", anchor="lm")
for i, name in enumerate(right):
    y = pin_y(i)
    d.rectangle([BX2 - 12, y - 12, BX2 + 12, y + 12], fill=(230, 190, 60), outline="black", width=2)
    d.text((BX2 - 22, y), name, font=f_mid, fill="white", anchor="rm")

# ---- GND バス（左端の縦線 → 下 → 右側 GND ピン）----
GX = 110
BUS_Y = 920
wire([(GX, pin_y(0)), (GX, BUS_Y), (1000, BUS_Y), (1000, pin_y(1)), (BX2, pin_y(1))], GND_C, 6)
d.text((GX - 10, pin_y(0) - 40), "GND", font=f_big, fill=GND_C, anchor="mm")

# ---- 左側の部品 ----
X_PART1, X_PART2 = 250, 430
parts = {0: ("sw", "短点レバー（DIT）"), 1: ("sw", "長点レバー（DAH）"), 2: ("bz", "圧電ブザー（パッシブ）"),
         3: ("sw", "MENU ボタン"), 6: ("sw", "OK ボタン")}
for i, (kind, label) in parts.items():
    y = pin_y(i)
    color = COL[left[i][:2]]
    wire([(BX1 - 12, y), (X_PART2, y)], color)
    if kind == "sw":
        switch(X_PART1, X_PART2, y, color, label)
        wire([(GX, y), (X_PART1, y)], GND_C)
    else:
        buzzer(X_PART1, X_PART2, y, color, label)
        wire([(GX, y), (X_PART1, y)], GND_C)
    dot(GX, y)

# D4 / D5 は OLED へ（ネットラベル）
for i, net in ((4, "SDA"), (5, "SCL")):
    y = pin_y(i)
    color = COL[left[i][:2]]
    wire([(BX1 - 12, y), (460, y)], color)
    d.polygon([(460, y - 16), (330, y - 16), (310, y), (330, y + 16), (460, y + 16)], fill=color)
    d.text((385, y), f"OLED {net}", font=f_mid, fill="white", anchor="mm")

# ---- OLED（右側）----
OX1, OY1, OX2, OY2 = 1110, 230, 1420, 520
d.rounded_rectangle([OX1, OY1, OX2, OY2], radius=12, fill=(20, 40, 120), outline="black", width=4)
d.rectangle([OX1 + 25, OY1 + 90, OX2 - 25, OY2 - 25], fill="black")
d.text(((OX1 + OX2) / 2, (OY1 + OY2) / 2 + 30), "0.96\" OLED\nSSD1306 (I2C)", font=f_mid, fill=(120, 200, 255), anchor="mm", align="center")
opins = ["GND", "VCC", "SCL", "SDA"]
for k, name in enumerate(opins):
    x = OX1 + 50 + k * 70
    d.rectangle([x - 11, OY1 + 18, x + 11, OY1 + 40], fill=(230, 190, 60), outline="black", width=2)
    d.text((x, OY1 + 60), name, font=f_small, fill="white", anchor="mm")
# 3V3 → VCC、GND → GND
vx = OX1 + 50 + 70
wire([(BX2 + 12, pin_y(2)), (1060, pin_y(2)), (1060, 170), (vx, 170), (vx, OY1 + 18)], COL["3V3"])
gx = OX1 + 50
wire([(1000, pin_y(1)), (1000, 140), (gx, 140), (gx, OY1 + 18)], GND_C)
dot(1000, pin_y(1))
# SCL / SDA ネットラベル
for k, net, col in ((2, "SCL ← D5", COL["D5"]), (3, "SDA ← D4", COL["D4"])):
    x = OX1 + 50 + k * 70
    wire([(x, OY1 + 18), (x, OY1 - 10 - (k - 2) * 0)], col)
d.text((OX1 + 225, OY1 - 30), "SCL←D5  SDA←D4", font=f_mid, fill="black", anchor="mm")
d.text(((OX1 + OX2) / 2, OY2 + 25), "※ピン順は製品ごとに違います。基板の印字に合わせてください", font=f_small, fill="black", anchor="mt")

# ---- 凡例・注意 ----
notes = [
    "● スイッチは「ピン ↔ GND」をつなぐだけ。プルアップは XIAO 内部で有効にするので抵抗は不要です",
    "● 4本足のタクトスイッチは、対角の2本を使うと確実です（同じ辺の2本は内部でつながっていることがあります）",
    "● ブザーはパッシブ型を D2 と GND に。音が大きすぎるときは 100Ω 前後を直列に入れます",
    "● OLED は後回しでも OK（つながっていなくてもキーヤーは動きます）。電源は必ず 3V3 から",
    "● 5V・D7〜D10 は使いません",
]
for k, n in enumerate(notes):
    d.text((60, 960 + k * 25), n, font=f_small, fill="black")

img.save("docs/wiring.png")
print("saved docs/wiring.png")
