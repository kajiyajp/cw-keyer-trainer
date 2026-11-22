# 作成：2026-11-22
# 目的：ユニバーサル基板（秋月 104303、ブレッドボード配線パターン 80×50mm 片面）の実体配線図を
#       表（部品面）と裏（はんだ面）の2枚の PNG にする（docs/board_front.png / docs/board_back.png）
#
# 基板のパターン：30 列。各列の A〜E と F〜J がそれぞれつながる。上下の端に電源レール 2 本ずつ
#   （上：外側＝−、内側＝＋／下：内側＝−、外側＝＋）。取付穴は中央の溝の両端（1 列目と 30 列目）に 2 つ。
# 実行：python tools/board_layout.py（Pillow が必要）

from PIL import Image, ImageDraw, ImageFont

FONT = "C:/Windows/Fonts/meiryo.ttc"
f_title = ImageFont.truetype(FONT, 30)
f_big = ImageFont.truetype(FONT, 19)
f_mid = ImageFont.truetype(FONT, 16)
f_small = ImageFont.truetype(FONT, 13)

# ---- 基板の寸法 ----
PITCH = 2.54
BOARD_W, BOARD_H = 80.0, 50.0
MARGIN_X = (BOARD_W - 29 * PITCH) / 2          # 1 列目の中心まで
P = 30                                         # 1 ピッチ＝30px
X0, Y0 = 70, 160                              # 基板の左上（px）
BW, BH = BOARD_W / PITCH * P, BOARD_H / PITCH * P

# 行の位置（中央の溝の中心を 0、奥（図の上）を＋、単位はピッチ）
ROW_U = {"J": 5.5, "I": 4.5, "H": 3.5, "G": 2.5, "F": 1.5,
         "E": -1.5, "D": -2.5, "C": -3.5, "B": -4.5, "A": -5.5,
         "T-": 8.75, "T+": 7.75, "B-": -7.75, "B+": -8.75}
MOUNT_COLS = (1, 30)

# ---- 線の色（信号ごと） ----
NET = {
    "GND": (40, 40, 40), "3V3": (220, 30, 30), "D0": (230, 110, 30), "D1": (30, 110, 220),
    "D2": (200, 150, 0), "SND": (200, 150, 0), "D4": (140, 60, 200), "D5": (0, 160, 170),
    "D6": (200, 60, 150), "D7": (110, 140, 20), "D8": (150, 90, 40),
    "D9": (240, 80, 80), "LED_R": (240, 80, 80), "D10": (60, 90, 240), "LED_B": (60, 90, 240),
    "NC": (150, 150, 150), "5V": (150, 150, 150), "D3": (150, 150, 150),
}

# ---- 部品のピン：(列, 行, 信号, 表示名) ----
XIAO_COLS = range(2, 9)
XIAO_FRONT = ["D0", "D1", "D2", "D3", "D4", "D5", "D6"]       # D 行（USB 側から）
XIAO_BACK = ["5V", "GND", "3V3", "D10", "D9", "D8", "D7"]      # H 行
ENC_COLS = range(23, 28)                                        # DIP 化基板（C 行と I 行）
ENC_FRONT = [("NC", "−"), ("D7", "A"), ("GND", "C"), ("D8", "B"), ("NC", "−")]
ENC_BACK = [("NC", "−"), ("D6", "4 SW"), ("LED_R", "3 赤"), ("LED_B", "2 青"), ("GND", "1 共通")]
OLED_HDR = [(14, "GND"), (15, "3V3"), (16, "D5"), (17, "D4")]   # J 行の 4 ピンヘッダー
OLED_NAMES = {"GND": "GND", "3V3": "VCC", "D5": "SCL", "D4": "SDA"}
SOUNDER = [(13, "B", "SND", "+"), (17, "B", "GND", "−")]

pins = []
for i, c in enumerate(XIAO_COLS):
    pins.append((c, "D", XIAO_FRONT[i], XIAO_FRONT[i]))
    pins.append((c, "H", XIAO_BACK[i], XIAO_BACK[i]))
