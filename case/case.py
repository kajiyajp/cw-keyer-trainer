# 作成：2026-11-22
# 目的：CW Keyer Trainer の 3D プリント用ケース（底ケース＋ふた）を CadQuery で作り、STEP / STL と確認用の画像を書き出す
#
# 実行（リポジトリのルートで）：
#   uv run --no-project --python 3.12 --with cadquery --with matplotlib python case/case.py
#
# 寸法はすべて mm。部品が手元と違うときは「部品の寸法」の数値を直して実行し直す。
# 座標：X＝右、Y＝奥、Z＝上。原点はケース底面の中央。
#
# 組み立て：ユニバーサル基板（秋月 104303、ブレッドボード配線パターン）を底ケースの台に載せ、
# 1 列目の取付穴は位置決めピンに差し（XIAO の下になるため）、30 列目を M3 ねじで台に留める。
# ふたは四隅の柱に M3 ねじ 4 本で留める。OLED はふたの裏に、つまみの軸はふたの穴から出す。
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
    """基板の c 列目の X 座標（基板の中心＝ケースの中心から）"""
    return (c - 15.5) * PITCH


def row_y(u):
    """行の Y 座標。u は中央の溝の中心からのピッチ数（奥が＋。J=5.5、A=-5.5）"""
    return u * PITCH


ROW = {"J": 5.5, "I": 4.5, "H": 3.5, "G": 2.5, "F": 1.5, "E": -1.5, "D": -2.5, "C": -3.5, "B": -4.5, "A": -5.5}
HEADER_H = 2.5                  # ピンヘッダーの樹脂部の高さ（XIAO・DIP 化基板を浮かせる分）

# Seeed XIAO RP2040：D 行と H 行の 2〜8 列。USB-C を左の壁に向ける
XIAO_X, XIAO_Y, XIAO_T = 21.0, 17.5, 1.0
XIAO_CX, XIAO_CY = col_x(5), (row_y(ROW["D"]) + row_y(ROW["H"])) / 2
USB_W, USB_H = 12.0, 7.0        # 左の壁の USB-C 穴（ケーブルの根元が入る大きさ）

# つまみ：EC12 エンコーダー（秋月 P-05772）＋ DIP 化基板 RECNV-2（P-07240）：C 行と I 行の 23〜27 列
ENC_CX, ENC_CY = col_x(25), (row_y(ROW["C"]) + row_y(ROW["I"])) / 2   # 軸の位置
ADAPTER_X, ADAPTER_Y, ADAPTER_T = 16.0, 23.5, 1.6
ENC_BODY_X, ENC_BODY_Y, ENC_BODY_H = 12.4, 13.2, 7.0
ENC_SHAFT_D, ENC_SHAFT_LEN = 6.0, 18.0     # 取付面から軸の先まで 25mm（本体 7＋軸 18）
ENC_KNURL_LEN = 7.0             # 軸先のギザギザ部（つまみがはまる長さ）
SHAFT_HOLE_D = 7.5              # ふたの軸穴

# OLED 0.96 インチ（SSD1306、I2C 4 ピン）。ふたの裏に付け、ガラスを窓から見せる
# 線は基板の J14〜J17 に直接はんだ付けする（コネクターだと高さが足りない）
OLED_CX, OLED_CY = -14.0, 4.0
OLED_PCB_X, OLED_PCB_Y, OLED_PCB_T = 27.3, 27.8, 1.0
OLED_GLASS_X, OLED_GLASS_Y, OLED_GLASS_T = 26.7, 19.3, 1.5
OLED_GLASS_DY = 0.0             # ガラスの中心の、基板中心からのずれ（ガラスは上下の取付穴の列の間にある）
OLED_VIEW_X, OLED_VIEW_Y = 23.0, 12.0      # ふたの窓（表示部より少し大きめ）
OLED_VIEW_DY = -1.0             # 窓の中心の、ガラス中心からのずれ
OLED_HOLE_DX, OLED_HOLE_DY = 23.5, 23.8    # 取付穴の間隔
OLED_HOLE_D = 2.0
OLED_RECESS = 1.0               # ふたの裏のガラス用のくぼみの深さ

