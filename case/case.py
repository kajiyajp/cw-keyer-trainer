# 作成：2026-11-22
# 目的：CW Keyer Trainer の 3D プリント用ケース（底ケース＋ふた）を CadQuery で作り、STEP / STL と確認用の画像を書き出す。
#       基板・XIAO・OLED・つまみ・ブザー・ジャック・ねじまで組み付けた状態の STEP（assembly.step）も書き出す
#
# 実行（リポジトリのルートで）：
#   uv run --no-project --python 3.12 --with cadquery --with matplotlib python case/case.py
#
# 寸法はすべて mm。部品が手元と違うときは「部品の寸法」の数値を直して実行し直す。
# 座標：X＝右、Y＝奥、Z＝上。原点は基板の中心の真下（ケース底面の高さ）。
#
# 方針：大きめのケースにして、基板・部品とケースのすき間を 10 mm 以上あける（配線や手を入れる余裕）。
#       固定ねじはすべて M3 皿ねじ（頭が表面と面一になるよう皿もみする）。
# 組み立て：ユニバーサル基板（秋月 104303、ブレッドボード配線パターン）を底ケースの台に載せ、
#   1 列目の取付穴は位置決めピンに差し（XIAO の下になるため）、30 列目は底から M3 皿ねじを通してナットで締める。
#   ふたは四隅の柱に M3 皿ねじ 4 本で留める。OLED はふたの裏に、つまみの軸はふたの穴から出す。
#   ブザー（耳付きのパネル取付型）は手前の壁の内側に M3 皿ねじ 2 本で留め、壁の音穴から鳴らす。
# 部品の位置は tools/board_layout.py の実体配線図（docs/board_front.png）と同じ。

from pathlib import Path

import cadquery as cq

OUT = Path(__file__).parent / "out"

# ---------------- 部品の寸法（手元の部品に合わせて直す） ----------------
# ユニバーサル基板（秋月 104303：80×50mm、t1.6、30 列。取付穴は中央の溝の両端＝1 列目と 30 列目に 2 つ）
BOARD_X, BOARD_Y, BOARD_T = 80.0, 50.0, 1.6
PITCH = 2.54
BOARD_HOLE_D = 3.2


def col_x(c):
    """基板の c 列目の X 座標（基板の中心から）"""
    return (c - 15.5) * PITCH


def row_y(u):
    """行の Y 座標。u は中央の溝の中心からのピッチ数（奥が＋）"""
    return u * PITCH


ROW = {"J": 5.5, "I": 4.5, "H": 3.5, "G": 2.5, "F": 1.5, "E": -1.5, "D": -2.5, "C": -3.5, "B": -4.5, "A": -5.5,
       "T-": 8.75, "T+": 7.75, "B-": -7.75, "B+": -8.75}
HEADER_H = 2.5                  # ピンヘッダーの樹脂部の高さ（XIAO・DIP 化基板を浮かせる分）

# Seeed XIAO RP2040：D 行と H 行の 2〜8 列。USB-C を左の壁に向ける
XIAO_X, XIAO_Y, XIAO_T = 21.0, 17.5, 1.0
XIAO_PARTS_H = 2.0              # XIAO の上の部品（USB-C を含む）の高さ
XIAO_CX, XIAO_CY = col_x(5), (row_y(ROW["D"]) + row_y(ROW["H"])) / 2
USB_W, USB_H = 15.0, 9.0        # 左の壁の USB-C 穴（ケーブルの根元が壁の中まで入る大きさ）

# つまみ：EC12 エンコーダー（秋月 P-05772）＋ DIP 化基板 RECNV-2（P-07240）：C 行と I 行の 23〜27 列
ENC_CX, ENC_CY = col_x(25), (row_y(ROW["C"]) + row_y(ROW["I"])) / 2   # 軸の位置
ADAPTER_X, ADAPTER_Y, ADAPTER_T = 16.0, 23.5, 1.6
ENC_BODY_X, ENC_BODY_Y, ENC_BODY_H = 12.4, 13.2, 7.0
ENC_SHAFT_D, ENC_SHAFT_LEN = 6.0, 18.0     # 取付面から軸の先まで 25mm（本体 7＋軸 18）
ENC_KNURL_LEN = 7.0             # 軸先のギザギザ部（つまみがはまる長さ）
SHAFT_HOLE_D = 7.5              # ふたの軸穴
KNOB_D, KNOB_H = 15.0, 15.0     # 付属のつまみ（寸法は仮。組み立て図用）

