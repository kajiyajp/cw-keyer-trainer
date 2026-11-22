# 作成：2026-11-23
# 目的：エレキー本体の回路図（KiCad 10 で開けるプロジェクト）を hardware/ に生成する
#       接続は firmware/src/pins.h と実体配線図（tools/board_layout.py）に合わせる。
#       信号は線（ワイヤー）で、電源は GND / +3V3 の記号でつなぐ。
# 実行：python tools/make_schematic.py [KiCad の symbols フォルダ]
#       既定は %LOCALAPPDATA%/Programs/KiCad/10.0/share/kicad/symbols。
#       書き出したあと kicad-cli sch upgrade で KiCad 10 の形式にそろえる（tools/check_schematic.ps1）

import json
import os
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "hardware"
PROJECT = "cw-keyer"
LIB = "cw-keyer"  # 自作の部品ライブラリの名前
NS = uuid.UUID("6f1c3c64-9d0e-4f4e-9a59-0c2b0f6d6a11")  # uuid を毎回同じにするための名前空間
ROOT_UUID = str(uuid.uuid5(NS, "root"))


# 名前から決まった uuid を返す（生成し直しても差分が出ないように）
def uid(name):
    return str(uuid.uuid5(NS, name))


# 文字列を KiCad の "..." 形式にする
def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


# 文字の大きさの指定（effects）を返す
def eff(hide=False, justify=None):
    j = f" (justify {justify})" if justify else ""
    h = " (hide yes)" if hide else ""
    return f"{h} (effects (font (size 1.27 1.27)){j})"


# ---- KiCad の標準ライブラリから部品の定義を取り出す ----

# 標準ライブラリ lib の部品 name の定義（トップレベルの (symbol ...)）を、名前を "lib:name" にして返す
def std_symbol(symdir, lib, name):
    s = (Path(symdir) / f"{lib}.kicad_sym").read_text(encoding="utf-8")
    start = s.index(f'\n\t(symbol "{name}"') + 1
    depth, i = 0, start
    while True:
        c = s[i]
        if c == '"':  # 文字列の中のかっこは数えない
            i += 1
            while s[i] != '"':
                i += 2 if s[i] == "\\" else 1
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                break
        i += 1
    body = s[start:i + 1]
    if "(extends" in body:
        raise SystemExit(f"{lib}:{name} は extends を使っているので対応していない")
    return body.replace(f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1)


# 部品の定義からピンの一覧 {番号: (x, y, 向き)} を返す（座標は部品の中、y は上が＋）
def pins_of(body):
    out = {}
    for m in re.finditer(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)[\s\S]*?\(number "([^"]*)"', body):
        x, y, a, num = m.groups()
        out[num] = (float(x), float(y), int(float(a)))
    return out


# ---- 自作の部品（標準ライブラリに無いもの） ----

# 自作部品の定義を作る。pins は [(番号, 名前, 種類, x, y, 向き)]、box は本体の四角 (x1, y1, x2, y2)
def custom_symbol(name, ref, value, desc, box, pins, extra=""):
    p = []
    for num, pname, ptype, x, y, a in pins:
        p.append(f"(pin {ptype} line (at {x} {y} {a}) (length 2.54)"
                 f" (name {q(pname)}{eff()}) (number {q(num)}{eff()}))")
    x1, y1, x2, y2 = box
    return (f'(symbol {q(name)} (exclude_from_sim no) (in_bom yes) (on_board yes)\n'
            f'  (property "Reference" {q(ref)} (at {x1} {y1 + 1.27} 0){eff(justify="left bottom")})\n'
            f'  (property "Value" {q(value)} (at {x1} {y2 - 1.27} 0){eff(justify="left top")})\n'
            f'  (property "Footprint" "" (at 0 0 0){eff(hide=True)})\n'
            f'  (property "Datasheet" "" (at 0 0 0){eff(hide=True)})\n'
            f'  (property "Description" {q(desc)} (at 0 0 0){eff(hide=True)})\n'
            f'  (symbol {q(name + "_0_1")} (rectangle (start {x1} {y1}) (end {x2} {y2})'
            f' (stroke (width 0.254) (type default)) (fill (type background))){extra})\n'
            f'  (symbol {q(name + "_1_1")}\n    ' + "\n    ".join(p) + ")\n)")