# 圧電サウンダ（パッシブ型、φ17×7mm を想定）：B13・B17。基板に載せ、ふたに音穴
SOUNDER_CX, SOUNDER_CY = col_x(15), row_y(ROW["B"])
SOUNDER_D, SOUNDER_H = 17.0, 7.0

# 3.5mm ステレオジャック（パネル取付、M6 ねじ）。奥の壁に付ける
JACK_CX, JACK_CZ = 10.0, 16.0
JACK_HOLE_D = 6.3
JACK_BODY_D, JACK_BODY_LEN = 8.0, 12.0     # 壁の内側に出る本体（干渉確認用）

# ---------------- ケースの寸法 ----------------
WALL = 2.0
FLOOR = 2.0
LID_T = 2.0
CLEAR = 0.5                     # 基板と壁のすき間
CORNER_R = 3.0
STANDOFF_H = 5.0                # 床から基板の下面まで（はんだ面の逃げ）
STANDOFF_D = 6.0
PILOT_D = 2.6                   # M3 タッピング用の下穴
PIN_D, PIN_LEN = 2.8, 2.0       # 1 列目の位置決めピン（基板の上に出る長さ）
SCREW_HOLE_D = 3.4              # ふたの M3 通し穴
POST_D = 7.0                    # ふたを留める四隅の柱（基板の外側に置く）
LIP_H, LIP_W, LIP_GAP = 1.5, 1.2, 0.2      # ふたの裏の位置合わせ用のふち
KNOB_GAP = 1.0                  # ふたの上面とつまみの下面のすき間

# ---------------- 計算で決まる寸法 ----------------
# 基板の取付穴は2つだけなので、ふたを留める柱は基板の前後（Y 方向の外側）に置く
IN_X = BOARD_X + 2 * CLEAR
IN_Y = BOARD_Y + 2 * (CLEAR + POST_D)
OUT_X, OUT_Y = IN_X + 2 * WALL, IN_Y + 2 * WALL
BOARD_Z = FLOOR + STANDOFF_H                 # 基板の下面
BOARD_TOP = BOARD_Z + BOARD_T
ADAPTER_Z = BOARD_TOP + HEADER_H             # DIP 化基板の下面
ENC_MOUNT_Z = ADAPTER_Z + ADAPTER_T          # エンコーダーの取付面
SHAFT_TOP = ENC_MOUNT_Z + ENC_BODY_H + ENC_SHAFT_LEN
# ふたの上面：つまみ（ギザギザ部にはめる）の下に KNOB_GAP のすき間ができる高さ
LID_TOP = SHAFT_TOP - ENC_KNURL_LEN - KNOB_GAP
BASE_H = LID_TOP - LID_T                     # 底ケースの壁の高さ（ふたの下面）
BOARD_HOLES = [(col_x(1), 0.0), (col_x(30), 0.0)]   # 1 列目＝位置決めピン、30 列目＝ねじ
PX, PY = IN_X / 2 - POST_D / 2, IN_Y / 2 - POST_D / 2
POSTS = [(sx * PX, sy * PY) for sx in (-1, 1) for sy in (-1, 1)]
XIAO_Z = BOARD_TOP + HEADER_H
USB_CZ = XIAO_Z + XIAO_T + 1.6              # USB-C の中心の高さ
OLED_PCB_TOP = BASE_H + OLED_RECESS - OLED_GLASS_T   # ガラスはくぼみに入り、基板はその下


def rounded_box(x, y, h, r, z=0.0):
    """角を丸めた直方体（底面の中央が (0, 0, z)）"""
    return cq.Workplane("XY").box(x, y, h, centered=(True, True, False)).edges("|Z").fillet(r).translate((0, 0, z))


def cylinder(d, h, x, y, z):
    """Z 方向の円柱（底面の中心が (x, y, z)）"""
    return cq.Workplane("XY").circle(d / 2).extrude(h).translate((x, y, z))