# OLED 0.96 インチ（ASIN B0HGLXK9TW：SSD1315、I2C 4 ピン、27×27mm）。ふたの裏に付け、ガラスを窓から見せる
# ピンヘッダーは付けず、線を OLED と基板の J14〜J17 に直接はんだ付けする
OLED_CX, OLED_CY = 0.0, 15.0    # ふたの奥の中央（XIAO の真上を避け、J14〜J17 の真上）
OLED_PCB_X, OLED_PCB_Y, OLED_PCB_T = 27.0, 27.0, 1.0
OLED_GLASS_X, OLED_GLASS_Y, OLED_GLASS_T = 26.7, 19.3, 1.5
OLED_GLASS_DY = 0.0             # ガラスの中心の、基板中心からのずれ（上下の取付穴の列の間）
OLED_VIEW_X, OLED_VIEW_Y = 23.0, 12.0      # ふたの窓（表示部より少し大きめ）
OLED_VIEW_DY = -1.0             # 窓の中心の、ガラス中心からのずれ
OLED_HOLE_DX, OLED_HOLE_DY = 23.0, 23.0    # 取付穴の間隔（寸法は仮）
OLED_HOLE_D = 2.0
OLED_RECESS = 1.0               # ふたの裏のガラス用のくぼみの深さ

# ブザー（ASIN B0CZJ5DGDH：電子ブザー、DC 3〜24V、耳付きのパネル取付型、リード線付き。tone() で鳴らせ TONE も効く）
# 寸法は写真からの推定（SFM-20B 相当）。手元の物を測って直す
BUZ_D, BUZ_H = 23.0, 13.0       # 本体の直径・高さ（音の出る面から耳の面まで）
BUZ_EAR_PITCH = 30.0            # 耳の穴の間隔
BUZ_EAR_HOLE_D, BUZ_EAR_W, BUZ_EAR_T = 3.2, 7.0, 2.5
BUZ_CX = 0.0                    # 手前の壁での左右の位置

# 3.5mm ステレオジャック（TRS、3 端子、パネル取付・M6 ねじを想定）。奥の壁に付ける
JACK_CX = 10.0
JACK_HOLE_D = 6.3
JACK_BODY_D, JACK_BODY_LEN = 8.0, 12.0     # 壁の内側に出る本体

# ---------------- ケースの寸法 ----------------
WALL = 2.5
FLOOR = 3.0                     # 底から皿ねじを通すので厚め
LID_T = 3.0                     # 皿ねじの頭が沈む厚さ
MIN_CLEAR = 10.0                # 基板・部品とケースのすき間の目標
MARGIN = 12.0                   # 基板と左・右・奥の壁のすき間（四隅の柱を入れても 10 mm 以上残る）
MARGIN_FRONT = BUZ_H + MIN_CLEAR + 1.0     # 手前はブザーを付けるぶん広く（ブザーと基板も 10 mm 以上）
CORNER_R = 3.0
STANDOFF_H = 10.0               # 床から基板の下面まで（はんだ面の下のすき間）
STANDOFF_D = 7.0
PIN_D, PIN_LEN = 2.8, 2.0       # 1 列目の位置決めピン（基板の上に出る長さ）
POST_R = 6.0                    # ふたを留める四隅の柱（内側の角を中心にした丸）
SCREW_IN = 2.0                  # ふたのねじの位置：内側の角から中心側へ
# M3 皿ねじ（JIS の皿小ねじ：頭 φ6、90°）
M3_CLEAR_D = 3.4
CSK_D = 6.4
M3_TAP_D = 2.5                  # 柱の下穴（M3 の小ねじを直接ねじ込む。インサートナットを使うなら 4.0 前後に）
M3_NUT_AF, M3_NUT_H = 5.5, 2.4
LIP_H, LIP_W, LIP_GAP = 1.5, 1.2, 0.2      # ふたの裏の位置合わせ用のふち
KNOB_GAP = 1.0                  # ふたの上面とつまみの下面のすき間

# ---------------- 計算で決まる寸法 ----------------
IN_X = BOARD_X + 2 * MARGIN
IN_Y = BOARD_Y + MARGIN + MARGIN_FRONT
CASE_CY = (MARGIN - MARGIN_FRONT) / 2        # ケースの中心（基板の中心より手前にずれる）
OUT_X, OUT_Y = IN_X + 2 * WALL, IN_Y + 2 * WALL
FRONT_IN = CASE_CY - IN_Y / 2                # 手前の壁の内面の Y
BACK_IN = CASE_CY + IN_Y / 2                 # 奥の壁の内面の Y
BOARD_Z = FLOOR + STANDOFF_H                 # 基板の下面
BOARD_TOP = BOARD_Z + BOARD_T
ADAPTER_Z = BOARD_TOP + HEADER_H             # DIP 化基板の下面
ENC_MOUNT_Z = ADAPTER_Z + ADAPTER_T          # エンコーダーの取付面
SHAFT_TOP = ENC_MOUNT_Z + ENC_BODY_H + ENC_SHAFT_LEN
LID_TOP = SHAFT_TOP - ENC_KNURL_LEN - KNOB_GAP   # つまみの下に KNOB_GAP のすき間ができる高さ
BASE_H = LID_TOP - LID_T                     # 底ケースの壁の高さ（ふたの下面）

