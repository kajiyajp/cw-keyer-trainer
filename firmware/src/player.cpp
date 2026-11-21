// 作成：2026-11-21
// 目的：モールス再生の実装（要素間1・字間3・語間7 短点）
#include "player.h"
#include "morse.h"

// 空白と符号表にない文字を飛ばす。空白を飛ばしたら true
bool Player::skipInvalid() {
  bool word = false;
  while (text_[ci_] && (text_[ci_] == ' ' || morseEncode(text_[ci_]) == nullptr)) {
    if (text_[ci_] == ' ') word = true;
    ++ci_;
  }
  return word;
}

// 文字列を大文字で取り込み、再生を始める
void Player::start(const char* text, uint8_t wpm, uint32_t nowMs) {
  uint8_t i = 0;
  for (; text[i] && i < sizeof(text_) - 1; ++i) {
    char c = text[i];
    text_[i] = (c >= 'a' && c <= 'z') ? c - 'a' + 'A' : c;
  }
  text_[i] = '\0';
  ci_ = ei_ = 0;
  dit_ = 1200 / (wpm ? wpm : 20);
  beepMode_ = false;
  on_ = false;
  skipInvalid();
  busy_ = text_[ci_] != '\0';
  next_ = nowMs;
}

// ビープを始める
void Player::beep(uint16_t ms, uint32_t nowMs) {
  beepMode_ = true;
  busy_ = true;
  on_ = true;
  next_ = nowMs + ms;
}

// 時刻に応じてトーンを切り替える
bool Player::update(uint32_t nowMs) {
  if (!busy_) return false;
  if ((int32_t)(nowMs - next_) < 0) return on_;

  if (beepMode_) {
    on_ = false;
    busy_ = false;
    return false;
  }
  const char* code = morseEncode(text_[ci_]);
  if (!on_) {
    on_ = true;
    next_ = nowMs + (code[ei_] == '.' ? dit_ : dit_ * 3);
    return true;
  }
  // 要素が終わった → 次の要素・文字・語へ
  on_ = false;
  ++ei_;
  if (code[ei_]) {
    next_ = nowMs + dit_;
    return false;
  }
  ei_ = 0;
  ++ci_;
  bool word = skipInvalid();
  if (!text_[ci_]) {
    busy_ = false;
    return false;
  }
  next_ = nowMs + dit_ * (word ? 7 : 3);
  return false;
}
