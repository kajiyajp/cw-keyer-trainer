// 作成：2026-11-22
// 目的：ロータリーエンコーダー（A/B 2相）の解読。1クリック＝1周期の型（EC12 24クリックなど）で、クリックごとに ±1 を返す
#pragma once
#include <stdint.h>

class QuadratureDecoder {
 public:
  // A/B 接点の状態を渡す（true＝閉じている＝ピンが LOW）
  // 1クリック進んで止まり位置（両方開き）に戻ったら +1（A が先に閉じる向き）か -1、それ以外は 0
  int8_t update(bool a, bool b);

 private:
  uint8_t prev_ = 0;  // 前回の状態（bit1＝A、bit0＝B）
  int8_t acc_ = 0;    // 止まり位置を出てからの移動量（1周期で ±4）
};