BOARD_HOLES = [(col_x(1), 0.0), (col_x(30), 0.0)]   # 1 列目＝位置決めピン、30 列目＝皿ねじ＋ナット
POST_CENTERS = [(sx * IN_X / 2, CASE_CY + sy * IN_Y / 2) for sx in (-1, 1) for sy in (-1, 1)]
LID_SCREWS = [(sx * (IN_X / 2 - SCREW_IN), CASE_CY + sy * (IN_Y / 2 - SCREW_IN)) for sx in (-1, 1) for sy in (-1, 1)]
XIAO_Z = BOARD_TOP + HEADER_H
USB_CZ = XIAO_Z + XIAO_T + 1.6
JACK_CZ = BOARD_TOP + 6.0
OLED_PCB_TOP = BASE_H + OLED_RECESS - OLED_GLASS_T
BUZ_CZ = (FLOOR + BASE_H) / 2                # ブザーの中心の高さ（壁の中ほど）
BUZ_EARS = [(BUZ_CX + s * BUZ_EAR_PITCH / 2, BUZ_CZ) for s in (-1, 1)]
LID_SCREW_LEN, BOARD_SCREW_LEN, BUZ_SCREW_LEN = 10, 16, 20


# ---------------- 形を作る道具 ----------------
def box_at(x, y, z, sx, sy, sz):
    """底面の中央が (x, y, z) の直方体"""
    return cq.Workplane("XY").box(sx, sy, sz, centered=(True, True, False)).translate((x, y, z))


def rounded_box(x, y, h, r, z=0.0, cy=0.0):
    """角を丸めた直方体（底面の中央が (0, cy, z)）"""
    return cq.Workplane("XY").box(x, y, h, centered=(True, True, False)).edges("|Z").fillet(r).translate((0, cy, z))


def cylinder(d, h, x, y, z):
    """Z 方向の円柱（底面の中心が (x, y, z)）"""
    return cq.Workplane("XY").circle(d / 2).extrude(h).translate((x, y, z))


def cylinder_y(d, length, x, y0, z):
    """Y 方向（奥向き）の円柱。手前の端の中心が (x, y0, z)"""
    return cq.Workplane(obj=cq.Solid.makeCylinder(d / 2, length, cq.Vector(x, y0, z), cq.Vector(0, 1, 0)))


def cone(d1, d2, h, base, direction):
    return cq.Workplane(obj=cq.Solid.makeCone(d1 / 2, d2 / 2, h, cq.Vector(*base), cq.Vector(*direction)))


def csk_cut(x, y, z_face, direction, depth):
    """M3 皿ねじの穴（皿もみ＋通し穴）。direction はねじを差し込む向き（面の外から中へ）"""
    dx, dy, dz = direction
    h = (CSK_D - M3_CLEAR_D) / 2
    outside = (x - dx, y - dy, z_face - dz)
    tip = (x + dx * h, y + dy * h, z_face + dz * h)
    c = cone(M3_CLEAR_D, CSK_D, h, tip, (-dx, -dy, -dz))
    shaft = cq.Workplane(obj=cq.Solid.makeCylinder(M3_CLEAR_D / 2, depth + 2, cq.Vector(*outside), cq.Vector(dx, dy, dz)))
    relief = cq.Workplane(obj=cq.Solid.makeCylinder(CSK_D / 2, 1, cq.Vector(*outside), cq.Vector(dx, dy, dz)))
    return c.union(shaft).union(relief)


def csk_screw(x, y, z_face, direction, length):
    """M3 皿ねじ（組み立て図用）。頭の上面が z_face の面と面一"""
    dx, dy, dz = direction
    h = 1.7
    head = cq.Workplane(obj=cq.Solid.makeCone(3.0, 1.5, h, cq.Vector(x, y, z_face), cq.Vector(dx, dy, dz)))
    body = cq.Workplane(obj=cq.Solid.makeCylinder(1.45, length - h, cq.Vector(x + dx * h, y + dy * h, z_face + dz * h),
                                                   cq.Vector(dx, dy, dz)))
    return head.union(body)


def hex_nut(x, y, z, direction=(0, 0, 1), af=M3_NUT_AF, h=M3_NUT_H, hole=3.0):
    """六角ナット（組み立て図用）。(x, y, z) は座面の中心、direction は厚みの向き（+Z か +Y）"""
    n = cq.Workplane("XY").polygon(6, af / 0.866).extrude(h).faces(">Z").workplane().hole(hole)
    if direction == (0, 1, 0):
        n = n.rotate((0, 0, 0), (1, 0, 0), -90)   # +Z を +Y へ
    return n.translate((x, y, z))


