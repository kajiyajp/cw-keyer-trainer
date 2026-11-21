// 作成：2026-11-21
// 目的：XIAO RP2040 / RP2350 共通のピン割り当て
#pragma once
#include <Arduino.h>

constexpr uint8_t PIN_DIT = D0;     // 短点レバー（押すと LOW）
constexpr uint8_t PIN_DAH = D1;     // 長点レバー（押すと LOW）
constexpr uint8_t PIN_BUZZER = D2;  // パッシブ圧電ブザー
constexpr uint8_t PIN_BTN_MENU = D3;
constexpr uint8_t PIN_BTN_OK = D6;
constexpr uint8_t PIN_SDA = D4;
constexpr uint8_t PIN_SCL = D5;
