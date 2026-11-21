// 作成：2026-11-21
// 目的：設定をフラッシュ（EEPROM エミュレーション）に保存・読み込みする
#pragma once
#include "config.h"

// 保存済みの設定を読む。未保存・壊れていたら既定値にして false
bool settingsLoad(Config& c);
// 保存を予約する（書き込み中は core1 が止まるので、打鍵していないときに settingsService が行う）
void settingsRequestSave(const Config& c);
// 毎ループ呼ぶ。予約があり、打鍵も再生もしていなければ保存する
void settingsService();
