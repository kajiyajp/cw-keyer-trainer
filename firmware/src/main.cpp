// 作成：2026-11-21
// 目的：core0 のメイン処理（USB・解読・シリアルコマンド・オフライン画面）。打鍵は core1（engine.cpp）
#include <Arduino.h>
#include "decoder.h"
#include "engine.h"
#include "hw_usb.h"
#include "protocol.h"
#include "settings.h"
#include "ui.h"

namespace {
Config config;
Decoder decoder;

// 設定をエンジンと解読器に反映する
void applyConfig() {
  engineApply(config);
  decoder.setDitMs(1200 / config.wpm);
}

// 打鍵イベントを HID・解読器・シリアルへ流す
void handleEngineEvents() {
  EngineEvent e;
  char line[24];
  while (engineNextEvent(e)) {
    uiNoteActivity(e.atMs);
    if (e.started) {
      usbKey(true);
      decoder.onKeyDown();
    } else {
      usbKey(false);
      decoder.onElement(e.symbol, e.atMs);
      formatElement(e.symbol, e.durationMs, line, sizeof line);
      usbPrintLine(line);
    }
  }
}

// シリアルコマンドを処理する
void handleCommands() {
  char cmd[64], line[96];
  if (!usbReadLine(cmd, sizeof cmd)) return;
  switch (handleLine(cmd, config)) {
    case CmdResult::Ok: applyConfig(); usbPrintLine("OK"); break;
    case CmdResult::GetConfig: formatConfig(config, line, sizeof line); usbPrintLine(line); break;
    case CmdResult::Save: settingsRequestSave(config); usbPrintLine("OK"); break;
    case CmdResult::Err:
      usbPrintLine("ERR");
#ifdef CW_HEARTBEAT
      // 診断用：ERR になった行を16進で出す
      for (const char* q = cmd; *q; ++q) Serial.printf("%02X ", (uint8_t)*q);
      Serial.println();
#endif
      break;
  }
}
}  // namespace

// 診断用：LED を 500ms ごとに反転する（LED は LOW で点灯）
#ifdef CW_HEARTBEAT
void heartbeat(uint8_t pin, uint32_t& last, uint32_t now) {
  if (now - last >= 500) { last = now; digitalWrite(pin, !digitalRead(pin)); }
}
#endif

void setup() {
#ifdef CW_HEARTBEAT
  pinMode(PIN_LED_R, OUTPUT);
  pinMode(PIN_LED_G, OUTPUT);
  digitalWrite(PIN_LED_G, HIGH);
  digitalWrite(PIN_LED_R, LOW);  // setup 中は赤
#endif
  usbBegin();
  settingsLoad(config);
  engineBegin(config);
  applyConfig();
  uiBegin(&config, applyConfig);
#ifdef CW_HEARTBEAT
  digitalWrite(PIN_LED_R, HIGH);
#endif
}

void loop() {
  uint32_t now = millis();
#ifdef CW_HEARTBEAT
  static uint32_t hb = 0;
  heartbeat(PIN_LED_G, hb, now);
#endif
  usbService();
  handleEngineEvents();
  char c = decoder.poll(now);
  if (c) {
    char line[8];
    formatChar(c, line, sizeof line);
    usbPrintLine(line);
    uiOnChar(c);
  }
  handleCommands();
  settingsService();
  usbService();  // 描画で止まる前に HID の送り残しを出す
  uiUpdate(now);
}