# XIAO RP2040：ピン番号は実物のまま。並びは配線が交差しないよう実物と変えている
# （左：上から D2・D0・D1・D3・D4・D5・D6、右：上から 3V3・5V・D10・D9・D8・D7・GND。実物の並びは docs/hardware.md のピン表）
XIAO_LEFT = [("3", "D2"), ("1", "D0"), ("2", "D1"), ("4", "D3"), ("5", "D4/SDA"), ("6", "D5/SCL"), ("7", "D6")]
XIAO_RIGHT = [("12", "3V3", "power_out"), ("14", "5V", "power_out"),
              ("11", "D10", "bidirectional"), ("10", "D9", "bidirectional"), ("9", "D8", "bidirectional"),
              ("8", "D7", "bidirectional"), ("13", "GND", "power_out")]


# 自作部品の定義を {名前: 定義} で返す
def custom_symbols():
    xiao = [(n, nm, "bidirectional", -12.7, 7.62 - 2.54 * i, 0) for i, (n, nm) in enumerate(XIAO_LEFT)]
    xiao += [(n, nm, t, 12.7, 7.62 - 2.54 * i, 180) for i, (n, nm, t) in enumerate(XIAO_RIGHT)]
    # つまみ：信号は左に上から 2 青・3 赤・B・A・4 押しボタン、GND の C と 1 共通は下（2色 LED は共通カソード）
    enc = [("2", "LED_B", "passive", -10.16, 5.08, 0), ("3", "LED_R", "passive", -10.16, 2.54, 0),
           ("B", "B", "passive", -10.16, 0, 0), ("A", "A", "passive", -10.16, -2.54, 0),
           ("4", "SW", "passive", -10.16, -5.08, 0),
           ("C", "C", "passive", -2.54, -10.16, 90), ("1", "COM", "passive", 2.54, -10.16, 90)]
    # OLED：実物の並びは GND・VCC・SCL・SDA。電源を端に寄せて VCC を上、GND を下にする
    oled = [("2", "VCC", "power_in", -10.16, 3.81, 0), ("4", "SDA", "bidirectional", -10.16, 1.27, 0),
            ("3", "SCL", "input", -10.16, -1.27, 0), ("1", "GND", "power_in", -10.16, -3.81, 0)]
    return {
        "XIAO_RP2040": custom_symbol("XIAO_RP2040", "U", "XIAO_RP2040", "Seeed Studio XIAO RP2040",
                                     (-10.16, 10.16, 10.16, -10.16), xiao),
        "EC12_LED2": custom_symbol("EC12_LED2", "SW", "EC12_LED2", "押しボタン・2色 LED 付きロータリーエンコーダー（秋月 P-05772＋DIP 化基板 P-07240）",
                                   (-7.62, 7.62, 7.62, -7.62), enc),
        "OLED_I2C": custom_symbol("OLED_I2C", "DS", "OLED_I2C", "0.96 インチ OLED（SSD1306/SSD1315、I2C 4 ピン）",
                                  (-7.62, 6.35, 7.62, -6.35), oled),
    }


