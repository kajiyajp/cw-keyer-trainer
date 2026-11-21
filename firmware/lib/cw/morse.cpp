// 作成：2026-11-21
// 目的：符号表の実装（文字と符号のペアを線形探索）
#include "morse.h"
#include <string.h>

namespace {
struct Entry { char c; const char* code; };

const Entry TABLE[] = {
  {'A', ".-"},    {'B', "-..."},  {'C', "-.-."},  {'D', "-.."},   {'E', "."},
  {'F', "..-."},  {'G', "--."},   {'H', "...."},  {'I', ".."},    {'J', ".---"},
  {'K', "-.-"},   {'L', ".-.."},  {'M', "--"},    {'N', "-."},    {'O', "---"},
  {'P', ".--."},  {'Q', "--.-"},  {'R', ".-."},   {'S', "..."},   {'T', "-"},
  {'U', "..-"},   {'V', "...-"},  {'W', ".--"},   {'X', "-..-"},  {'Y', "-.--"},
  {'Z', "--.."},
  {'0', "-----"}, {'1', ".----"}, {'2', "..---"}, {'3', "...--"}, {'4', "....-"},
  {'5', "....."}, {'6', "-...."}, {'7', "--..."}, {'8', "---.."}, {'9', "----."},
  {'.', ".-.-.-"}, {',', "--..--"}, {'?', "..--.."}, {'/', "-..-."}, {'=', "-...-"},
  {'-', "-....-"},
};
constexpr int TABLE_LEN = sizeof(TABLE) / sizeof(TABLE[0]);
}  // namespace

// 文字を符号にする（小文字は大文字として扱う）
const char* morseEncode(char c) {
  if (c >= 'a' && c <= 'z') c = c - 'a' + 'A';
  for (int i = 0; i < TABLE_LEN; ++i) {
    if (TABLE[i].c == c) return TABLE[i].code;
  }
  return nullptr;
}

// 符号を文字にする
char morseDecode(const char* pattern) {
  if (pattern == nullptr || *pattern == '\0') return '*';
  for (int i = 0; i < TABLE_LEN; ++i) {
    if (strcmp(TABLE[i].code, pattern) == 0) return TABLE[i].c;
  }
  return '*';
}

// 文字ごとの符号を空白でつなぐ
void morsePattern(const char* text, char* out, size_t n) {
  if (n == 0) return;
  size_t len = 0;
  out[0] = '\0';
  for (const char* p = text; *p; ++p) {
    const char* code = morseEncode(*p);
    if (!code) continue;
    if (len > 0 && len + 1 < n) out[len++] = ' ';
    for (const char* q = code; *q && len + 1 < n; ++q) out[len++] = *q;
  }
  out[len] = '\0';
}
