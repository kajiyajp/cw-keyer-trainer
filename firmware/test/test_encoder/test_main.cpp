// 作成：2026-11-22
// 目的：ロータリーエンコーダー解読と、設定値を ±1 段階動かす処理のテスト
#include <unity.h>
#include "config.h"
#include "encoder.h"

void setUp() {}
void tearDown() {}

namespace {
// 状態の並び（bit1＝A、bit0＝B）を順に渡し、返り値の合計を返す
int feed(QuadratureDecoder& d, const uint8_t* seq, int n) {
  int sum = 0;
  for (int i = 0; i < n; ++i) sum += d.update(seq[i] & 2, seq[i] & 1);
  return sum;
}
const uint8_t CW[] = {0b10, 0b11, 0b01, 0b00};   // A が先に閉じる向き
const uint8_t CCW[] = {0b01, 0b11, 0b10, 0b00};  // B が先に閉じる向き
}  // namespace

// 1クリック進めると +1、止まり位置に戻るまでは 0
void test_one_click_cw() {
  QuadratureDecoder d;
  TEST_ASSERT_EQUAL(0, d.update(true, false));
  TEST_ASSERT_EQUAL(0, d.update(true, true));
  TEST_ASSERT_EQUAL(0, d.update(false, true));
  TEST_ASSERT_EQUAL(1, d.update(false, false));
}

void test_one_click_ccw() {
  QuadratureDecoder d;
  TEST_ASSERT_EQUAL(-1, feed(d, CCW, 4));
}

// 3クリック続けて回す
void test_multiple_clicks() {
  QuadratureDecoder d;
  int sum = 0;
  for (int i = 0; i < 3; ++i) sum += feed(d, CW, 4);
  TEST_ASSERT_EQUAL(3, sum);
  for (int i = 0; i < 2; ++i) sum += feed(d, CCW, 4);
  TEST_ASSERT_EQUAL(1, sum);
}

// 止まり位置付近のチャタリング（00 ↔ 10 の往復）は数えない
void test_bounce_ignored() {
  QuadratureDecoder d;
  const uint8_t s[] = {0b10, 0b00, 0b10, 0b00, 0b10, 0b00};
  TEST_ASSERT_EQUAL(0, feed(d, s, 6));
}

// 途中まで回して戻したら 0
void test_half_turn_back() {
  QuadratureDecoder d;
  const uint8_t s[] = {0b10, 0b11, 0b10, 0b00};
  TEST_ASSERT_EQUAL(0, feed(d, s, 4));
}

// 途中でチャタリングしても、最後まで回せば1クリック
void test_bounce_mid_click() {
  QuadratureDecoder d;
  const uint8_t s[] = {0b10, 0b11, 0b10, 0b11, 0b01, 0b11, 0b01, 0b00};
  TEST_ASSERT_EQUAL(1, feed(d, s, 8));
}

// 設定値：上限で最小に、最小で上限に折り返す
void test_setting_step_wraps() {
  Config c;
  c.wpm = WPM_MAX;
  configStep(c, ConfigItem::Wpm, +1);
  TEST_ASSERT_EQUAL(WPM_MIN, c.wpm);
  configStep(c, ConfigItem::Wpm, -1);
  TEST_ASSERT_EQUAL(WPM_MAX, c.wpm);
  c.toneHz = TONE_MIN;
  configStep(c, ConfigItem::Tone, -1);
  TEST_ASSERT_EQUAL(TONE_MAX, c.toneHz);
  configStep(c, ConfigItem::Tone, -1);
  TEST_ASSERT_EQUAL(TONE_MAX - TONE_STEP, c.toneHz);
}

// MODE は A → B → U → A、逆回しで A → U
void test_setting_step_mode_and_bool() {
  Config c;
  c.mode = KeyerMode::A;
  configStep(c, ConfigItem::Mode, +1);
  TEST_ASSERT(c.mode == KeyerMode::B);
  configStep(c, ConfigItem::Mode, +1);
  TEST_ASSERT(c.mode == KeyerMode::Ultimatic);
  configStep(c, ConfigItem::Mode, +1);
  TEST_ASSERT(c.mode == KeyerMode::A);
  configStep(c, ConfigItem::Mode, -1);
  TEST_ASSERT(c.mode == KeyerMode::Ultimatic);
  c.sidetone = true;
  configStep(c, ConfigItem::Sidetone, -1);
  TEST_ASSERT_FALSE(c.sidetone);
  c.kochLevel = KOCH_MIN;
  configStep(c, ConfigItem::Koch, -1);
  TEST_ASSERT_EQUAL(KOCH_MAX, c.kochLevel);
  c.echoLen = ECHOLEN_MAX;
  configStep(c, ConfigItem::EchoLen, +1);
  TEST_ASSERT_EQUAL(ECHOLEN_MIN, c.echoLen);
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_one_click_cw);
  RUN_TEST(test_one_click_ccw);
  RUN_TEST(test_multiple_clicks);
  RUN_TEST(test_bounce_ignored);
  RUN_TEST(test_half_turn_back);
  RUN_TEST(test_bounce_mid_click);
  RUN_TEST(test_setting_step_wraps);
  RUN_TEST(test_setting_step_mode_and_bool);
  return UNITY_END();
}
