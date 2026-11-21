// 作成：2026-11-21
// 目的：解読器（要素列 → 文字・語間）のテスト（短点 60ms 前提）
#include <unity.h>
#include "decoder.h"

void setUp() {}
void tearDown() {}

// K（-.-）を入れて最後の要素から短点2個分後に 'K'
void test_decode_k() {
  Decoder d; d.setDitMs(60);
  d.onElement('-', 180); d.onElement('.', 300); d.onElement('-', 600);
  TEST_ASSERT_EQUAL_CHAR(0, d.poll(700));
  TEST_ASSERT_EQUAL_CHAR('K', d.poll(720));
  TEST_ASSERT_EQUAL_CHAR(0, d.poll(730));
}

// A（.-）：長点を鳴らしている最中は文字を確定しない（E と T に分かれない）
void test_no_split_while_keying() {
  Decoder d; d.setDitMs(60);
  d.onKeyDown(); d.onElement('.', 60);
  d.onKeyDown();                                // 120ms から長点
  TEST_ASSERT_EQUAL_CHAR(0, d.poll(200));       // 短点終了から 140ms 経過しても打鍵中
  d.onElement('-', 300);
  TEST_ASSERT_EQUAL_CHAR('A', d.poll(420));
}

// 文字の後さらに待つと ' ' が1回だけ出る
void test_word_space_once() {
  Decoder d; d.setDitMs(60);
  d.onElement('.', 60);
  TEST_ASSERT_EQUAL_CHAR('E', d.poll(180));
  TEST_ASSERT_EQUAL_CHAR(0, d.poll(300));
  TEST_ASSERT_EQUAL_CHAR(' ', d.poll(360));
  TEST_ASSERT_EQUAL_CHAR(0, d.poll(1000));
}

// 未知の符号（短点9個）は '*'
void test_unknown_pattern() {
  Decoder d; d.setDitMs(60);
  for (int i = 0; i < 9; ++i) d.onElement('.', 60 + i * 120);
  TEST_ASSERT_EQUAL_CHAR('*', d.poll(10000));
}

// 要素を 20 個入れても落ちずに '*'、その後は正常に戻る
void test_overflow_safe() {
  Decoder d; d.setDitMs(60);
  for (int i = 0; i < 20; ++i) d.onElement('-', 180 + i * 240);
  TEST_ASSERT_EQUAL_CHAR('*', d.poll(20000));
  d.onElement('-', 20180);
  TEST_ASSERT_EQUAL_CHAR('T', d.poll(20300));
}

// 何も入れずに poll → 0（語間も出ない）
void test_no_char_while_idle() {
  Decoder d; d.setDitMs(60);
  TEST_ASSERT_EQUAL_CHAR(0, d.poll(0));
  TEST_ASSERT_EQUAL_CHAR(0, d.poll(100000));
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_decode_k);
  RUN_TEST(test_no_split_while_keying);
  RUN_TEST(test_word_space_once);
  RUN_TEST(test_unknown_pattern);
  RUN_TEST(test_overflow_safe);
  RUN_TEST(test_no_char_while_idle);
  return UNITY_END();
}
