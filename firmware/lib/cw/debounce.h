// 作成：2026-11-21
// 目的：パドル接点のチャタリング除去（最初の変化は即反映し、その後一定時間の変化を無視）
#pragma once
#include <stdint.h>

class Debouncer {
 public:
  explicit Debouncer(uint8_t ms = 5) : ms_(ms) {}

  // 生の入力を渡し、チャタリング除去後の状態を返す
  bool update(uint32_t nowMs, bool raw) {
    if (locked_ && (int32_t)(nowMs - lockUntil_) < 0) return stable_;
    locked_ = false;
    if (raw != stable_) {
      stable_ = raw;
      lockUntil_ = nowMs + ms_;
      locked_ = true;
    }
    return stable_;
  }

 private:
  uint8_t ms_;
  bool stable_ = false;
  bool locked_ = false;
  uint32_t lockUntil_ = 0;
};
