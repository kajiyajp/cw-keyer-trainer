// 作成：2026-11-21
// 目的：OLED とボタン2つによるオフライン画面（メニュー／エコー練習／自由打鍵／設定）
#pragma once
#include <stdint.h>
#include "config.h"

// UI を初期化する。onConfigChanged は設定を変えたときに呼ばれる
void uiBegin(Config* cfg, void (*onConfigChanged)());
// 解読した文字を渡す（' ' は語間）
void uiOnChar(char c);
// 打鍵があったことを知らせる（打鍵中は描画を控えて HID のタイミングを守る）
void uiNoteActivity(uint32_t nowMs);
// 毎ループ呼ぶ（ボタン・画面遷移・描画）
void uiUpdate(uint32_t nowMs);
