// 作成：2026-11-21
// 目的：XIAO RP2040 / RP2350 共通のピン割り当て（D0〜D10 をすべて使う）
#pragma once
#include <Arduino.h>

constexpr uint8_t PIN_DIT = D0;     // 短点レバー（押すと LOW）
constexpr uint8_t PIN_DAH = D1;     // 長点レバー（押すと LOW）
constexpr uint8_t PIN_BUZZER = D2;  // パッシブ圧電サウンダ
// D3 は空き（将来の拡張用）
constexpr uint8_t PIN_SDA = D4;
constexpr uint8_t PIN_SCL = D5;
constexpr uint8_t PIN_KNOB_SW = D6;   // つまみの押しボタン（押すと LOW）。タクトスイッチでも可
constexpr uint8_t PIN_KNOB_A = D7;    // つまみ A 相（閉じると LOW）。回す向きが逆なら A と B を入れ替える
constexpr uint8_t PIN_KNOB_B = D8;    // つまみ B 相
constexpr uint8_t PIN_KNOB_RED = D9;  // つまみの赤 LED（HIGH で点灯）
constexpr uint8_t PIN_KNOB_BLUE = D10;  // つまみの青 LED（HIGH で点灯）