# ---- 回路図に置く部品と、ピンごとのつなぎ先 ----
# つなぎ先："ネット名"（ROUTES の線でつなぐ）、"GND" / "+3V3"（電源記号）、None（未接続の印）
# 向き：rot＝回転（90＝横向き）、mirror_x＝上下反転、mirror_y＝左右反転
PARTS = [
    # (参照名, lib_id, 値, 置く位置 (x, y), 向き, {ピン番号: つなぎ先}, 追加の欄)
    ("U1", f"{LIB}:XIAO_RP2040", "XIAO RP2040", (127, 101.6), {},
     {"1": "DIT", "2": "DAH", "3": "D2", "4": None, "5": "SDA", "6": "SCL", "7": "KNOB_SW",
      "8": "KNOB_A", "9": "KNOB_B", "10": "D9", "11": "D10", "12": "+3V3", "13": "GND", "14": None},
     {"Note": "Seeed Studio XIAO RP2040"}),
    ("J1", "Connector_Audio:AudioJack3", "3.5mm ステレオジャック", (76.2, 99.06), {"mirror_x": True},
     {"T": "DIT", "R": "DAH", "S": "GND"},
     {"Note": "パネル取付。先端＝短点、リング＝長点、根元＝GND"}),
    ("R1", "Device:R", "2.2k〜10k", (101.6, 81.28), {"rot": 90}, {"1": "SND", "2": "D2"},
     {"Note": "音量調整。音が大きすぎなければジャンパー線でよい"}),
    ("BZ1", "Device:Buzzer", "圧電サウンダ", (92.71, 83.82), {"mirror_y": True}, {"1": "SND", "2": "GND"},
     {"Note": "ASIN B0CZJ5DGDH（耳付き）。PWM で音の高さが変わることを実機で確認済み"}),
    ("R2", "Device:R", "100", (154.94, 88.9), {}, {"1": "LED_B", "2": "D10"}, {"Note": "つまみの青 LED の電流制限"}),
    ("R3", "Device:R", "1k", (162.56, 88.9), {}, {"1": "LED_R", "2": "D9"}, {"Note": "つまみの赤 LED の電流制限"}),
    ("SW1", f"{LIB}:EC12_LED2", "EC12 24クリック 2色LED", (182.88, 104.14), {},
     {"A": "KNOB_A", "C": "GND", "B": "KNOB_B", "4": "KNOB_SW", "3": "LED_R", "2": "LED_B", "1": "GND"},
     {"Note": "秋月 P-05772 ＋ DIP 化基板 P-07240"}),
    ("DS1", f"{LIB}:OLED_I2C", "OLED 0.96\" I2C", (88.9, 121.92), {"mirror_y": True},
     {"1": "GND", "2": "+3V3", "3": "SCL", "4": "SDA"},
     {"Note": "SSD1306/SSD1315 128×64。電源は必ず 3V3"}),
]

# 信号の線：(ネット名, [始点のピン "参照名:番号", 曲がり角 (x, y)..., 終点のピン])。
# 曲がり角は、別のネットの線と重ならず、線の端が別の線の途中に乗らない位置にしてある（乗るとショートになる）
ROUTES = [
    ("DIT", ["U1:1", "J1:T"]),
    ("DAH", ["U1:2", "J1:R"]),
    ("D2", ["U1:3", (109.22, 93.98), (109.22, 81.28), "R1:2"]),
    ("SND", ["R1:1", "BZ1:1"]),
    ("SDA", ["U1:5", (106.68, 104.14), (106.68, 120.65), "DS1:4"]),
    ("SCL", ["U1:6", (109.22, 106.68), (109.22, 123.19), "DS1:3"]),
    ("KNOB_SW", ["U1:7", (111.76, 109.22), (111.76, 133.35), (165.1, 133.35), (165.1, 109.22), "SW1:4"]),
    ("D10", ["U1:11", (154.94, 99.06), "R2:2"]),
    ("D9", ["U1:10", (162.56, 101.6), "R3:2"]),
    ("LED_B", ["R2:1", (154.94, 81.28), (170.18, 81.28), (170.18, 99.06), "SW1:2"]),
    ("LED_R", ["R3:1", (162.56, 83.82), (167.64, 83.82), (167.64, 101.6), "SW1:3"]),
    ("KNOB_B", ["U1:9", "SW1:B"]),
    ("KNOB_A", ["U1:8", "SW1:A"]),
]

WIRE = 5.08  # 電源記号へ出す線の長さ