for i, c in enumerate(ENC_COLS):
    pins.append((c, "C", ENC_FRONT[i][0], ENC_FRONT[i][1]))
    pins.append((c, "I", ENC_BACK[i][0], ENC_BACK[i][1]))
for c, net in OLED_HDR:
    pins.append((c, "J", net, OLED_NAMES[net]))
for c, r, net, name in SOUNDER:
    pins.append((c, r, net, name))

# 抵抗：(列1, 行1, 列2, 行2, 信号, 表示)
RESISTORS = [
    (4, "C", 10, "C", "D2", "R1 音量（0Ω〜10kΩ。ジャンパー線でも可）"),
    (5, "J", 11, "J", "D10", "R2 100Ω（青）"),
    (6, "I", 12, "I", "D9", "R3 1kΩ（赤）"),
]
# ジャンパー線：(列1, 行1, 列2, 行2, 信号)
WIRES = [
    (3, "J", 3, "T-", "GND"), (4, "J", 4, "T+", "3V3"),
    (14, "I", 14, "T-", "GND"), (15, "I", 15, "T+", "3V3"),
    (16, "I", 7, "B", "D5"), (17, "I", 6, "B", "D4"),
    (24, "J", 8, "B", "D6"), (8, "J", 24, "A", "D7"), (7, "J", 26, "A", "D8"),
    (12, "G", 25, "J", "LED_R"), (11, "H", 26, "J", "LED_B"),
    (27, "J", 27, "T-", "GND"), (25, "B", 25, "B-", "GND"),
    (10, "D", 13, "E", "SND"),                        # サウンダの下を避けて E 行から
    (17, "E", 19, "E", "GND"), (19, "A", 19, "B-", "GND"),
    (20, "T-", 20, "B-", "GND"),
]
# 基板の外へ出る線：(列, 行, 信号, 表示, 引き出す向き)
OFFBOARD = [
    (2, "A", "D0", "ジャック 先端（短点）", "down"),
    (3, "A", "D1", "ジャック リング（長点）", "down"),
    (10, "T-", "GND", "ジャック 根元（GND）", "up"),
]


def hx(c, back=False):
    """列 c の x 座標（px）。裏面は左右反転"""
    x = X0 + (MARGIN_X + (c - 1) * PITCH) / PITCH * P
    return 2 * X0 + BW - x if back else x


def hy(r):
    """行 r の y 座標（px）"""
    return Y0 + (BOARD_H / 2 - ROW_U[r] * PITCH) / PITCH * P


def board_base(d, back):
    """基板の板・穴・印字を描く"""
    d.rounded_rectangle([X0, Y0, X0 + BW, Y0 + BH], radius=8,
                        fill=(196, 170, 110) if back else (225, 215, 170), outline="black", width=3)
    if back:
        # 銅のパターン（各列の A〜E・F〜J、電源レール）
        cu = (225, 150, 80)
        for c in range(1, 31):
            for r1, r2 in (("A", "E"), ("F", "J")):
                d.rounded_rectangle([hx(c, True) - 9, hy(r2) - 11, hx(c, True) + 9, hy(r1) + 11], radius=8, fill=cu)
        for r in ("T-", "T+", "B-", "B+"):
            d.rounded_rectangle([hx(30, True) - 11, hy(r) - 9, hx(1, True) + 11, hy(r) + 9], radius=8, fill=cu)
    for c in range(1, 31):
        for r in ROW_U:
            x, y = hx(c, back), hy(r)
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(70, 60, 40))
    for c in MOUNT_COLS:
        x, y = hx(c, back), (hy("E") + hy("F")) / 2
        d.ellipse([x - 16, y - 16, x + 16, y + 16], fill="white", outline="black", width=2)
    # 行・列の印字
    for r in "ABCDEFGHIJ":
        d.text((hx(1, back) - 22 if not back else hx(1, back) + 22, hy(r)), r, font=f_small, fill="black", anchor="mm")
    for c in (1, 5, 10, 15, 20, 25, 30):
        if c != 15:  # 上の 15 は OLED ヘッダーの文字と重なるので省く
            d.text((hx(c, back), hy("J") - 22), str(c), font=f_small, fill="black", anchor="mm")
        d.text((hx(c, back), hy("A") + 22), str(c), font=f_small, fill="black", anchor="mm")
    for r, s in (("T-", "−"), ("T+", "＋"), ("B-", "−"), ("B+", "＋")):
        xl = hx(1, back) - 22 if not back else hx(1, back) + 22
        d.text((xl, hy(r)), s, font=f_mid, fill=(200, 0, 0) if s == "＋" else (0, 0, 160), anchor="mm")


