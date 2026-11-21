// 作成：2026-11-21
// 目的：キーヤーが出した要素列を文字に解読する（字間＝短点2個分、語間＝短点5個分で区切る）
#pragma once
#include <stdint.h>

class Decoder {
 public:
  // 短点の長さ ms を設定する
  void setDitMs(uint16_t ms) { ditMs_ = ms; }
  // 要素が始まったときに呼ぶ（打鍵中は文字を確定しない）
  void onKeyDown() { keying_ = true; }
  // 要素が終わったときに呼ぶ
  void onElement(char symbol, uint32_t endMs);
  // 文字確定で文字、語間で ' '、何もなければ 0 を返す
  char poll(uint32_t nowMs);

 private:
  static constexpr int MAX_LEN = 8;
  char buf_[MAX_LEN + 1] = {0};
  uint8_t len_ = 0;
  bool overflow_ = false;
  bool wordPending_ = false;
  bool keying_ = false;       // 要素を鳴らしている最中  // 文字を出した後、まだ語間を出していない
  uint32_t lastEnd_ = 0;
  uint16_t ditMs_ = 60;
};