# ---------------- ケース ----------------
def make_walls():
    """壁と四隅の柱（すき間の確認にも使う）"""
    outer = rounded_box(OUT_X, OUT_Y, BASE_H, CORNER_R, cy=CASE_CY)
    walls = outer.cut(rounded_box(IN_X, IN_Y, BASE_H, 0.5, cy=CASE_CY))
    for x, y in POST_CENTERS:
        walls = walls.union(cylinder(2 * POST_R, BASE_H - FLOOR, x, y, FLOOR).intersect(outer))
    return walls


def buzzer_bosses():
    """手前の壁から、ブザーの耳まで伸びる台（ブザーの音の面を壁に当て、耳を台にねじ留め）"""
    length = BUZ_H - BUZ_EAR_T
    b = None
    for x, z in BUZ_EARS:
        s = cylinder_y(BUZ_EAR_W, length, x, FRONT_IN, z)
        b = s if b is None else b.union(s)
    return b


def make_base():
    """底ケース：床・壁・四隅の柱・基板の台・ブザーの台・USB-C 穴・ジャック穴・音穴"""
    shell = rounded_box(OUT_X, OUT_Y, FLOOR, CORNER_R, cy=CASE_CY).union(make_walls())
    (px, py), (sx, sy) = BOARD_HOLES
    for x, y in BOARD_HOLES:
        shell = shell.union(cylinder(STANDOFF_D, STANDOFF_H, x, y, FLOOR))
    shell = shell.union(cylinder(PIN_D, BOARD_T + PIN_LEN, px, py, BOARD_Z))          # 1 列目：位置決めピン
    shell = shell.cut(csk_cut(sx, sy, 0.0, (0, 0, 1), FLOOR + STANDOFF_H))            # 30 列目：底から皿ねじ
    for x, y in LID_SCREWS:                                                            # ふたのねじの下穴
        shell = shell.cut(cylinder(M3_TAP_D, 12, x, y, BASE_H - 12))
    # ブザー：台と、手前の壁から皿ねじ、音穴
    shell = shell.union(buzzer_bosses())
    for x, z in BUZ_EARS:
        shell = shell.cut(csk_cut(x, FRONT_IN - WALL, z, (0, 1, 0), WALL + BUZ_H))
    pts = [(BUZ_CX + i * 3.2, BUZ_CZ + j * 3.2) for i in range(-2, 3) for j in range(-2, 3) if i * i + j * j <= 4]
    for x, z in pts:
        shell = shell.cut(cylinder_y(2.0, WALL + 2, x, FRONT_IN - WALL - 1, z))
    # 左の壁：USB-C（角の丸い長穴）／奥の壁：ジャック
    usb = (cq.Workplane("YZ").workplane(offset=-OUT_X / 2 - 1)
           .center(XIAO_CY, USB_CZ).slot2D(USB_W, USB_H).extrude(WALL + 2))
    shell = shell.cut(usb)
    shell = shell.cut(cylinder_y(JACK_HOLE_D, WALL + 2, JACK_CX, BACK_IN - 1, JACK_CZ))
    return shell


def make_lid():
    """ふた：軸穴・OLED の窓とくぼみ・位置合わせのふち・四隅の皿ねじ穴"""
    lid = rounded_box(OUT_X, OUT_Y, LID_T, CORNER_R, BASE_H, cy=CASE_CY)
    ox, oy = IN_X - 2 * LIP_GAP, IN_Y - 2 * LIP_GAP
    lip = rounded_box(ox, oy, LIP_H, 0.5, BASE_H - LIP_H, cy=CASE_CY)
    lip = lip.cut(rounded_box(ox - 2 * LIP_W, oy - 2 * LIP_W, LIP_H, 0.5, BASE_H - LIP_H, cy=CASE_CY))
    for x, y in POST_CENTERS:
        lip = lip.cut(cylinder(2 * POST_R + 1, LIP_H + 1, x, y, BASE_H - LIP_H - 0.5))
    lid = lid.union(lip)
    for x, y in LID_SCREWS:
        lid = lid.cut(csk_cut(x, y, LID_TOP, (0, 0, -1), LID_T))
    lid = lid.cut(cylinder(SHAFT_HOLE_D, LID_T + 2, ENC_CX, ENC_CY, BASE_H - 1))
    gy = OLED_CY + OLED_GLASS_DY
    lid = lid.cut(box_at(OLED_CX, gy, BASE_H, OLED_GLASS_X + 0.4, OLED_GLASS_Y + 0.4, OLED_RECESS))
    lid = lid.cut(cq.Workplane("XY").box(OLED_VIEW_X, OLED_VIEW_Y, LID_T + 2, centered=(True, True, False))
                  .edges("|Z").fillet(1.0).translate((OLED_CX, gy + OLED_VIEW_DY, BASE_H - 1)))
    spacer_h = BASE_H - OLED_PCB_TOP
    for x, y in oled_holes():
        if spacer_h > 0.05:
            lid = lid.union(cylinder(3.5, spacer_h, x, y, OLED_PCB_TOP))
        lid = lid.union(cylinder(OLED_HOLE_D - 0.2, OLED_PCB_T + 1.5, x, y, OLED_PCB_TOP - OLED_PCB_T - 1.5))
    return lid


