// 作成：2026-11-21
// 目的：文字列をモールスで再生する（ブロックしない。トーンの ON/OFF だけを返す）
#pragma once
#include <stdint.h>

class Player {
 public:
  // 文字列の再生を始める
  void start(const char* text, uint8_t wpm, uint32_t nowMs);
  // 指定時間だけトーンを鳴らす（正解の「ピッ」用）
  void beep(uint16_t ms, uint32_t nowMs);
  // 毎ループ呼び、今トーンを鳴らすべきかを返す
  bool update(uint32_t nowMs);
  // 再生中か
  bool busy() const { return busy_; }

 private:
  // 次に鳴らせる文字まで進める。語間をまたいだら true
  bool skipInvalid();

  char text_[24] = {0};
  uint8_t ci_ = 0;          // 文字の位置
  uint8_t ei_ = 0;          // 符号内の要素の位置
  uint16_t dit_ = 60;
  bool on_ = false;
  bool busy_ = false;
  bool beepMode_ = false;
  uint32_t next_ = 0;
};
