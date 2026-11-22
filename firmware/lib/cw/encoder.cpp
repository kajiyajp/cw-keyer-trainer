// 作成：2026-11-22
// 目的：エンコーダー解読の実装。正しい隣どうしの変化だけを数え、チャタリングや飛んだ変化は打ち消し・無視する
#include "encoder.h"

namespace {
// [前の状態 × 4 ＋ 今の状態] → 移動量。順方向は 00 → 10 → 11 → 01 → 00（A が先に閉じる）
const int8_t STEP[16] = {
    // 今: 00  01  10  11
    0, -1, +1, 0,   // 前 00
    +1, 0, 0, -1,   // 前 01
    -1, 0, 0, +1,   // 前 10
    0, +1, -1, 0,   // 前 11
};
}  // namespace

int8_t QuadratureDecoder::update(bool a, bool b) {
  uint8_t cur = (a ? 2 : 0) | (b ? 1 : 0);
  if (cur == prev_) return 0;
  acc_ += STEP[prev_ * 4 + cur];
  prev_ = cur;
  if (cur != 0) return 0;
  // 止まり位置に戻った：半周期以上進んでいれば1クリックとみなす（途中で戻した分は打ち消し合う）
  int8_t r = acc_ >= 2 ? 1 : acc_ <= -2 ? -1 : 0;
  acc_ = 0;
  return r;
}