def oled_holes():
    return [(OLED_CX + sx * OLED_HOLE_DX / 2, OLED_CY + sy * OLED_HOLE_DY / 2) for sx in (-1, 1) for sy in (-1, 1)]


# ---------------- 部品（組み立て図・干渉確認用） ----------------
def make_board():
    """ユニバーサル基板（穴 φ1.0 を 2.54mm ピッチで。取付穴 2 つ）"""
    b = box_at(0, 0, BOARD_Z, BOARD_X, BOARD_Y, BOARD_T)
    pts = [(col_x(c), row_y(u)) for c in range(1, 31) for u in ROW.values()]
    b = b.cut(cq.Workplane("XY").pushPoints(pts).circle(0.5).extrude(BOARD_T + 2).translate((0, 0, BOARD_Z - 1)))
    for x, y in BOARD_HOLES:
        b = b.cut(cylinder(BOARD_HOLE_D, BOARD_T + 2, x, y, BOARD_Z - 1))
    return b


def make_xiao():
    """XIAO RP2040：基板・USB-C・チップ・シールド（おおよその形）"""
    pcb = box_at(XIAO_CX, XIAO_CY, XIAO_Z, XIAO_X, XIAO_Y, XIAO_T)
    usb = box_at(XIAO_CX - XIAO_X / 2 + 3.3, XIAO_CY, XIAO_Z + XIAO_T, 7.5, 8.9, 3.2)
    chip = box_at(XIAO_CX + 2.0, XIAO_CY, XIAO_Z + XIAO_T, 7.0, 7.0, 1.0)
    flash = box_at(XIAO_CX + 7.5, XIAO_CY, XIAO_Z + XIAO_T, 4.0, 5.0, 1.0)
    return pcb, usb.union(chip).union(flash)


def make_headers():
    """ピンヘッダー（樹脂部＋ピン）：XIAO の D 行・H 行、DIP 化基板の C 行・I 行"""
    plastic, pins = None, None
    for cx, cols, rows in ((XIAO_CX, range(2, 9), ("D", "H")), (ENC_CX, range(23, 28), ("C", "I"))):
        for r in rows:
            p = box_at((col_x(cols[0]) + col_x(cols[-1])) / 2, row_y(ROW[r]), BOARD_TOP, len(cols) * PITCH, PITCH, HEADER_H)
            plastic = p if plastic is None else plastic.union(p)
            for c in cols:
                q = box_at(col_x(c), row_y(ROW[r]), BOARD_Z - 3.0, 0.64, 0.64, 3.0 + BOARD_T + HEADER_H + 2.6)
                pins = q if pins is None else pins.union(q)
    return plastic, pins


def make_encoder():
    adapter = box_at(ENC_CX, ENC_CY, ADAPTER_Z, ADAPTER_X, ADAPTER_Y, ADAPTER_T)
    body = box_at(ENC_CX, ENC_CY, ENC_MOUNT_Z, ENC_BODY_X, ENC_BODY_Y, ENC_BODY_H)
    shaft = cylinder(ENC_SHAFT_D, ENC_SHAFT_LEN, ENC_CX, ENC_CY, ENC_MOUNT_Z + ENC_BODY_H)
    knob_z = SHAFT_TOP - ENC_KNURL_LEN
    knob = (cylinder(KNOB_D, KNOB_H, ENC_CX, ENC_CY, knob_z).edges(">Z").fillet(1.5)
            .cut(cylinder(ENC_SHAFT_D, ENC_KNURL_LEN, ENC_CX, ENC_CY, knob_z - 0.01)))
    return adapter, body, shaft, knob


def make_oled():
    pcb = box_at(OLED_CX, OLED_CY, OLED_PCB_TOP - OLED_PCB_T, OLED_PCB_X, OLED_PCB_Y, OLED_PCB_T)
    for x, y in oled_holes():
        pcb = pcb.cut(cylinder(OLED_HOLE_D, OLED_PCB_T + 2, x, y, OLED_PCB_TOP - OLED_PCB_T - 1))
    glass = box_at(OLED_CX, OLED_CY + OLED_GLASS_DY, OLED_PCB_TOP, OLED_GLASS_X, OLED_GLASS_Y, OLED_GLASS_T)
    return pcb, glass


