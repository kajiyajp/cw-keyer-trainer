# 作成：2026-11-23
# 目的：KiCad が書き出したネットリストを、firmware/src/pins.h から組み立てた「正しい接続」と突き合わせる
#       回路図の生成スクリプト（make_schematic.py）とは別に正解を作るので、どちらかを間違えると失敗する
# 実行：python tools/check_schematic.py <ネットリスト（kicadsexpr 形式）>

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESISTORS = {"R1", "R2", "R3", "R4"}  # 向きのない 2 端子部品（どちらのピンでもよい）


# pins.h から {定数名: XIAO のピン番号} を返す（D0〜D6＝1〜7 番、D7〜D10＝8〜11 番）
def xiao_pins():
    text = (ROOT / "firmware" / "src" / "pins.h").read_text(encoding="utf-8")
    out = {}
    for name, n in re.findall(r"constexpr uint8_t (PIN_\w+) = D(\d+);", text):
        out[name] = str(int(n) + 1)
    return out


# 正しい接続をネットごとの集合の一覧で返す（要素は "参照名.ピン"。抵抗は参照名だけ）
def expected():
    p = xiao_pins()
    u = lambda k: "U1." + p[k]
    return [
        {u("PIN_DIT"), "J1.T"},
        {u("PIN_DAH"), "J1.R"},
        # ブザー：D2 → R1 → Q1 のベース。5V → R4 → BZ1(+)、BZ1(−) → RV1 → Q1 のコレクタ。D1 はブザーと逆向きに並列
        {u("PIN_BUZZER"), "R1"},
        {"R1", "Q1.3"},
        {"U1.14", "R4"},                        # 5V
        {"R4", "BZ1.1", "D1.1"},                # ブザーの＋とダイオードのカソード
        {"BZ1.2", "D1.2", "RV1.3"},             # ブザーの−とダイオードのアノード
        {"RV1.1", "RV1.2", "Q1.2"},             # ボリューム（真ん中の足を 1 とつなぐ）とコレクタ
        {u("PIN_SDA"), "DS1.4"},
        {u("PIN_SCL"), "DS1.3"},
        {u("PIN_KNOB_SW"), "SW1.4"},
        {u("PIN_KNOB_A"), "SW1.A"},
        {u("PIN_KNOB_B"), "SW1.B"},
        {u("PIN_KNOB_RED"), "R3"},
        {"R3", "SW1.3"},
        {u("PIN_KNOB_BLUE"), "R2"},
        {"R2", "SW1.2"},
        {"U1.13", "J1.S", "Q1.1", "SW1.C", "SW1.1", "DS1.1"},  # GND（Q1.1 はエミッタ）
        {"U1.12", "DS1.2"},                                     # 3V3
    ]


# ネットリストから、2 つ以上の部品がつながるネットを集合の一覧で返す
def actual(netlist_text):
    nets = []
    for body in re.findall(r"\(net\s+\(code[^)]*\)\s*\(name [^)]*\)(.*?)\n\s*\)\s*(?=\(net|\)\s*\)\s*$)",
                           netlist_text, re.S):
        nodes = set()
        for ref, pin in re.findall(r'\(node\s+\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', body):
            nodes.add(ref if ref in RESISTORS else f"{ref}.{pin}")
        if len(nodes) >= 2:
            nets.append(nodes)
    return nets


# 突き合わせて、違いを表示する。一致すれば 0、違えば 1 を返す
def main():
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    want = sorted(map(sorted, expected()))
    got = sorted(map(sorted, actual(text)))
    missing = [n for n in want if n not in got]
    extra = [n for n in got if n not in want]
    for n in missing:
        print("足りない接続：", " - ".join(n))
    for n in extra:
        print("余分な接続　：", " - ".join(n))
    # 未使用のピン（D3）がどこにもつながっていないこと
    used = {x for n in got for x in n}
    for pin, name in [("U1.4", "D3")]:
        if pin in used:
            print(f"未使用のはずの {name} がつながっている")
            missing.append([pin])
    if missing or extra:
        print("NG：回路図と pins.h が合いません")
        return 1
    print(f"OK：{len(want)} 本のネットがすべて pins.h と一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
