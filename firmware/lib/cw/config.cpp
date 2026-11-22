// 作成：2026-11-22
// 目的：設定値を1段階ずつ動かす（エンコーダーで増やす・減らす）
#include "config.h"

namespace {
// lo〜hi の値 v を step ずつ dir の向きに動かし、端を越えたら反対の端へ
template <typename T>
T wrapStep(T v, T lo, T hi, T step, int8_t dir) {
  if (dir > 0) return v + step > hi ? lo : (T)(v + step);
  return v < lo + step ? hi : (T)(v - step);
}
}  // namespace

void configStep(Config& c, ConfigItem item, int8_t dir) {
  if (dir == 0) return;
  switch (item) {
    case ConfigItem::Wpm: c.wpm = wrapStep<uint8_t>(c.wpm, WPM_MIN, WPM_MAX, 1, dir); break;
    case ConfigItem::Mode: {
      uint8_t m = wrapStep<uint8_t>((uint8_t)c.mode, 0, (uint8_t)KeyerMode::Ultimatic, 1, dir);
      c.mode = (KeyerMode)m;
      break;
    }
    case ConfigItem::Tone: c.toneHz = wrapStep<uint16_t>(c.toneHz, TONE_MIN, TONE_MAX, TONE_STEP, dir); break;
    case ConfigItem::Sidetone: c.sidetone = !c.sidetone; break;
    case ConfigItem::Koch: c.kochLevel = wrapStep<uint8_t>(c.kochLevel, KOCH_MIN, KOCH_MAX, 1, dir); break;
    case ConfigItem::EchoLen: c.echoLen = wrapStep<uint8_t>(c.echoLen, ECHOLEN_MIN, ECHOLEN_MAX, 1, dir); break;
    case ConfigItem::Hint: c.hint = !c.hint; break;
    default: break;
  }
}
