// 作成：2026-11-21
// 目的：core1 で動く打鍵エンジン（パドル・キーヤー・ブザー・再生）と、core0 との受け渡し
#pragma once
#include <stdint.h>
#include "config.h"

// core1 から core0 へ送る打鍵イベント
struct EngineEvent {
  bool started;      // true：要素開始／false：要素終了
  char symbol;       // '.' or '-'
  uint32_t durationMs;
  uint32_t atMs;     // 発生時刻（millis）
};

// core0 の setup() で最初に呼ぶ（キューを用意し、core1 を動かし始める）
void engineBegin(const Config& cfg);
// 設定を core1 に反映する
void engineApply(const Config& cfg);
// 文字列をブザーで再生する（再生中はパドルを無視）
void enginePlay(const char* text, uint8_t wpm);
// ビープを鳴らす
void engineBeep(uint16_t hz, uint16_t ms);
// 再生中か
bool enginePlayerBusy();
// 打鍵も再生もしていないか（フラッシュ書き込みなど core1 を止める処理はこのときだけ行う）
bool engineIdle();
// 打鍵イベントを1つ取り出す（なければ false）
bool engineNextEvent(EngineEvent& e);