def dot(d, x, y, color, r=7):
    d.ellipse([x - r, y - r, x + r, y + r], fill=color, outline="white", width=2)


def front():
    img = Image.new("RGBA", (1640, 930), "white")
    d = ImageDraw.Draw(img)
    d.text((820, 30), "実体配線図（表・部品面）  秋月 104303 ブレッドボード配線パターン基板 80×50mm", font=f_title, fill="black", anchor="mt")
    d.text((820, 75), "左に USB-C（ケースの左の壁）、上が奥（ジャック側）。線はジャンパー線（色は信号ごと）", font=f_mid, fill="black", anchor="mt")
    board_base(d, back=False)

    # 部品（半透明）
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    o = ImageDraw.Draw(over)
    # XIAO：本体 21×17.5mm、USB-C は左
    cx, cy = (hx(2) + hx(8)) / 2, (hy("D") + hy("H")) / 2
    w, h = 21 / PITCH * P, 17.5 / PITCH * P
    o.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=10, fill=(30, 90, 60, 170), outline=(0, 0, 0, 255), width=2)
    o.rectangle([cx - w / 2 - 12, cy - 4.5 / PITCH * P, cx - w / 2 + 25, cy + 4.5 / PITCH * P], fill=(180, 180, 180, 230), outline=(0, 0, 0, 255))
    # DIP 化基板＋エンコーダー＋軸
    ex, ey = hx(25), (hy("C") + hy("I")) / 2
    aw, ah = 16 / PITCH * P, 23.5 / PITCH * P
    o.rectangle([ex - aw / 2, ey - ah / 2, ex + aw / 2, ey + ah / 2], fill=(40, 70, 160, 120), outline=(0, 0, 0, 255), width=2)
    bw = 12.4 / PITCH * P
    o.rectangle([ex - bw / 2, ey - bw / 2, ex + bw / 2, ey + bw / 2], fill=(90, 90, 90, 170), outline=(0, 0, 0, 255), width=2)
    o.ellipse([ex - 3 / PITCH * P, ey - 3 / PITCH * P, ex + 3 / PITCH * P, ey + 3 / PITCH * P], fill=(200, 200, 200, 230), outline=(0, 0, 0, 255))
    # 圧電サウンダ φ17
    sx, sy = (hx(13) + hx(17)) / 2, hy("B")
    sr = 8.5 / PITCH * P
    o.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(250, 235, 200, 140), outline=(0, 0, 0, 255), width=2)
    # OLED 用ヘッダー
    o.rectangle([hx(14) - 14, hy("J") - 14, hx(17) + 14, hy("J") + 14], fill=(20, 20, 20, 200))
    img.alpha_composite(over)
    d = ImageDraw.Draw(img)
    d.text((cx, cy), "XIAO RP2040", font=f_big, fill="white", anchor="mm")
    d.text((cx - w / 2 + 6, cy), "USB-C", font=f_small, fill="black", anchor="lm")
    d.text((ex, ey - bw / 2 - 2), "つまみ", font=f_small, fill="white", anchor="md")
    d.text((sx, sy + sr - 10), "圧電サウンダ", font=f_small, fill="black", anchor="md")
    # 取付穴（部品の下に隠れるので輪郭を描き直す）
    my = (hy("E") + hy("F")) / 2
    for c in MOUNT_COLS:
        d.ellipse([hx(c) - 16, my - 16, hx(c) + 16, my + 16], outline=(200, 0, 0), width=3)
    d.text((hx(30), my + 20), "取付穴", font=f_small, fill=(200, 0, 0), anchor="mt")
    d.text((hx(30), my + 38), "（ねじ）", font=f_small, fill=(200, 0, 0), anchor="mt")
    d.text((hx(1) + 4, my + 22), "取付穴（ピン）", font=f_small, fill=(200, 0, 0), anchor="lt")

    # ピン（はんだ付けする穴）
    for c, r, net, name in pins:
        dot(d, hx(c), hy(r), NET[net], 6)
    # 抵抗
    for c1, r1, c2, r2, net, label in RESISTORS:
        x1, y1, x2, y2 = hx(c1), hy(r1), hx(c2), hy(r2)
        d.line([(x1, y1), (x2, y2)], fill=(120, 120, 120), width=3)
        mx = (x1 + x2) / 2
        d.rounded_rectangle([mx - 30, y1 - 9, mx + 30, y1 + 9], radius=6, fill=(230, 200, 150), outline="black", width=2)
        for x in (x1, x2):
            dot(d, x, y1, NET[net], 6)
    # ジャンパー線
    for c1, r1, c2, r2, net in WIRES:
        x1, y1, x2, y2 = hx(c1), hy(r1), hx(c2), hy(r2)
        d.line([(x1, y1), (x2, y2)], fill=NET[net], width=5)
        dot(d, x1, y1, NET[net])
        dot(d, x2, y2, NET[net])
    # 基板の外へ
    for k, (c, r, net, label, way) in enumerate(OFFBOARD):
        x, y = hx(c), hy(r)
        y2 = Y0 + BH + 35 + 26 * k if way == "down" else Y0 - 40   # 文字が重ならないよう段違いに
        d.line([(x, y), (x, y2)], fill=NET[net], width=5)
        dot(d, x, y, NET[net])
        d.text((x + 8, y2), label, font=f_small, fill="black", anchor="lm" if way == "up" else "lt")
    # 抵抗の名前（線の上に重ならないよう最後に）
    for c1, r1, c2, r2, net, label in RESISTORS:
        mx = (hx(c1) + hx(c2)) / 2
        d.text((mx, hy(r1)), label.split(" ")[0], font=f_small, fill="black", anchor="mm")
    d.text(((hx(14) + hx(17)) / 2, hy("J") - 26), "OLED へ", font=f_small, fill="black", anchor="mm")

    legend(d, X0 + BW + 30, Y0 - 10)
    img.convert("RGB").save("docs/board_front.png")
    print("saved docs/board_front.png")