def cylinder_y(d, length, x, y0, z):
    """Y 方向（奥向き）の円柱。手前の端の中心が (x, y0, z)"""
    return cq.Workplane(obj=cq.Solid.makeCylinder(d / 2, length, cq.Vector(x, y0, z), cq.Vector(0, 1, 0)))


def make_base():
    """底ケース：床・壁・基板の台（ピン／ねじ）・ふたを留める柱・USB-C 穴・ジャック穴"""
    shell = rounded_box(OUT_X, OUT_Y, BASE_H, CORNER_R)
    shell = shell.cut(rounded_box(IN_X, IN_Y, BASE_H, CORNER_R - WALL / 2, FLOOR))
    (px, py), (sx, sy) = BOARD_HOLES
    for x, y in BOARD_HOLES:
        shell = shell.union(cylinder(STANDOFF_D, STANDOFF_H, x, y, FLOOR))
    # 1 列目：位置決めピン（XIAO の下になり、ねじを回せないため）
    shell = shell.union(cylinder(PIN_D, BOARD_T + PIN_LEN, px, py, BOARD_Z))
    # 30 列目：M3 タッピングの下穴（床は貫通させない）
    shell = shell.cut(cylinder(PILOT_D, STANDOFF_H + FLOOR - 0.6, sx, sy, 0.6))
    # ふたを留める四隅の柱（上から M3 タッピングの下穴）
    for x, y in POSTS:
        shell = shell.union(cylinder(POST_D, BASE_H - FLOOR, x, y, FLOOR))
        shell = shell.cut(cylinder(PILOT_D, 10, x, y, BASE_H - 10))
    # 左の壁：USB-C（角の丸い長穴）
    usb = (cq.Workplane("YZ").workplane(offset=-OUT_X / 2 - 1)
           .center(XIAO_CY, USB_CZ).slot2D(USB_W, USB_H).extrude(WALL + 2))
    shell = shell.cut(usb)
    # 奥の壁：ジャック
    shell = shell.cut(cylinder_y(JACK_HOLE_D, WALL + 2, JACK_CX, OUT_Y / 2 - WALL - 1, JACK_CZ))
    return shell


def make_lid():
    """ふた：軸穴・OLED の窓とくぼみ・音穴・位置合わせのふち・四隅のねじ穴"""
    lid = rounded_box(OUT_X, OUT_Y, LID_T, CORNER_R, BASE_H)
    # 位置合わせのふち（壁の内側に入る枠。四隅の柱の所は欠く）
    ox, oy = IN_X - 2 * LIP_GAP, IN_Y - 2 * LIP_GAP
    lip = rounded_box(ox, oy, LIP_H, CORNER_R - WALL / 2, BASE_H - LIP_H)
    lip = lip.cut(rounded_box(ox - 2 * LIP_W, oy - 2 * LIP_W, LIP_H, 0.8, BASE_H - LIP_H))
    for x, y in POSTS:
        lip = lip.cut(cylinder(POST_D + 4, LIP_H + 1, x, y, BASE_H - LIP_H - 0.5))
    lid = lid.union(lip)
    # 四隅のねじ穴
    for x, y in POSTS:
        lid = lid.cut(cylinder(SCREW_HOLE_D, LID_T + 2, x, y, BASE_H - 1))
    # つまみの軸穴
    lid = lid.cut(cylinder(SHAFT_HOLE_D, LID_T + 2, ENC_CX, ENC_CY, BASE_H - 1))
    # OLED：裏にガラス用のくぼみ、表に窓
    gy = OLED_CY + OLED_GLASS_DY
    lid = lid.cut(cq.Workplane("XY").box(OLED_GLASS_X + 0.4, OLED_GLASS_Y + 0.4, OLED_RECESS, centered=(True, True, False))
                  .translate((OLED_CX, gy, BASE_H)))
    lid = lid.cut(cq.Workplane("XY").box(OLED_VIEW_X, OLED_VIEW_Y, LID_T + 2, centered=(True, True, False))
                  .edges("|Z").fillet(1.0).translate((OLED_CX, gy + OLED_VIEW_DY, BASE_H - 1)))
    # OLED の取付：ふたの裏から基板の穴に差すピン（差してから熱でつぶすか接着する）
    spacer_h = BASE_H - OLED_PCB_TOP    # ふたの下面から OLED 基板の上面まで
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = OLED_CX + sx * OLED_HOLE_DX / 2, OLED_CY + sy * OLED_HOLE_DY / 2
            if spacer_h > 0.05:
                lid = lid.union(cylinder(3.5, spacer_h, x, y, OLED_PCB_TOP))
            lid = lid.union(cylinder(OLED_HOLE_D - 0.2, OLED_PCB_T + 1.5, x, y, OLED_PCB_TOP - OLED_PCB_T - 1.5))
    # 音穴（サウンダの真上に φ2 を並べる）
    pts = [(SOUNDER_CX + dx * 3.2, SOUNDER_CY + dy * 3.2) for dx in range(-2, 3) for dy in range(-2, 3)
           if dx * dx + dy * dy <= 4]
    holes = cq.Workplane("XY").pushPoints(pts).circle(1.0).extrude(LID_T + 2).translate((0, 0, BASE_H - 1))
    lid = lid.cut(holes)
    return lid


