// 作成：2026-11-21
// 目的：符号表（morseEncode / morseDecode / KOCH_ORDER）のテスト
#include <unity.h>
#include "morse.h"

void setUp() {}
void tearDown() {}

// 文字→符号の変換
void test_encode() {
  TEST_ASSERT_EQUAL_STRING(".-", morseEncode('A'));
  TEST_ASSERT_EQUAL_STRING(".-", morseEncode('a'));
  TEST_ASSERT_EQUAL_STRING("-----", morseEncode('0'));
  TEST_ASSERT_EQUAL_STRING("-...-", morseEncode('='));
  TEST_ASSERT_NULL(morseEncode('#'));
}

// 符号→文字の変換
void test_decode() {
  TEST_ASSERT_EQUAL_CHAR('K', morseDecode("-.-"));
  TEST_ASSERT_EQUAL_CHAR('?', morseDecode("..--.."));
  TEST_ASSERT_EQUAL_CHAR('*', morseDecode("........."));
  TEST_ASSERT_EQUAL_CHAR('*', morseDecode(""));
}

// Koch 順の全文字が符号表にあること
void test_koch_all_encodable() {
  for (const char* p = KOCH_ORDER; *p; ++p) TEST_ASSERT_NOT_NULL(morseEncode(*p));
}

// 文字列を符号の並びにする（表示用）。未対応文字は飛ばし、バッファからはみ出さない
void test_pattern() {
  char b[32];
  morsePattern("CQ", b, sizeof b);
  TEST_ASSERT_EQUAL_STRING("-.-. --.-", b);
  morsePattern("K#M", b, sizeof b);
  TEST_ASSERT_EQUAL_STRING("-.- --", b);
  morsePattern("", b, sizeof b);
  TEST_ASSERT_EQUAL_STRING("", b);
  char s[6];
  morsePattern("CQ", s, sizeof s);
  TEST_ASSERT_EQUAL_STRING("-.-. ", s);
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_encode);
  RUN_TEST(test_decode);
  RUN_TEST(test_koch_all_encodable);
  RUN_TEST(test_pattern);
  return UNITY_END();
}
