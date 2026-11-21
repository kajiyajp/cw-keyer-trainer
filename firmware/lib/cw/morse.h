// 作成：2026-11-21
// 目的：欧文モールス符号表（英数字・記号）と Koch 法の文字順
#pragma once
#include <stddef.h>

// Koch 法で文字を追加していく順番（41 文字）
constexpr const char* KOCH_ORDER = "KMURESNAPTLWI.JZ=FOY,VG5/Q92H38B?47C1D60X";

// 文字を ".-" 形式の符号にする。未対応文字は nullptr
const char* morseEncode(char c);

// 文字列を "-.-. --.-" のような符号の並びにする（表示用）。未対応文字は飛ばし、n-1 文字で切る
void morsePattern(const char* text, char* out, size_t n);

// ".-" 形式の符号を文字にする。一致しなければ '*'
char morseDecode(const char* pattern);
