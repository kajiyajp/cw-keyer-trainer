// 作成：2026-11-21
// 目的：機器の設定値（フラッシュ保存・シリアル・OLED 設定画面で共通に使う）
#pragma once
#include <stdint.h>
#include "keyer.h"

struct Config {
  uint8_t wpm = 20;              // 5〜40
  KeyerMode mode = KeyerMode::B;
  uint16_t toneHz = 700;         // 400〜1200
  bool sidetone = true;
  uint8_t kochLevel = 2;         // 2〜41
  uint8_t echoLen = 1;           // エコー練習（Koch）の出題文字数 1〜5
  bool hint = true;              // エコー練習で出題の文字と符号を画面に出す
};

constexpr uint8_t WPM_MIN = 5, WPM_MAX = 40;
constexpr uint16_t TONE_MIN = 400, TONE_MAX = 1200;
constexpr uint8_t KOCH_MIN = 2, KOCH_MAX = 41;
constexpr uint8_t ECHOLEN_MIN = 1, ECHOLEN_MAX = 5;
