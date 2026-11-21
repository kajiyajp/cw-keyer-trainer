// 作成：2026-11-21
// 目的：シリアルコマンドの実装（空白区切り、大文字小文字を区別しない）
#include "protocol.h"
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

namespace {
constexpr int MAX_TOKENS = 4;
constexpr int TOKEN_LEN = 16;

// 行を大文字の単語に分ける。単語数を返す（多すぎ・長すぎは -1）
int tokenize(const char* line, char tok[MAX_TOKENS][TOKEN_LEN]) {
  int count = 0;
  const char* p = line;
  while (*p) {
    while (*p && isspace((unsigned char)*p)) ++p;
    if (!*p) break;
    if (count >= MAX_TOKENS) return -1;
    int len = 0;
    while (*p && !isspace((unsigned char)*p)) {
      if (len >= TOKEN_LEN - 1) return -1;
      tok[count][len++] = (char)toupper((unsigned char)*p++);
    }
    tok[count][len] = '\0';
    ++count;
  }
  return count;
}

// 全桁が数字で、範囲内なら true
bool parseRange(const char* s, long lo, long hi, long& out) {
  if (!*s) return false;
  char* end = nullptr;
  long v = strtol(s, &end, 10);
  if (*end != '\0' || v < lo || v > hi) return false;
  out = v;
  return true;
}

// SET コマンドを解釈する
CmdResult handleSet(const char* key, const char* val, Config& cfg) {
  long v;
  if (strcmp(key, "WPM") == 0) {
    if (!parseRange(val, WPM_MIN, WPM_MAX, v)) return CmdResult::Err;
    cfg.wpm = (uint8_t)v;
  } else if (strcmp(key, "MODE") == 0) {
    if (strcmp(val, "A") == 0) cfg.mode = KeyerMode::A;
    else if (strcmp(val, "B") == 0) cfg.mode = KeyerMode::B;
    else return CmdResult::Err;
  } else if (strcmp(key, "TONE") == 0) {
    if (!parseRange(val, TONE_MIN, TONE_MAX, v)) return CmdResult::Err;
    cfg.toneHz = (uint16_t)v;
  } else if (strcmp(key, "SIDETONE") == 0) {
    if (!parseRange(val, 0, 1, v)) return CmdResult::Err;
    cfg.sidetone = v == 1;
  } else if (strcmp(key, "KOCH") == 0) {
    if (!parseRange(val, KOCH_MIN, KOCH_MAX, v)) return CmdResult::Err;
    cfg.kochLevel = (uint8_t)v;
  } else if (strcmp(key, "ECHOLEN") == 0) {
    if (!parseRange(val, ECHOLEN_MIN, ECHOLEN_MAX, v)) return CmdResult::Err;
    cfg.echoLen = (uint8_t)v;
  } else if (strcmp(key, "HINT") == 0) {
    if (!parseRange(val, 0, 1, v)) return CmdResult::Err;
    cfg.hint = v == 1;
  } else {
    return CmdResult::Err;
  }
  return CmdResult::Ok;
}
}  // namespace

// 1行を解釈する
CmdResult handleLine(const char* line, Config& cfg) {
  char tok[MAX_TOKENS][TOKEN_LEN];
  int n = tokenize(line, tok);
  if (n == 3 && strcmp(tok[0], "SET") == 0) return handleSet(tok[1], tok[2], cfg);
  if (n == 2 && strcmp(tok[0], "GET") == 0 && strcmp(tok[1], "CONFIG") == 0) return CmdResult::GetConfig;
  if (n == 1 && strcmp(tok[0], "SAVE") == 0) return CmdResult::Save;
  return CmdResult::Err;
}

// 設定を1行にする
void formatConfig(const Config& cfg, char* out, size_t n) {
  snprintf(out, n, "CONFIG WPM=%u MODE=%c TONE=%u SIDETONE=%u KOCH=%u ECHOLEN=%u HINT=%u", cfg.wpm,
           cfg.mode == KeyerMode::A ? 'A' : 'B', cfg.toneHz, cfg.sidetone ? 1u : 0u, cfg.kochLevel,
           cfg.echoLen, cfg.hint ? 1u : 0u);
}

// 要素イベントを1行にする
void formatElement(char symbol, uint32_t ms, char* out, size_t n) {
  snprintf(out, n, "E %c %lu", symbol, (unsigned long)ms);
}

// 解読文字を1行にする
void formatChar(char c, char* out, size_t n) {
  snprintf(out, n, "C %c", c);
}