# 参照名・値の文字の位置（部品の置き場所からのずれ。回路図の座標）。ここに無い部品は右横に置く
TEXT_AT = {  # 電源記号は名前を記号の先（GND は下、+3V3 は上）に書く
    "GND": ((0, 3.81), (0, 3.81)), "+3V3": ((0, -3.81), (0, -3.81)),
    "U1": ((0, -12.7), (0, 12.7)), "J1": ((0, -6.35), (-2.54, 6.35)), "BZ1": ((-2.54, -5.08), (-2.54, 6.35)),
    "R1": ((0, -2.54), (0, 2.54)), "R2": ((-3.81, -1.27), (-3.81, 1.27)), "R3": ((-3.81, -1.27), (-3.81, 1.27)),
    "SW1": ((0, -10.16), (0, 21.59)), "DS1": ((0, -8.89), (0, 8.89)),
}


# 部品の中の座標・向きを、部品の向き（回転・反転）で変えて返す（y は上が＋のまま）
def orient(o, x, y):
    if o.get("rot") == 90:  # 左回りに 90°
        x, y = -y, x
    if o.get("mirror_y"):
        x = -x
    if o.get("mirror_x"):
        y = -y
    return x, y


# 部品の中の座標 (x, y) を回路図の座標にする（回路図は y が下向き）
def place(at, o, x, y):
    x, y = orient(o, x, y)
    return round(at[0] + x, 4), round(at[1] - y, 4)


# ピンの外向き（部品の外へ向かう向き）を回路図の座標で返す。angle はピンから本体へ向かう向き
def outward(o, angle):
    import math
    dx, dy = orient(o, round(math.cos(math.radians(angle))), round(math.sin(math.radians(angle))))
    return -dx, dy  # 本体と逆向き。回路図は y が下向きなので y はそのまま（-(-dy)）


# 点 p が線 (a, b)（縦か横）の上にあるかを返す（端を含む）
def on_seg(p, a, b):
    return (min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])
            and (a[0] == b[0] == p[0] or a[1] == b[1] == p[1]))


# 別のネットの線どうし・線とほかのピンが触れていないか調べる。触れていたら止める
# （KiCad はジャンクションの無い T 字や重なりを、ファイルの上では別のネットとして扱うが、
#   画面で編集すると自動でつながってショートになるので、ここで防ぐ）
def check_geometry(segs, pin_xy, pin_net):
    errors = []
    for i, (n1, a1, b1) in enumerate(segs):
        for n2, a2, b2 in segs[i + 1:]:
            if n1 != n2 and any(on_seg(p, a2, b2) for p in (a1, b1)) | any(on_seg(p, a1, b1) for p in (a2, b2)):
                errors.append(f"{n1} の線 {a1}-{b1} と {n2} の線 {a2}-{b2} が触れている")
        for pin, xy in pin_xy.items():
            if pin_net[pin] != n1 and on_seg(xy, a1, b1):
                errors.append(f"{n1} の線 {a1}-{b1} がピン {pin}（{pin_net[pin]}）に触れている")
    if errors:
        raise SystemExit("線が別のネットに触れています：\n  " + "\n  ".join(errors))


