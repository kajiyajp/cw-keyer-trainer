// 作成：2026-11-21
// 目的：iambic キーヤーとチャタリング除去のテスト（20WPM = 短点 60ms 前提）
#include <unity.h>
#include <string.h>
#include "keyer.h"
#include "debounce.h"

void setUp() {}
void tearDown() {}

namespace {
// 1ms ごとの keyDown を記録するバッファ
bool tone[3000];
// 終わった要素の記号を順に記録する
char sent[32];
int sentLen;
uint32_t lastDuration;

// パドル入力の時刻表：[fromMs, toMs) の間 dit/dah を押す
struct Press { uint32_t from, to; };

// from〜to まで 1ms 刻みで keyer を回す
void run(IambicKeyer& k, uint32_t from, uint32_t to, Press dit, Press dah) {
  for (uint32_t t = from; t < to; ++t) {
    bool d = t >= dit.from && t < dit.to;
    bool h = t >= dah.from && t < dah.to;
    KeyerEvent e = k.update(t, d, h);
    if (e.ended && sentLen < 31) { sent[sentLen++] = e.symbol; sent[sentLen] = 0; lastDuration = e.durationMs; }
    tone[t] = k.keyDown();
  }
}

void reset() { memset(tone, 0, sizeof tone); sent[0] = 0; sentLen = 0; lastDuration = 0; }
const Press NONE = {0, 0};
}  // namespace

// 短点1回：0〜59ms 鳴って、その後は鳴らない
void test_single_dit() {
  reset(); IambicKeyer k; k.setWpm(20);
  run(k, 0, 400, {0, 10}, NONE);
  TEST_ASSERT_TRUE(tone[0]); TEST_ASSERT_TRUE(tone[59]);
  TEST_ASSERT_FALSE(tone[60]); TEST_ASSERT_FALSE(tone[119]); TEST_ASSERT_FALSE(tone[200]);
  TEST_ASSERT_EQUAL_STRING(".", sent);
  TEST_ASSERT_EQUAL_UINT16(60, k.ditMs());
}

// 長点 = 180ms
void test_dah_length() {
  reset(); IambicKeyer k; k.setWpm(20);
  run(k, 0, 500, NONE, {0, 10});
  TEST_ASSERT_TRUE(tone[179]); TEST_ASSERT_FALSE(tone[180]);
  TEST_ASSERT_EQUAL_STRING("-", sent);
}

// 両方押しっぱなし → 交互に続く
void test_squeeze_alternates() {
  reset(); IambicKeyer k; k.setWpm(20);
  run(k, 0, 1000, {0, 2000}, {0, 2000});
  TEST_ASSERT_EQUAL_STRING(".-.-.", sent);  // . 0-59, - 120-299, . 360-419, - 480-659, . 720-779
  TEST_ASSERT_TRUE(tone[120]); TEST_ASSERT_TRUE(tone[360]);
}

// 両押し中、長点の途中で両方離す：B は短点を1つ追加、A は追加しない
void test_mode_b_extra_element() {
  reset(); IambicKeyer b; b.setWpm(20); b.setMode(KeyerMode::B);
  run(b, 0, 1000, {0, 200}, {0, 200});
  TEST_ASSERT_EQUAL_STRING(".-.", sent);

  reset(); IambicKeyer a; a.setWpm(20); a.setMode(KeyerMode::A);
  run(a, 0, 1000, {0, 200}, {0, 200});
  TEST_ASSERT_EQUAL_STRING(".-", sent);
}

// 長点の途中で短点を一瞬押して離す → 長点の後に短点（A でも B でも）
void test_dit_memory() {
  reset(); IambicKeyer k; k.setWpm(20); k.setMode(KeyerMode::A);
  run(k, 0, 600, {50, 70}, {0, 10});
  TEST_ASSERT_EQUAL_STRING("-.", sent);
  TEST_ASSERT_TRUE(tone[240]);   // 長点 0-179、間 180-239、短点 240-299
}

// 長点中に速度変更 → 今の長点は 180ms のまま、次の短点は 120ms（10WPM）
void test_wpm_change_next_element() {
  reset(); IambicKeyer k; k.setWpm(20);
  run(k, 0, 100, {50, 70}, {0, 10});
  k.setWpm(10);
  run(k, 100, 700, NONE, NONE);
  TEST_ASSERT_TRUE(tone[179]); TEST_ASSERT_FALSE(tone[180]);
  TEST_ASSERT_TRUE(tone[240]); TEST_ASSERT_TRUE(tone[359]); TEST_ASSERT_FALSE(tone[360]);
  TEST_ASSERT_EQUAL_UINT32(120, lastDuration);
}

// 要素の終わりで記号と長さを報告する
void test_event_reports_duration() {
  reset(); IambicKeyer k; k.setWpm(20);
  run(k, 0, 300, NONE, {0, 10});
  TEST_ASSERT_EQUAL_STRING("-", sent);
  TEST_ASSERT_EQUAL_UINT32(180, lastDuration);
}

// 速度は 5〜40 に丸める
void test_wpm_clamped() {
  IambicKeyer k;
  k.setWpm(100); TEST_ASSERT_EQUAL_UINT16(30, k.ditMs());   // 40WPM
  k.setWpm(1);   TEST_ASSERT_EQUAL_UINT16(240, k.ditMs());  // 5WPM
}

// チャタリング除去：最初の変化はすぐ反映し、その後 5ms のバタつきは無視
void test_debouncer_ignores_bounce() {
  Debouncer d(5);
  TEST_ASSERT_FALSE(d.update(0, false));
  TEST_ASSERT_TRUE(d.update(1, true));    // 押した瞬間に反映（遅れなし）
  TEST_ASSERT_TRUE(d.update(2, false));   // バタつき → 無視
  TEST_ASSERT_TRUE(d.update(3, true));
  TEST_ASSERT_TRUE(d.update(5, false));   // まだロック中
  TEST_ASSERT_TRUE(d.update(6, true));    // ロック明け、押されたまま
  TEST_ASSERT_FALSE(d.update(20, false)); // 離したらすぐ反映
}

// ロック中に離されて、そのまま離れていたら、ロック明けに反映
void test_debouncer_settles_after_lock() {
  Debouncer d(5);
  d.update(0, true);
  TEST_ASSERT_TRUE(d.update(3, false));
  TEST_ASSERT_FALSE(d.update(6, false));
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_single_dit);
  RUN_TEST(test_dah_length);
  RUN_TEST(test_squeeze_alternates);
  RUN_TEST(test_mode_b_extra_element);
  RUN_TEST(test_dit_memory);
  RUN_TEST(test_wpm_change_next_element);
  RUN_TEST(test_event_reports_duration);
  RUN_TEST(test_wpm_clamped);
  RUN_TEST(test_debouncer_ignores_bounce);
  RUN_TEST(test_debouncer_settles_after_lock);
  return UNITY_END();
}
