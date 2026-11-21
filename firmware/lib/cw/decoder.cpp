// 作成：2026-11-21
// 目的：解読器の実装
#include "decoder.h"
#include "morse.h"

// 要素をバッファに追加する（あふれたら無効フラグ）
void Decoder::onElement(char symbol, uint32_t endMs) {
  if (len_ < MAX_LEN) {
    buf_[len_++] = symbol;
    buf_[len_] = '\0';
  } else {
    overflow_ = true;
  }
  lastEnd_ = endMs;
  wordPending_ = false;
  keying_ = false;
}

// 経過時間から文字・語間を確定する
char Decoder::poll(uint32_t nowMs) {
  if (keying_) return 0;
  uint32_t gap = nowMs - lastEnd_;
  if (len_ > 0 && gap >= 2u * ditMs_) {
    char c = overflow_ ? '*' : morseDecode(buf_);
    len_ = 0;
    buf_[0] = '\0';
    overflow_ = false;
    wordPending_ = true;
    return c;
  }
  if (len_ == 0 && wordPending_ && gap >= 5u * ditMs_) {
    wordPending_ = false;
    return ' ';
  }
  return 0;
}