def make_buzzer():
    """耳付きのブザー：音の面を手前の壁に当て、耳を台に留める"""
    body = cylinder_y(BUZ_D, BUZ_H, BUZ_CX, FRONT_IN, BUZ_CZ)
    ear_y = FRONT_IN + BUZ_H - BUZ_EAR_T      # 耳は本体の奥側（音の面の反対）の端
    ears = (cq.Workplane("XY").box(BUZ_EAR_PITCH, BUZ_EAR_T, BUZ_EAR_W, centered=(True, False, True))
            .translate((BUZ_CX, ear_y, BUZ_CZ)))
    for x, z in BUZ_EARS:
        ears = ears.union(cylinder_y(BUZ_EAR_W, BUZ_EAR_T, x, ear_y, z))
    for x, z in BUZ_EARS:
        ears = ears.cut(cylinder_y(BUZ_EAR_HOLE_D, BUZ_EAR_T + 2, x, ear_y - 1, z))
    return body.union(ears)


def make_jack():
    """パネル取付の 3.5mm ジャック：本体・ねじ部・ナット・端子 3 本"""
    body = cylinder_y(JACK_BODY_D, JACK_BODY_LEN, JACK_CX, BACK_IN - JACK_BODY_LEN, JACK_CZ)
    bush = cylinder_y(6.0, WALL + 3.0, JACK_CX, BACK_IN, JACK_CZ)
    bush = bush.cut(cylinder_y(3.6, WALL + 4.0, JACK_CX, BACK_IN - 0.5, JACK_CZ))
    nut = hex_nut(JACK_CX, BACK_IN + WALL, JACK_CZ, (0, 1, 0), af=8.0, h=2.0, hole=6.0)
    lugs = None
    for dx in (-2.5, 0.0, 2.5):
        lug = box_at(JACK_CX + dx, BACK_IN - JACK_BODY_LEN - 2.5, JACK_CZ - 5.5, 1.5, 5.0, 0.4)
        lugs = lug if lugs is None else lugs.union(lug)
    return body.union(bush).union(lugs), nut


def make_parts():
    """干渉・すき間の確認用の部品"""
    p = {}
    p["基板"] = box_at(0, 0, BOARD_Z, BOARD_X, BOARD_Y, BOARD_T)
    for x, y in BOARD_HOLES:
        p["基板"] = p["基板"].cut(cylinder(BOARD_HOLE_D, BOARD_T + 2, x, y, BOARD_Z - 1))
    p["XIAO"] = box_at(XIAO_CX, XIAO_CY, XIAO_Z, XIAO_X, XIAO_Y, XIAO_T + XIAO_PARTS_H)
    plastic, _ = make_headers()
    p["ヘッダー"] = plastic
    adapter, body, shaft, _ = make_encoder()
    p["DIP 化基板"], p["エンコーダー"], p["軸"] = adapter, body, shaft
    p["OLED 基板"], p["OLED ガラス"] = make_oled()
    p["ブザー"] = make_buzzer()
    p["ジャック"] = cylinder_y(JACK_BODY_D, JACK_BODY_LEN, JACK_CX, BACK_IN - JACK_BODY_LEN, JACK_CZ)
    p["ナット"] = cylinder(M3_NUT_AF / 0.866, M3_NUT_H, BOARD_HOLES[1][0], BOARD_HOLES[1][1], BOARD_TOP)
    return p


def volume(a, b):
    try:
        return a.intersect(b).val().Volume()
    except Exception:
        return 0.0


def gap(a, b):
    return a.val().distance(b.val())


def check(base, lid, parts):
    """部品どうし・部品とケースの重なりを調べる（部品を載せている所の接触は除く）"""
    problems = []
    names = list(parts)
    allowed = {("基板", "ヘッダー"), ("XIAO", "ヘッダー"), ("DIP 化基板", "ヘッダー"), ("DIP 化基板", "エンコーダー"),
               ("エンコーダー", "軸"), ("OLED 基板", "OLED ガラス"), ("基板", "ナット")}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if (a, b) in allowed or (b, a) in allowed:
                continue
            v = volume(parts[a], parts[b])
            if v > 0.5:
                problems.append(f"{a} と {b}：{v:.1f} mm³")
    for case_name, case in (("底ケース", base), ("ふた", lid)):
        for n in names:
            if (case_name, n) in {("ふた", "軸"), ("ふた", "OLED 基板")}:
                continue
            v = volume(case, parts[n])
            if v > 0.5:
                problems.append(f"{case_name} と {n}：{v:.1f} mm³")
    return problems


