// 作成：2026-11-21
// 目的：USB シリアルの1行1コマンドの解釈と、機器から送る行の形式
#pragma once
#include <stddef.h>
#include <stdint.h>
#include "config.h"

enum class CmdResult : uint8_t { Ok, Err, GetConfig, Save };

// 1行を解釈して cfg を更新する（失敗時は cfg を変えない）
CmdResult handleLine(const char* line, Config& cfg);
// "CONFIG WPM=20 MODE=B TONE=700 SIDETONE=1 KOCH=2" を作る
void formatConfig(const Config& cfg, char* out, size_t n);
// "E . 62" を作る
void formatElement(char symbol, uint32_t ms, char* out, size_t n);
// "C A" を作る
void formatChar(char c, char* out, size_t n);