# 回路図の中身（文字列）と、自作部品の定義 {名前: 定義} を返す
def build(symdir):
    lib_defs = {}
    for lib, name in [("Device", "R"), ("Device", "Buzzer"), ("Connector_Audio", "AudioJack3"),
                      ("power", "GND"), ("power", "+3V3")]:
        lib_defs[f"{lib}:{name}"] = std_symbol(symdir, lib, name)
    custom = custom_symbols()
    for name, body in custom.items():
        lib_defs[f"{LIB}:{name}"] = body.replace(f'(symbol "{name}"', f'(symbol "{LIB}:{name}"', 1)

    items, pwr_n, segs = [], [0], []  # segs：引いた線の一覧 (ネット, 始点, 終点)。形の検査に使う

    # 線を 1 本引く
    def wire(p1, p2, key, net):
        segs.append((net, p1, p2))
        items.append(f'(wire (pts (xy {p1[0]} {p1[1]}) (xy {p2[0]} {p2[1]})) (stroke (width 0) (type default))'
                     f' (uuid {q(uid("w" + key))}))')

    # 部品を 1 つ置く（電源記号も同じ関数で置く）
    def symbol(lib_id, ref, value, at, o=None, props=None, hide_ref=False, text_at=None):
        o = o or {}
        pins = pins_of(lib_defs[lib_id])
        is_pwr = ref.startswith("#")
        if text_at:  # 指定の位置に中央ぞろえ
            (rdx, rdy), (vdx, vdy) = text_at
            rj = None
        else:  # 部品の右横に左ぞろえ
            (rdx, rdy), (vdx, vdy), rj = (2.54, -1.27), (2.54, 1.27), "left"
        rx, ry, vx, vy = at[0] + rdx, at[1] + rdy, at[0] + vdx, at[1] + vdy
        ta = o.get("rot", 0)  # 文字の角度（回転した部品でも文字が横向きになるよう、部品と同じ角度を書く）
        mirror = " (mirror x)" if o.get("mirror_x") else " (mirror y)" if o.get("mirror_y") else ""
        lines = [f'(symbol (lib_id {q(lib_id)}) (at {at[0]} {at[1]} {o.get("rot", 0)}){mirror} (unit 1)'
                 f' (exclude_from_sim no) (in_bom {"no" if is_pwr else "yes"}) (on_board yes) (dnp no)'
                 f' (uuid {q(uid("sym" + ref))})',
                 f'  (property "Reference" {q(ref)} (at {rx} {ry} {ta}){eff(hide=hide_ref, justify=rj)})',
                 f'  (property "Value" {q(value)} (at {vx} {vy} {ta}){eff(justify=rj)})',
                 f'  (property "Footprint" "" (at {at[0]} {at[1]} 0){eff(hide=True)})',
                 f'  (property "Datasheet" "" (at {at[0]} {at[1]} 0){eff(hide=True)})']
        for k, v in (props or {}).items():
            lines.append(f'  (property {q(k)} {q(v)} (at {at[0]} {at[1]} 0){eff(hide=True)})')
        for num in pins:
            lines.append(f'  (pin {q(num)} (uuid {q(uid(ref + "pin" + num))}))')
        lines.append(f'  (instances (project {q(PROJECT)} (path {q("/" + ROOT_UUID)} (reference {q(ref)}) (unit 1)))))')
        items.append("\n".join(lines))
        return pins

    pin_xy, pin_net = {}, {}  # "参照名:番号" → 回路図の座標 / つなぎ先
    for ref, lib_id, value, at, o, conn, props in PARTS:
        pins = symbol(lib_id, ref, value, at, o, props=props, text_at=TEXT_AT.get(ref))
        if set(pins) != set(conn):
            raise SystemExit(f"{ref} のピン {sorted(pins)} とつなぎ先 {sorted(conn)} が合わない")
        for num, (px, py, a) in pins.items():
            net = conn[num]
            x, y = place(at, o, px, py)
            pin_xy[f"{ref}:{num}"], pin_net[f"{ref}:{num}"] = (x, y), net
            if net is None:
                items.append(f'(no_connect (at {x} {y}) (uuid {q(uid(ref + "nc" + num))}))')
            elif net in ("GND", "+3V3"):
                # 電源記号：GND は下、+3V3 は上へ。横に出た線は L 字に曲げてから置く
                dx, dy = outward(o, a)
                x2, y2 = round(x + dx * WIRE, 4), round(y + dy * WIRE, 4)
                wire((x, y), (x2, y2), ref + "p" + num, net)
                turn = 1 if net == "GND" else -1
                if dy == 0:
                    y3 = round(y2 + turn * 2.54, 4)
                    wire((x2, y2), (x2, y3), ref + "p2" + num, net)
                    y2 = y3
                elif dy != turn:
                    raise SystemExit(f"{ref} の {num} 番は {net} と逆向きに出ている（部品のピンの並びを直す）")
                pwr_n[0] += 1
                symbol(f"power:{net}", f"#PWR{pwr_n[0]:02d}", net, (x2, y2), hide_ref=True, text_at=TEXT_AT[net])

    # 信号の線を引く。始点と終点のピンのつなぎ先が、そのネットと合っているか確かめる
    routed = set()
    for net, path in ROUTES:
        for p in (path[0], path[-1]):
            if pin_net.get(p) != net:
                raise SystemExit(f"{net} の線の端 {p} のつなぎ先は {pin_net.get(p)}")
            routed.add(p)
        pts = [pin_xy[p] if isinstance(p, str) else p for p in path]
        for k in range(len(pts) - 1):
            (x1, y1), (x2, y2) = pts[k], pts[k + 1]
            if x1 != x2 and y1 != y2:
                raise SystemExit(f"{net} の {k} 本目の線が斜め：{pts[k]} → {pts[k + 1]}")
            wire(pts[k], pts[k + 1], f"{net}{k}", net)
    missing = [p for p, n in pin_net.items() if n not in (None, "GND", "+3V3") and p not in routed]
    if missing:
        raise SystemExit(f"線が引かれていないピン：{missing}")
    check_geometry(segs, pin_xy, pin_net)

    notes = [
        ("CW Keyer Trainer 本体（XIAO RP2040）", 25.4, 25.4),
        ("・電源は GND / +3V3 の記号でつながっている（同じ記号どうしが接続）", 25.4, 30.48),
        ("・D0/D1/D6/D7/D8 は内部プルアップ（外付け抵抗なし）。つまみのチャタリングはソフトで処理", 25.4, 35.56),
        ("・D3 と 5V は未使用", 25.4, 40.64),
    ]
    for i, (t, x, y) in enumerate(notes):
        items.append(f'(text {q(t)} (exclude_from_sim no) (at {x} {y} 0){eff(justify="left bottom")}'
                     f' (uuid {q(uid("note" + str(i)))}))')

    sch = (f'(kicad_sch (version 20250114) (generator "make_schematic") (generator_version "1.0")\n'
           f' (uuid {q(ROOT_UUID)}) (paper "A4")\n'
           f' (title_block (title "CW Keyer Trainer") (date "2026-11-23") (rev "1")'
           f' (comment 1 "生成：tools/make_schematic.py（手で直したら生成し直さないこと）"))\n'
           f' (lib_symbols\n' + "\n".join(lib_defs.values()) + ")\n" +
           "\n".join(items) +
           '\n (sheet_instances (path "/" (page "1")))\n)\n')
    return sch, custom