def clearances(lid, parts):
    """基板と基板の部品から、壁・柱・ふた・ブザーまでのすき間"""
    walls = make_walls()
    rows = []
    for n in ("基板", "XIAO", "DIP 化基板", "エンコーダー"):
        rows.append((n, "壁・柱", gap(parts[n], walls)))
    for n in ("基板", "XIAO", "DIP 化基板", "エンコーダー"):
        rows.append((n, "ブザー", gap(parts[n], parts["ブザー"])))
    rows.append(("XIAO", "ふた・OLED", min(gap(parts["XIAO"], lid), gap(parts["XIAO"], parts["OLED 基板"]))))
    rows.append(("基板", "床（はんだ面の下）", BOARD_Z - FLOOR))
    return rows


# ---------------- 組み立て STEP ----------------
def make_assembly(base, lid):
    """ケースに全部品とねじを組み付けた状態（色付き）。部品名はほかの CAD で文字化けしないよう英数字にする"""
    C = cq.Color
    a = cq.Assembly(name="cw_keyer_trainer")
    a.add(base, name="case_base", color=C(0.82, 0.82, 0.80, 1))
    a.add(lid, name="case_lid", color=C(0.90, 0.75, 0.50, 1))
    a.add(make_board(), name="board_akizuki_104303", color=C(0.85, 0.80, 0.55, 1))
    pcb, comps = make_xiao()
    a.add(pcb, name="xiao_rp2040_pcb", color=C(0.10, 0.35, 0.20, 1))
    a.add(comps, name="xiao_rp2040_parts", color=C(0.75, 0.75, 0.78, 1))
    plastic, pins = make_headers()
    a.add(plastic, name="pin_header_plastic", color=C(0.1, 0.1, 0.1, 1))
    a.add(pins, name="pin_header_pins", color=C(0.85, 0.70, 0.30, 1))
    adapter, body, shaft, knob = make_encoder()
    a.add(adapter, name="encoder_adapter_recnv2", color=C(0.20, 0.35, 0.70, 1))
    a.add(body, name="encoder_ec12", color=C(0.25, 0.25, 0.25, 1))
    a.add(shaft, name="encoder_shaft", color=C(0.80, 0.80, 0.82, 1))
    a.add(knob, name="knob", color=C(0.15, 0.15, 0.15, 1))
    opcb, glass = make_oled()
    a.add(opcb, name="oled_pcb", color=C(0.10, 0.20, 0.55, 1))
    a.add(glass, name="oled_glass", color=C(0.05, 0.05, 0.05, 1))
    a.add(make_buzzer(), name="buzzer", color=C(0.12, 0.12, 0.12, 1))
    jack, jnut = make_jack()
    a.add(jack, name="jack_3p5mm_trs", color=C(0.30, 0.30, 0.30, 1))
    a.add(jnut, name="jack_nut", color=C(0.80, 0.80, 0.82, 1))
    steel = C(0.70, 0.70, 0.72, 1)
    for i, (x, y) in enumerate(LID_SCREWS):
        a.add(csk_screw(x, y, LID_TOP, (0, 0, -1), LID_SCREW_LEN), name=f"lid_screw_m3x{LID_SCREW_LEN}_{i + 1}", color=steel)
    sx, sy = BOARD_HOLES[1]
    a.add(csk_screw(sx, sy, 0.0, (0, 0, 1), BOARD_SCREW_LEN), name=f"board_screw_m3x{BOARD_SCREW_LEN}", color=steel)
    a.add(hex_nut(sx, sy, BOARD_TOP), name="board_nut_m3", color=steel)
    for i, (x, z) in enumerate(BUZ_EARS):
        a.add(csk_screw(x, FRONT_IN - WALL, z, (0, 1, 0), BUZ_SCREW_LEN), name=f"buzzer_screw_m3x{BUZ_SCREW_LEN}_{i + 1}", color=steel)
        a.add(hex_nut(x, FRONT_IN + BUZ_H, z, (0, 1, 0)), name=f"buzzer_nut_m3_{i + 1}", color=steel)
    return a


