# 作成：2026-11-21
# 目的：XIAO RP2040 とパドル・ブザー・OLED・つまみ（LED 付きロータリーエンコーダー）の配線図（docs/wiring.png）を生成する
#       ブザーはトランジスタの回路（D2 と 5V から）なので、この図では行き先だけ書き、中身は回路図（docs/schematic.svg）に任せる
from PIL import Image, ImageDraw, ImageFont

W, H = 1500, 1160
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)

FONT = "C:/Windows/Fonts/meiryo.ttc"
f_title = ImageFont.truetype(FONT, 34)
f_big = ImageFont.truetype(FONT, 22)
f_mid = ImageFont.truetype(FONT, 19)
f_small = ImageFont.truetype(FONT, 16)

GND_C = (40, 40, 40)
COL = {"D0": (220, 50, 50), "D1": (30, 110, 220), "D2": (230, 140, 0), "D3": (40, 160, 80),
       "D4": (140, 60, 200), "D5": (0, 160, 170), "D6": (200, 60, 150), "D7": (110, 140, 20),
       "D8": (150, 90, 40), "D9": (230, 40, 40), "D10": (40, 80, 230), "3V3": (210, 30, 30)}


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


# 抵抗記号（x1〜x2 の間、高さ y）
def resistor(x1, x2, y, color, label):
    cx = (x1 + x2) / 2
    wire([(x1, y), (cx - 30, y)], color)
    wire([(cx + 30, y), (x2, y)], color)
    d.rectangle([cx - 30, y - 11, cx + 30, y + 11], outline="black", width=3, fill="white")
    d.text((cx, y - 16), label, font=f_small, fill="black", anchor="mb")


# 圧電サウンダ記号
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
parts = {0: ("sw", "短点レバー（DIT）"), 1: ("sw", "長点レバー（DAH）")}
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

# D2 はブザーの回路へ（ネットラベル）
y2 = pin_y(2)
wire([(BX1 - 12, y2), (460, y2)], COL["D2"])
d.polygon([(460, y2 - 16), (200, y2 - 16), (180, y2), (200, y2 + 16), (460, y2 + 16)], fill=COL["D2"])
d.text((320, y2), "ブザー回路 R1（1kΩ）へ", font=f_mid, fill="white", anchor="mm")

# 5V もブザーの回路へ（ネットラベル）
y5 = pin_y(0)
wire([(BX2 + 12, y5), (860, y5)], COL["D2"])
d.polygon([(860, y5 - 16), (975, y5 - 16), (990, y5), (975, y5 + 16), (860, y5 + 16)], fill=COL["D2"])
d.text((922, y5), "ブザー R4へ", font=f_small, fill="white", anchor="mm")

# D4 / D5 は OLED へ（ネットラベル）
for i, net in ((4, "SDA"), (5, "SCL")):
    y = pin_y(i)
    color = COL[left[i][:2]]
    wire([(BX1 - 12, y), (460, y)], color)
    d.polygon([(460, y - 16), (330, y - 16), (310, y), (330, y + 16), (460, y + 16)], fill=color)
    d.text((385, y), f"OLED {net}", font=f_mid, fill="white", anchor="mm")

# D3 は空き
d.text((BX1 - 30, pin_y(3)), "（空き）", font=f_mid, fill=(120, 120, 120), anchor="rm")

# D6 はつまみの押しボタンへ（ネットラベル）
y6 = pin_y(6)
wire([(BX1 - 12, y6), (460, y6)], COL["D6"])
d.polygon([(460, y6 - 16), (250, y6 - 16), (230, y6), (250, y6 + 16), (460, y6 + 16)], fill=COL["D6"])
d.text((345, y6), "つまみ SW（端子4）", font=f_mid, fill="white", anchor="mm")

# ---- OLED（右側）----
OX1, OY1, OX2, OY2 = 1110, 210, 1420, 440
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

# ---- つまみ：LED 付きロータリーエンコーダー（右下）----
EX1, EY1, EX2, EY2 = 1180, 490, 1440, 860
d.rounded_rectangle([EX1, EY1, EX2, EY2], radius=12, fill=(60, 60, 60), outline="black", width=4)
d.ellipse([EX1 + 150, EY1 + 100, EX1 + 240, EY1 + 190], fill=(150, 150, 150), outline="black", width=3)
d.text((EX1 + 195, EY1 + 215), "つまみ", font=f_small, fill="white", anchor="mt")
d.text((EX1 + 195, EY1 + 238), "EC12 (LED付)", font=f_small, fill="white", anchor="mt")
# 左辺の端子：上から 3(赤) 2(青) B A
term_rows = {"D10": ("2 青LED+", "100Ω〜"), "D9": ("3 赤LED+", "1kΩ〜"), "D8": ("B", None), "D7": ("A", None)}
for i, name in ((3, "D10"), (4, "D9"), (5, "D8"), (6, "D7")):
    y = pin_y(i)
    color = COL[name]
    label, res = term_rows[name]
    if res:
        wire([(BX2 + 12, y), (1060, y)], color)
        resistor(1060, EX1, y, color, res)
    else:
        wire([(BX2 + 12, y), (EX1, y)], color)
    d.rectangle([EX1 - 8, y - 8, EX1 + 8, y + 8], fill=(230, 190, 60), outline="black", width=2)
    d.text((EX1 + 16, y), label, font=f_small, fill="white", anchor="lm")
# 下辺の端子：C と 1 は GND、4 は D6 へ
for x, label in ((EX1 + 40, "C"), (EX1 + 110, "1"), (EX1 + 200, "4")):
    d.rectangle([x - 8, EY2 - 8, x + 8, EY2 + 8], fill=(230, 190, 60), outline="black", width=2)
    d.text((x, EY2 - 16), label, font=f_small, fill="white", anchor="mb")
for x in (EX1 + 40, EX1 + 110):
    wire([(x, EY2 + 8), (x, BUS_Y)], GND_C)
    dot(x, BUS_Y)
wire([(1000, BUS_Y), (EX1 + 110, BUS_Y)], GND_C, 6)
x4 = EX1 + 200
wire([(x4, EY2 + 8), (x4, EY2 + 30)], COL["D6"])
d.rounded_rectangle([x4 - 30, EY2 + 30, x4 + 30, EY2 + 60], radius=6, fill=COL["D6"])
d.text((x4, EY2 + 45), "→D6", font=f_small, fill="white", anchor="mm")

# ---- 凡例・注意 ----
notes = [
    "● スイッチは「ピン ↔ GND」をつなぐだけ。プルアップは XIAO 内部で有効にするので抵抗は不要です",
    "● つまみ：A→D7、B→D8、C と 1→GND、4（押しボタン）→D6。LED は 3（赤）→抵抗→D9、2（青）→抵抗→D10（HIGH で点灯）",
    "● 青 LED は 3.3V だと暗めです。100Ω から明るさを見て決めます（赤は 1kΩ から）。回す向きが逆なら A と B を入れ替えます",
    "● ブザー（電磁式 16Ω）はトランジスタで 5V から鳴らします（XIAO のピンでは電流が足りない）。中身は回路図 docs/schematic.svg",
    "● OLED は後回しでも OK（つながっていなくてもキーヤーは動きます）。電源は必ず 3V3 から",
    "● D3 は使いません。エンコーダーを付けないときは D6 にタクトスイッチをつなぐと「決定」だけ使えます",
]
for k, n in enumerate(notes):
    d.text((60, 990 + k * 25), n, font=f_small, fill="black")

img.save("docs/wiring.png")
print("saved docs/wiring.png")