def make_parts():
    """干渉確認用の部品（簡単な箱と円柱）"""
    p = {}
    board = cq.Workplane("XY").box(BOARD_X, BOARD_Y, BOARD_T, centered=(True, True, False)).translate((0, 0, BOARD_Z))
    for x, y in BOARD_HOLES:
        board = board.cut(cylinder(BOARD_HOLE_D, BOARD_T + 2, x, y, BOARD_Z - 1))
    p["基板"] = board
    p["XIAO"] = (cq.Workplane("XY").box(XIAO_X, XIAO_Y, XIAO_T, centered=(True, True, False))
                 .translate((XIAO_CX, XIAO_CY, XIAO_Z)))
    p["XIAO の USB-C"] = (cq.Workplane("XY").box(7.5, 9.0, 3.2, centered=(True, True, False))
                          .translate((XIAO_CX - XIAO_X / 2 + 3.0, XIAO_CY, XIAO_Z + XIAO_T)))
    # ピンヘッダー 7 ピン × 2 列（D 行と H 行）
    def header_row(r):
        return (cq.Workplane("XY").box(7 * PITCH, PITCH, HEADER_H, centered=(True, True, False))
                .translate((XIAO_CX, row_y(ROW[r]), BOARD_TOP)))
    p["XIAO のヘッダー"] = header_row("D").union(header_row("H"))
    p["DIP 化基板"] = (cq.Workplane("XY").box(ADAPTER_X, ADAPTER_Y, ADAPTER_T, centered=(True, True, False))
                      .translate((ENC_CX, ENC_CY, ADAPTER_Z)))
    p["エンコーダー"] = (cq.Workplane("XY").box(ENC_BODY_X, ENC_BODY_Y, ENC_BODY_H, centered=(True, True, False))
                        .translate((ENC_CX, ENC_CY, ENC_MOUNT_Z)))
    p["軸"] = cylinder(ENC_SHAFT_D, ENC_SHAFT_LEN, ENC_CX, ENC_CY, ENC_MOUNT_Z + ENC_BODY_H)
    gy = OLED_CY + OLED_GLASS_DY
    p["OLED 基板"] = (cq.Workplane("XY").box(OLED_PCB_X, OLED_PCB_Y, OLED_PCB_T, centered=(True, True, False))
                     .translate((OLED_CX, OLED_CY, OLED_PCB_TOP - OLED_PCB_T)))
    p["OLED ガラス"] = (cq.Workplane("XY").box(OLED_GLASS_X, OLED_GLASS_Y, OLED_GLASS_T, centered=(True, True, False))
                       .translate((OLED_CX, gy, OLED_PCB_TOP)))
    p["OLED のピン"] = (cq.Workplane("XY").box(10.2, 2.6, 8.5, centered=(True, True, False))
                       .translate((OLED_CX, OLED_CY + OLED_PCB_Y / 2 - 1.6, OLED_PCB_TOP - OLED_PCB_T - 8.5)))
    p["サウンダ"] = cylinder(SOUNDER_D, SOUNDER_H, SOUNDER_CX, SOUNDER_CY, BOARD_TOP)
    p["ジャック"] = cylinder_y(JACK_BODY_D, JACK_BODY_LEN, JACK_CX, IN_Y / 2 - JACK_BODY_LEN, JACK_CZ)
    return p