def legend(d, x, y):
    lines = [
        ("部品（穴の位置）", None),
        ("XIAO：D 行 2〜8 列（D0〜D6）、H 行 2〜8 列（5V〜D7）", None),
        ("つまみ：C 行 23〜27（−,A,C,B,−）、I 行 23〜27（−,SW,赤,青,共通）", None),
        ("サウンダ：B13（＋）・B17（−）。足の間隔が違うときは列を変える", None),
        ("OLED ヘッダー：J14〜17（GND,VCC,SCL,SDA）", None),
        ("", None),
        ("ジャンパー線", None),
        ("GND：J3・I14・J27→上の−、B25・A19→下の−", "GND"),
        ("上下の−を 20 列でつなぐ。サウンダ−：E17→E19", "GND"),
        ("3V3：J4・I15→上の＋", "3V3"),
        ("D2：R1（C4〜C10）、D10→E13→サウンダ＋", "D2"),
        ("D4 SDA：B6→I17　D5 SCL：B7→I16", "D4"),
        ("D6 押しボタン：B8→J24", "D6"),
        ("D7 A：J8→A24　D8 B：J7→A26", "D7"),
        ("D9 赤：R3（I6〜I12）、G12→J25", "D9"),
        ("D10 青：R2（J5〜J11）、H11→J26", "D10"),
        ("", None),
        ("基板の外", None),
        ("ジャック：先端→A2、リング→A3、根元→上の−（T10）", "D0"),
        ("OLED：J14〜17 からケーブルでふたの裏の OLED へ", None),
        ("", None),
        ("● 取付穴（中央の溝の両端）：1 列目は XIAO の下", None),
        ("   になるので位置決めピン、30 列目をねじで留める", None),
        ("● DIP 化基板のピンと端子の対応は、はんだ付け", None),
        ("   前にテスターで確かめる", None),
    ]
    for k, (t, net) in enumerate(lines):
        if net:
            d.line([(x, y + k * 27 + 9), (x + 22, y + k * 27 + 9)], fill=NET[net], width=5)
        bold = t and not t.startswith(("XIAO", "つまみ", "サウンダ", "OLED", "GND", "3V3", "D", "ジャック", "●", "   ", "上下"))
        d.text((x + (30 if net else 0), y + k * 27), t, font=f_mid if bold else f_small, fill="black")


