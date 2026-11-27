// 作成：2026-11-21
// 目的：打鍵エンジンの実装。OLED 描画などで core0 が止まっても打鍵タイミングが崩れないよう core1 で回す
#include "engine.h"
#include <Arduino.h>
#include <pico/util/queue.h>
#include <string.h>
#include "debounce.h"
#include "keyer.h"
#include "pins.h"
#include "player.h"

namespace {
struct PlayRequest {
  char text[24];
  uint8_t wpm;
  uint16_t hz;
  uint16_t beepMs;  // 0 以外ならビープ
};

queue_t eventQ;
queue_t playQ;
volatile bool ready = false;

// core0 → core1 の設定（1語ずつなので volatile で十分）
volatile uint8_t cfgWpm = 20;
volatile uint8_t cfgMode = (uint8_t)KeyerMode::B;
volatile uint16_t cfgTone = 3000;
volatile bool cfgSidetone = true;
volatile uint32_t cfgSeq = 0;
// 再生要求の数（core0 が増やす）と、終わった数（core1 が増やす）。差があれば再生中
volatile uint32_t playRequested = 0;
volatile uint32_t playDone = 0;
volatile bool keyerIdle = true;

// 以下は core1 だけが触る
IambicKeyer keyer;
Debouncer ditIn(5), dahIn(5);
Player player;
uint16_t playHz = 700;
bool keyLedOn = false;  // サイドトーン OFF のとき、打鍵中につまみの青 LED を点ける

// 打鍵の表示 LED を、変化したときだけ切り替える（core0 の「正解」点灯を毎回消さないため）
void keyLedSet(bool on) {
  if (on == keyLedOn) return;
  keyLedOn = on;
  digitalWrite(PIN_KNOB_BLUE, on ? HIGH : LOW);
}
bool buzzerOn = false;
uint16_t buzzerHz = 0;
uint32_t appliedSeq = 0;

// ブザーの ON/OFF と周波数を、変化があったときだけ切り替える
void buzzerSet(bool on, uint16_t hz) {
  if (on && (!buzzerOn || hz != buzzerHz)) {
    tone(PIN_BUZZER, hz);
    buzzerHz = hz;
  } else if (!on && buzzerOn) {
    noTone(PIN_BUZZER);
  }
  buzzerOn = on;
}

// イベントを core0 へ送る（満杯なら捨てる）
void pushEvent(bool started, char symbol, uint32_t dur, uint32_t at) {
  EngineEvent e{started, symbol, dur, at};
  queue_try_add(&eventQ, &e);
}
}  // namespace

// キューを用意して core1 の開始を許可する
void engineBegin(const Config& cfg) {
  queue_init(&eventQ, sizeof(EngineEvent), 32);
  queue_init(&playQ, sizeof(PlayRequest), 4);
  engineApply(cfg);
  ready = true;
}

// 設定を共有変数に書き、番号を進める
void engineApply(const Config& cfg) {
  cfgWpm = cfg.wpm;
  cfgMode = (uint8_t)cfg.mode;
  cfgTone = cfg.toneHz;
  cfgSidetone = cfg.sidetone;
  cfgSeq = cfgSeq + 1;
}

// 再生要求を送る
void enginePlay(const char* text, uint8_t wpm) {
  PlayRequest r{};
  strncpy(r.text, text, sizeof(r.text) - 1);
  r.wpm = wpm;
  r.hz = cfgTone;
  if (queue_try_add(&playQ, &r)) playRequested = playRequested + 1;
}

// ビープ要求を送る
void engineBeep(uint16_t hz, uint16_t ms) {
  PlayRequest r{};
  r.hz = hz;
  r.beepMs = ms;
  if (queue_try_add(&playQ, &r)) playRequested = playRequested + 1;
}

bool enginePlayerBusy() { return playRequested != playDone; }

bool engineIdle() { return keyerIdle && playRequested == playDone; }

bool engineNextEvent(EngineEvent& e) { return queue_try_remove(&eventQ, &e); }

// ---- core1 ----

// core1 の初期化（core0 の準備を待つ）
void setup1() {
  while (!ready) tight_loop_contents();
  pinMode(PIN_DIT, INPUT_PULLUP);
  pinMode(PIN_DAH, INPUT_PULLUP);
  pinMode(PIN_BUZZER, OUTPUT);
#ifdef CW_HEARTBEAT
  pinMode(PIN_LED_B, OUTPUT);
  digitalWrite(PIN_LED_B, HIGH);
  // 診断用：起動音 1回目＝tone()、2回目＝ピンを直接 ON/OFF（約 1kHz）
  tone(PIN_BUZZER, 1000);
  delay(300);
  noTone(PIN_BUZZER);
  delay(500);
  for (int i = 0; i < 300; ++i) {
    digitalWrite(PIN_BUZZER, HIGH);
    delayMicroseconds(500);
    digitalWrite(PIN_BUZZER, LOW);
    delayMicroseconds(500);
  }
#endif
}

// core1 のループ：再生中は再生、それ以外はキーヤー
void loop1() {
  uint32_t now = millis();
#ifdef CW_HEARTBEAT
  static uint32_t hb = 0;  // 診断用：core1 が回っていれば青が点滅
  if (now - hb >= 500) { hb = now; digitalWrite(PIN_LED_B, !digitalRead(PIN_LED_B)); }
#endif

  if (appliedSeq != cfgSeq) {
    appliedSeq = cfgSeq;
    keyer.setWpm(cfgWpm);
    keyer.setMode((KeyerMode)cfgMode);
  }

  PlayRequest r;
  if (!player.busy() && queue_try_remove(&playQ, &r)) {
    playHz = r.hz;
    if (r.beepMs) player.beep(r.beepMs, now);
    else player.start(r.text, r.wpm, now);
    if (!player.busy()) playDone = playDone + 1;  // 空文字などで即終了
  }

  if (player.busy()) {
    bool on = player.update(now);
    buzzerSet(on, playHz);
    // 再生中のパドルは無視。ただし打鍵途中の要素の終わりは core0 に伝える（HID の押しっぱなし防止）
    KeyerEvent ev = keyer.update(now, false, false);
    if (ev.ended) pushEvent(false, ev.symbol, ev.durationMs, now);
    keyerIdle = keyer.idle();
    keyLedSet(false);
    if (!player.busy()) playDone = playDone + 1;
    return;
  }

  bool dit = ditIn.update(now, digitalRead(PIN_DIT) == LOW);
  bool dah = dahIn.update(now, digitalRead(PIN_DAH) == LOW);
#ifdef CW_HEARTBEAT
  digitalWrite(PIN_LED_R, (dit || dah) ? LOW : HIGH);  // 診断用：パドルを押している間は赤
#endif
  KeyerEvent ev = keyer.update(now, dit, dah);
  if (ev.ended) pushEvent(false, ev.symbol, ev.durationMs, now);
  if (ev.started) pushEvent(true, ev.symbol, 0, now);
  buzzerSet(keyer.keyDown() && cfgSidetone, cfgTone);
  keyLedSet(keyer.keyDown() && !cfgSidetone);
  keyerIdle = keyer.idle() && !dit && !dah;
}
