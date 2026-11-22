// 作成：2026-11-21
// 目的：設定保存の実装（マジック値で未初期化を判定し、範囲外は既定値に戻す）
#include "settings.h"
#include <EEPROM.h>
#include "engine.h"

namespace {
constexpr uint32_t MAGIC = 0x43574B32;  // "CWK2"（Config に echoLen / hint を足したので更新）
struct Stored {
  uint32_t magic;
  Config cfg;
};
bool started = false;
Config pending;
bool hasPending = false;

void ensureBegin() {
  if (!started) {
    EEPROM.begin(256);
    started = true;
  }
}

// 各値が範囲内か
bool valid(const Config& c) {
  return c.wpm >= WPM_MIN && c.wpm <= WPM_MAX && c.toneHz >= TONE_MIN && c.toneHz <= TONE_MAX &&
         c.kochLevel >= KOCH_MIN && c.kochLevel <= KOCH_MAX &&
         c.echoLen >= ECHOLEN_MIN && c.echoLen <= ECHOLEN_MAX &&
         (c.mode == KeyerMode::A || c.mode == KeyerMode::B || c.mode == KeyerMode::Ultimatic);
}
}  // namespace

bool settingsLoad(Config& c) {
  ensureBegin();
  Stored s;
  EEPROM.get(0, s);
  if (s.magic != MAGIC || !valid(s.cfg)) {
    c = Config{};
    return false;
  }
  c = s.cfg;
  return true;
}

void settingsRequestSave(const Config& c) {
  pending = c;
  hasPending = true;
}

void settingsService() {
  if (!hasPending || !engineIdle()) return;
  hasPending = false;
  ensureBegin();
  Stored s{MAGIC, pending};
  EEPROM.put(0, s);
  EEPROM.commit();  // この間 core1 は止まる
}