def render(shapes, path, elev, azim, title):
    """形を matplotlib で描いて PNG にする（確認用）"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    plt.rcParams["font.family"] = ["Meiryo", "Yu Gothic", "sans-serif"]
    fig = plt.figure(figsize=(9, 7), dpi=110)
    ax = fig.add_subplot(111, projection="3d")
    lo, hi = [1e9] * 3, [-1e9] * 3
    all_polys, all_cols = [], []
    for shape, color, alpha in shapes:
        verts, tris = shape.val().tessellate(0.2, 0.3)
        pts = [(v.x, v.y, v.z) for v in verts]
        for p in pts:
            lo = [min(a, b) for a, b in zip(lo, p)]
            hi = [max(a, b) for a, b in zip(hi, p)]
        polys = [[pts[i] for i in t] for t in tris]
        light = (-0.4, -0.5, 0.75)
        for a, b, c in polys:
            u = [b[k] - a[k] for k in range(3)]
            v = [c[k] - a[k] for k in range(3)]
            n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
            ln = sum(x * x for x in n) ** 0.5 or 1.0
            s = 0.45 + 0.55 * abs(sum(n[k] * light[k] for k in range(3)) / ln)
            all_cols.append((color[0] * s, color[1] * s, color[2] * s, alpha))
        all_polys += polys
    ax.add_collection3d(Poly3DCollection(all_polys, facecolors=all_cols, edgecolor="none"))
    c = [(a + b) / 2 for a, b in zip(lo, hi)]
    r = max(b - a for a, b in zip(lo, hi)) / 2
    ax.set_xlim(c[0] - r, c[0] + r)
    ax.set_ylim(c[1] - r, c[1] + r)
    ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    base, lid = make_base(), make_lid()
    parts = make_parts()

    print(f"外形：{OUT_X:.1f} × {OUT_Y:.1f} × {LID_TOP:.1f} mm（底ケースの高さ {BASE_H:.1f}、ふた {LID_T}）")
    print(f"軸の先：{SHAFT_TOP:.1f} mm、ふたの上に出る軸：{SHAFT_TOP - LID_TOP:.1f} mm")
    print(f"ねじ：ふた＝M3×{LID_SCREW_LEN} 皿 4本、基板＝M3×{BOARD_SCREW_LEN} 皿＋ナット、ブザー＝M3×{BUZ_SCREW_LEN} 皿＋ナット 2組")
    problems = check(base, lid, parts)
    print("干渉：なし" if not problems else "干渉：\n  " + "\n  ".join(problems))
    print(f"すき間（目標 {MIN_CLEAR:.0f} mm 以上）：")
    for a, b, g in clearances(lid, parts):
        print(f"  {a} → {b}：{g:.1f} mm {'OK' if g >= MIN_CLEAR - 0.05 else '（不足）'}")
    print(f"  エンコーダー → ふた：{BASE_H - (ENC_MOUNT_Z + ENC_BODY_H):.1f} mm（軸がふたを通るため、軸の長さで決まる。例外）")

    cq.exporters.export(base, str(OUT / "case_base.step"))
    cq.exporters.export(lid, str(OUT / "case_lid.step"))
    cq.exporters.export(base, str(OUT / "case_base.stl"), tolerance=0.05, angularTolerance=0.2)
    lid_print = lid.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, LID_TOP))
    cq.exporters.export(lid_print, str(OUT / "case_lid.stl"), tolerance=0.05, angularTolerance=0.2)
    assy = make_assembly(base, lid)
    assy.export(str(OUT / "assembly.step"))

    ghost = [(s, (0.2, 0.5, 0.9), 0.9) for s in parts.values()]
    render([(base, (0.85, 0.85, 0.82), 1.0)], OUT / "preview_base.png", 30, -130, "底ケース（左に USB-C、奥にジャック、手前にブザー）")
    render([(base, (0.85, 0.85, 0.82), 1.0)], OUT / "preview_bottom.png", -40, -60, "底ケースの裏（基板を留める皿ねじ）")
    render([(base, (0.85, 0.85, 0.82), 1.0)], OUT / "preview_front.png", 15, -95, "手前の壁（ブザーの音穴と皿ねじ）")
    render([(lid, (0.85, 0.85, 0.82), 1.0)], OUT / "preview_lid.png", -35, -60, "ふた（裏から）")
    render([(base, (0.85, 0.85, 0.82), 1.0), (lid, (0.9, 0.75, 0.5), 1.0)],
           OUT / "preview_top.png", 40, -65, "組み立てた外観（OLED の窓・つまみの穴・皿ねじ）")
    render([(base, (0.85, 0.85, 0.82), 0.25)] + ghost + [(lid, (0.9, 0.7, 0.4), 0.25)],
           OUT / "preview_assembly.png", 28, -55, "組み立て（部品は青）")
    # 組み立て STEP の中身（ふたを外して上から）
    shown = []
    for child in assy.children:
        if child.name == "case_lid":
            continue
        rgba = child.color.toTuple() if child.color else (0.5, 0.5, 0.5, 1)
        alpha = 0.35 if child.name == "case_base" else 1.0
        shown.append((cq.Workplane(obj=child.obj.val()), rgba[:3], alpha))
    render(shown, OUT / "preview_parts.png", 45, -60, "assembly.step の中身（ふたを外した状態）")
    print(f"書き出し：{OUT}")


if __name__ == "__main__":
    main()
