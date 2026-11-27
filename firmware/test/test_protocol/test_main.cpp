// 作成：2026-11-21
// 目的：シリアルコマンドの解釈と出力形式のテスト
#include <unity.h>
#include "protocol.h"

void setUp() {}
void tearDown() {}

void test_set_wpm() {
  Config c;
  TEST_ASSERT(handleLine("SET WPM 25", c) == CmdResult::Ok);
  TEST_ASSERT_EQUAL(25, c.wpm);
}

// トーンは上限 5000Hz まで設定できる（圧電ブザーは高めの音のほうがよく鳴り、年を取っても聞こえる高さ）
void test_set_tone_max() {
  Config c;
  TEST_ASSERT(handleLine("SET TONE 5000", c) == CmdResult::Ok);
  TEST_ASSERT_EQUAL(5000, c.toneHz);
}

// 出題の文字数とヒント
void test_set_echolen_hint() {
  Config c;
  TEST_ASSERT_EQUAL(1, c.echoLen);
  TEST_ASSERT_TRUE(c.hint);
  TEST_ASSERT(handleLine("SET ECHOLEN 3", c) == CmdResult::Ok);
  TEST_ASSERT_EQUAL(3, c.echoLen);
  TEST_ASSERT(handleLine("SET ECHOLEN 0", c) == CmdResult::Err);
  TEST_ASSERT(handleLine("SET ECHOLEN 6", c) == CmdResult::Err);
  TEST_ASSERT_EQUAL(3, c.echoLen);
  TEST_ASSERT(handleLine("SET HINT 0", c) == CmdResult::Ok);
  TEST_ASSERT_FALSE(c.hint);
  TEST_ASSERT(handleLine("SET HINT 2", c) == CmdResult::Err);
}

// 範囲外は ERR で設定は変わらない
void test_out_of_range() {
  Config c;
  TEST_ASSERT(handleLine("SET WPM 999", c) == CmdResult::Err);
  TEST_ASSERT(handleLine("SET WPM 4", c) == CmdResult::Err);
  TEST_ASSERT(handleLine("SET TONE 5100", c) == CmdResult::Err);
  TEST_ASSERT(handleLine("SET KOCH 42", c) == CmdResult::Err);
  TEST_ASSERT_EQUAL(20, c.wpm);
  TEST_ASSERT_EQUAL(3000, c.toneHz);
}

// 数字以外が混ざったら ERR
void test_not_a_number() {
  Config c;
  TEST_ASSERT(handleLine("SET WPM 2x", c) == CmdResult::Err);
  TEST_ASSERT(handleLine("SET WPM", c) == CmdResult::Err);
  TEST_ASSERT_EQUAL(20, c.wpm);
}

void test_unknown_cmd() {
  Config c;
  TEST_ASSERT(handleLine("SET FOO 1", c) == CmdResult::Err);
  TEST_ASSERT(handleLine("HELLO", c) == CmdResult::Err);
}

void test_empty_line() {
  Config c;
  TEST_ASSERT(handleLine("", c) == CmdResult::Err);
  TEST_ASSERT(handleLine("\r", c) == CmdResult::Err);
}

// 小文字・CRLF・余分な空白でも通る
void test_crlf_lowercase() {
  Config c;
  TEST_ASSERT(handleLine("set mode a\r", c) == CmdResult::Ok);
  TEST_ASSERT(c.mode == KeyerMode::A);
  TEST_ASSERT(handleLine("SET MODE U", c) == CmdResult::Ok);
  TEST_ASSERT(c.mode == KeyerMode::Ultimatic);
  TEST_ASSERT(handleLine("SET MODE X", c) == CmdResult::Err);
  TEST_ASSERT(c.mode == KeyerMode::Ultimatic);
  TEST_ASSERT(handleLine("  SET   SIDETONE  0 ", c) == CmdResult::Ok);
  TEST_ASSERT_FALSE(c.sidetone);
}

void test_get_and_save() {
  Config c;
  TEST_ASSERT(handleLine("GET CONFIG", c) == CmdResult::GetConfig);
  TEST_ASSERT(handleLine("SAVE", c) == CmdResult::Save);
}

void test_format_config() {
  Config c; char b[96];
  formatConfig(c, b, sizeof b);
  TEST_ASSERT_EQUAL_STRING("CONFIG WPM=20 MODE=B TONE=3000 SIDETONE=1 KOCH=2 ECHOLEN=1 HINT=1", b);
  c.mode = KeyerMode::Ultimatic;
  formatConfig(c, b, sizeof b);
  TEST_ASSERT_EQUAL_STRING("CONFIG WPM=20 MODE=U TONE=3000 SIDETONE=1 KOCH=2 ECHOLEN=1 HINT=1", b);
}

void test_format_element_and_char() {
  char b[16];
  formatElement('.', 62, b, sizeof b);
  TEST_ASSERT_EQUAL_STRING("E . 62", b);
  formatChar('A', b, sizeof b);
  TEST_ASSERT_EQUAL_STRING("C A", b);
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_set_wpm);
  RUN_TEST(test_set_tone_max);
  RUN_TEST(test_set_echolen_hint);
  RUN_TEST(test_out_of_range);
  RUN_TEST(test_not_a_number);
  RUN_TEST(test_unknown_cmd);
  RUN_TEST(test_empty_line);
  RUN_TEST(test_crlf_lowercase);
  RUN_TEST(test_get_and_save);
  RUN_TEST(test_format_config);
  RUN_TEST(test_format_element_and_char);
  return UNITY_END();
}
