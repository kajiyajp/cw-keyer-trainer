// 作成：2026-11-21
// 目的：エコー練習の出題と採点のテスト
#include <unity.h>
#include <ctype.h>
#include <stdio.h>
#include <string.h>
#include "trainer.h"

void setUp() {}
void tearDown() {}

// level=2 なら 'K' 'M' だけ、長さ 5
void test_koch_uses_only_level_chars() {
  EchoTrainer t(123);
  for (int i = 0; i < 50; ++i) {
    const char* p = t.nextPrompt(PromptKind::Koch, 2);
    TEST_ASSERT_EQUAL(5, (int)strlen(p));
    for (const char* c = p; *c; ++c) TEST_ASSERT_TRUE(*c == 'K' || *c == 'M');
  }
}

// コールサインは英数字のみ・4〜6 文字・数字を1つ含む
void test_callsign_format() {
  EchoTrainer t(7);
  for (int i = 0; i < 100; ++i) {
    const char* p = t.nextPrompt(PromptKind::Callsign, 2);
    int len = (int)strlen(p), digits = 0;
    TEST_ASSERT_TRUE(len >= 4 && len <= 6);
    for (const char* c = p; *c; ++c) {
      TEST_ASSERT_TRUE(isupper((unsigned char)*c) || isdigit((unsigned char)*c));
      if (isdigit((unsigned char)*c)) ++digits;
    }
    TEST_ASSERT_EQUAL(1, digits);
  }
}

// 略語は一覧のどれか
void test_abbrev_from_list() {
  EchoTrainer t(9);
  const char* list = " CQ DE TU 73 RST UR 5NN QTH OP ";
  for (int i = 0; i < 30; ++i) {
    char key[12];
    snprintf(key, sizeof key, " %s ", t.nextPrompt(PromptKind::Abbrev, 2));
    TEST_ASSERT_NOT_NULL(strstr(list, key));
  }
}

// 出題どおりに打てば正解（' ' は無視）
void test_correct_answer() {
  EchoTrainer t(1);
  char prompt[16];
  strcpy(prompt, t.nextPrompt(PromptKind::Koch, 5));
  for (const char* c = prompt; *c; ++c) {
    TEST_ASSERT_FALSE(t.answerComplete());
    t.onChar(*c);
    t.onChar(' ');
  }
  TEST_ASSERT_TRUE(t.answerComplete());
  TEST_ASSERT_TRUE(t.isCorrect());
}

// 1文字違えば不正解
void test_wrong_answer() {
  EchoTrainer t(1);
  char prompt[16];
  strcpy(prompt, t.nextPrompt(PromptKind::Koch, 5));
  for (int i = 0; prompt[i]; ++i) t.onChar(i == 2 ? '*' : prompt[i]);
  TEST_ASSERT_TRUE(t.answerComplete());
  TEST_ASSERT_FALSE(t.isCorrect());
}

// 回答だけ消しても出題は変わらず、打ち直せる
void test_reset_answer_keeps_prompt() {
  EchoTrainer t(3);
  char prompt[16];
  strcpy(prompt, t.nextPrompt(PromptKind::Abbrev, 2));
  t.onChar('X');
  t.resetAnswer();
  TEST_ASSERT_EQUAL_STRING(prompt, t.prompt());
  for (const char* c = prompt; *c; ++c) t.onChar(*c);
  TEST_ASSERT_TRUE(t.isCorrect());
}

// 同じ seed なら同じ出題
void test_same_seed_same_prompt() {
  EchoTrainer a(42), b(42);
  char pa[16];
  strcpy(pa, a.nextPrompt(PromptKind::Callsign, 2));
  TEST_ASSERT_EQUAL_STRING(pa, b.nextPrompt(PromptKind::Callsign, 2));
}

// Koch の出題は指定した文字数（1〜5 に収める）
void test_koch_length() {
  EchoTrainer t(7);
  TEST_ASSERT_EQUAL(1, strlen(t.nextPrompt(PromptKind::Koch, 2, 1)));
  TEST_ASSERT_EQUAL(3, strlen(t.nextPrompt(PromptKind::Koch, 2, 3)));
  TEST_ASSERT_EQUAL(1, strlen(t.nextPrompt(PromptKind::Koch, 2, 0)));
  TEST_ASSERT_EQUAL(5, strlen(t.nextPrompt(PromptKind::Koch, 2, 9)));
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_koch_uses_only_level_chars);
  RUN_TEST(test_callsign_format);
  RUN_TEST(test_abbrev_from_list);
  RUN_TEST(test_correct_answer);
  RUN_TEST(test_wrong_answer);
  RUN_TEST(test_reset_answer_keeps_prompt);
  RUN_TEST(test_same_seed_same_prompt);
  RUN_TEST(test_koch_length);
  return UNITY_END();
}
