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
constexpr uint16_t TONE_STEP = 50;

// OLED 設定画面の項目（並び順＝画面の表示順）
enum class ConfigItem : uint8_t { Wpm, Mode, Tone, Sidetone, Koch, EchoLen, Hint, Count };

// 項目の値を dir（+1 / -1）の向きに1段階動かす。範囲の端では反対の端へ折り返す
void configStep(Config& c, ConfigItem item, int8_t dir);