def back():
    img = Image.new("RGB", (1640, 930), "white")
    d = ImageDraw.Draw(img)
    d.text((820, 30), "実体配線図（裏・はんだ面）  左右が反転しています", font=f_title, fill="black", anchor="mt")
    d.text((820, 75), "オレンジ＝銅のパターン。色の点がはんだ付けする穴（色は信号ごと）。パターンを切る場所はありません", font=f_mid, fill="black", anchor="mt")
    board_base(d, back=True)
    used = {}
    for c, r, net, name in pins:
        used[(c, r)] = (net, name)
    for c1, r1, c2, r2, net, label in RESISTORS:
        used.setdefault((c1, r1), (net, ""))
        used.setdefault((c2, r2), ("SND" if net == "D2" else "LED_B" if net == "D10" else "LED_R", ""))
    for c1, r1, c2, r2, net in WIRES:
        used.setdefault((c1, r1), (net, ""))
        used.setdefault((c2, r2), (net, ""))
    for c, r, net, label, way in OFFBOARD:
        used.setdefault((c, r), (net, ""))
    for (c, r), (net, name) in used.items():
        if net == "NC":
            continue
        dot(d, hx(c, True), hy(r), NET[net], 7)
    # 主な部品の位置（裏から見た位置に枠だけ）
    def box(c1, c2, r1, r2, label, above=False):
        xa, xb = sorted((hx(c1, True), hx(c2, True)))
        d.rectangle([xa - 16, hy(r1) - 16, xb + 16, hy(r2) + 16], outline=(0, 0, 0), width=2)
        if above:
            d.text(((xa + xb) / 2, hy(r1) - 20), label, font=f_small, fill="black", anchor="mb")
        else:
            d.text(((xa + xb) / 2, hy(r2) + 20), label, font=f_small, fill="black", anchor="mt")
    box(2, 8, "H", "D", "XIAO")
    box(23, 27, "I", "C", "つまみ")
    box(14, 17, "J", "J", "OLED ヘッダー", above=True)
    # 信号名の凡例
    x, y = X0 + BW + 30, Y0
    d.text((x, y), "点の色", font=f_mid, fill="black")
    for k, (net, t) in enumerate([("GND", "GND"), ("3V3", "3V3"), ("D0", "D0 短点"), ("D1", "D1 長点"),
                                   ("D2", "D2・サウンダ"), ("D4", "D4 SDA"), ("D5", "D5 SCL"), ("D6", "D6 押しボタン"),
                                   ("D7", "D7 A 相"), ("D8", "D8 B 相"), ("D9", "D9・赤 LED"), ("D10", "D10・青 LED")]):
        dot(d, x + 10, y + 40 + k * 30, NET[net], 8)
        d.text((x + 28, y + 40 + k * 30), t, font=f_mid, fill="black", anchor="lm")
    d.text((x, y + 420), "● 各列の A〜E、F〜J は銅でつながって", font=f_small, fill="black")
    d.text((x, y + 442), "   いるので、同じ帯の穴どうしは同じ信号", font=f_small, fill="black")
    d.text((x, y + 470), "● 上下の端の帯は電源レール（−／＋）", font=f_small, fill="black")
    img.save("docs/board_back.png")
    print("saved docs/board_back.png")


if __name__ == "__main__":
    front()
    back()