def volume(a, b):
    """2つの形が重なる体積（mm³）"""
    try:
        return a.intersect(b).val().Volume()
    except Exception:
        return 0.0


def check(base, lid, parts):
    """部品どうし・部品とケースの重なりを調べて表示する（基板に載る部品と基板の接触は除く）"""
    problems = []
    names = list(parts)
    allowed = {("基板", "XIAO のヘッダー"), ("XIAO", "XIAO のヘッダー"), ("XIAO", "XIAO の USB-C"),
               ("DIP 化基板", "エンコーダー"), ("エンコーダー", "軸"), ("OLED 基板", "OLED ガラス"),
               ("OLED 基板", "OLED のピン"), ("基板", "サウンダ")}
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
                continue  # 軸は穴を通る／OLED はピンで固定する
            v = volume(case, parts[n])
            if v > 0.5:
                problems.append(f"{case_name} と {n}：{v:.1f} mm³")
    return problems


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
    all_polys, all_cols = [], []   # 形をまとめて1つに描く（奥から順に重ねるため）
    for shape, color, alpha in shapes:
        verts, tris = shape.val().tessellate(0.2, 0.3)
        pts = [(v.x, v.y, v.z) for v in verts]
        for p in pts:
            lo = [min(a, b) for a, b in zip(lo, p)]
            hi = [max(a, b) for a, b in zip(hi, p)]
        polys = [[pts[i] for i in t] for t in tris]
        # 面の向きで明るさを変える（光は左上手前から）
        light = (-0.4, -0.5, 0.75)
        cols = []
        for a, b, c in polys:
            u = [b[k] - a[k] for k in range(3)]
            v = [c[k] - a[k] for k in range(3)]
            n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
            ln = sum(x * x for x in n) ** 0.5 or 1.0
            s = 0.45 + 0.55 * abs(sum(n[k] * light[k] for k in range(3)) / ln)
            cols.append((color[0] * s, color[1] * s, color[2] * s, alpha))
        all_polys += polys
        all_cols += cols
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
    print("ねじ：ふた＝M3 × 8 mm タッピング 4本、基板（30 列目）＝M3 × 6 mm タッピング 1本")
    problems = check(base, lid, parts)
    print("干渉：なし" if not problems else "干渉：\n  " + "\n  ".join(problems))

    cq.exporters.export(base, str(OUT / "case_base.step"))
    cq.exporters.export(lid, str(OUT / "case_lid.step"))
    cq.exporters.export(base, str(OUT / "case_base.stl"), tolerance=0.05, angularTolerance=0.2)
    # ふたは上面を下にして印刷するので、ひっくり返して書き出す
    lid_print = lid.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, LID_TOP))
    cq.exporters.export(lid_print, str(OUT / "case_lid.stl"), tolerance=0.05, angularTolerance=0.2)

    ghost = [(s, (0.2, 0.5, 0.9), 0.9) for n, s in parts.items()]
    render([(base, (0.85, 0.85, 0.82), 1.0)], OUT / "preview_base.png", 30, -130, "底ケース（左の壁に USB-C、奥の壁にジャック）")
    render([(lid, (0.85, 0.85, 0.82), 1.0)], OUT / "preview_lid.png", -35, -60, "ふた（裏から）")
    render([(base, (0.85, 0.85, 0.82), 1.0), (lid, (0.9, 0.75, 0.5), 1.0)],
           OUT / "preview_top.png", 40, -65, "組み立てた外観（OLED の窓・つまみの穴・音穴）")
    render([(base, (0.85, 0.85, 0.82), 0.25)] + ghost + [(lid, (0.9, 0.7, 0.4), 0.25)],
           OUT / "preview_assembly.png", 28, -55, "組み立て（部品は青）")
    print(f"書き出し：{OUT}")


if __name__ == "__main__":
    main()
