// 作成：2026-11-21
// 目的：USB 複合デバイス（CDC シリアル＋HID キーボード）。core0 からだけ呼ぶ
#pragma once
#include <stddef.h>
#include <stdint.h>

// HID で送るキー。iPhone で keydown/keyup が取れるか実機確認して決める（仮：F13）
constexpr uint8_t HID_KEYCODE = 0x68;  // HID_KEY_F13

// USB を初期化する（setup() の最初に呼ぶ）
void usbBegin();
// 毎ループ呼ぶ（HID の送り残しを送る）
void usbService();
// キーヤー出力を HID キーの押下／解放として送る
void usbKey(bool down);
// CDC から1行読む（ブロックしない。行がそろったら true）
bool usbReadLine(char* buf, size_t n);
// CDC へ1行書く（未接続・送信バッファ不足なら捨てる）
void usbPrintLine(const char* s);