# ファイルを書き出す
def main():
    symdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.environ["LOCALAPPDATA"], "Programs", "KiCad", "10.0", "share", "kicad", "symbols")
    sch, custom = build(symdir)
    OUT.mkdir(exist_ok=True)
    (OUT / f"{PROJECT}.kicad_sch").write_text(sch, encoding="utf-8", newline="\n")
    (OUT / f"{LIB}.kicad_sym").write_text(
        '(kicad_symbol_lib (version 20241209) (generator "make_schematic") (generator_version "1.0")\n'
        + "\n".join(custom.values()) + "\n)\n", encoding="utf-8", newline="\n")
    (OUT / "sym-lib-table").write_text(
        f'(sym_lib_table\n  (version 7)\n  (lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}.kicad_sym")'
        f'(options "")(descr "CW Keyer Trainer の自作部品"))\n)\n', encoding="utf-8", newline="\n")
    pro = OUT / f"{PROJECT}.kicad_pro"
    if not pro.exists():  # KiCad が設定を書き足すので、無いときだけ作る
        pro.write_text(json.dumps({"meta": {"filename": f"{PROJECT}.kicad_pro", "version": 3}}, indent=2) + "\n",
                       encoding="utf-8", newline="\n")
    print(f"書き出し：{OUT}")


if __name__ == "__main__":
    main()
