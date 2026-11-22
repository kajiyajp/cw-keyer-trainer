// 作成：2026-11-21
// 目的：オフライン画面の実装。MENU 短押し＝次／値変更、OK＝決定、MENU 長押し＝メニューへ戻る
#include "ui.h"
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Wire.h>
#include <string.h>
#include "debounce.h"
#include "engine.h"
#include "morse.h"
#include "pins.h"
#include "settings.h"
#include "trainer.h"

namespace {
enum class Screen : uint8_t { Menu, Echo, Free, Settings };
enum class EchoState : uint8_t { Playing, Answer, Result };

constexpr uint16_t LONG_PRESS_MS = 800;
constexpr uint16_t REDRAW_MS = 100;       // 描画の最短間隔（描画中は core0 が約 25ms 止まる）
constexpr uint16_t RESULT_WAIT_MS = 1200;
constexpr uint16_t OK_BEEP_HZ = 1600;  // トーン上限（1200Hz）より高くして打鍵音と区別する
constexpr uint16_t OK_BEEP_MS = 50;

Adafruit_SSD1306 oled(128, 64, &Wire, -1);
bool oledOk = false;
Config* cfg = nullptr;
void (*configChanged)() = nullptr;

Screen screen = Screen::Menu;
uint8_t menuIndex = 0;
const char* const MENU_ITEMS[] = {"Echo", "Free", "Settings"};
uint8_t settingIndex = 0;
const char* const SETTING_NAMES[] = {"WPM", "MODE", "TONE", "SIDETONE", "KOCH", "ECHO LEN", "HINT"};
constexpr uint8_t SETTING_COUNT = 7;

EchoTrainer trainer(1);
PromptKind kind = PromptKind::Koch;
EchoState echoState = EchoState::Playing;
uint32_t resultAt = 0;
uint16_t scoreOk = 0, scoreAll = 0;
char typed[12] = {0};

char freeText[64] = {0};  // 自由打鍵の表示（末尾に追加し、あふれたら前を捨てる）

Debouncer menuIn(20), okIn(20);
bool menuPrev = false, okPrev = false, longFired = false;
uint32_t menuDownAt = 0;
bool dirty = true;
uint32_t lastDraw = 0;
uint32_t lastActivity = 0;  // 最後の打鍵イベントの時刻

const char* kindName() {
  return kind == PromptKind::Koch ? "Koch" : kind == PromptKind::Callsign ? "Call" : "Abbr";
}

// 新しい問題を出して再生する
void newPrompt() {
  trainer.nextPrompt(kind, cfg->kochLevel, cfg->echoLen);
  typed[0] = '\0';
  enginePlay(trainer.prompt(), cfg->wpm);
  echoState = EchoState::Playing;
  dirty = true;
}

// 設定項目の値を1段階進める（上限で折り返す）
void bumpSetting() {
  switch (settingIndex) {
    case 0: cfg->wpm = cfg->wpm >= WPM_MAX ? WPM_MIN : cfg->wpm + 1; break;
    case 1:  // A → B → U → A
      cfg->mode = cfg->mode == KeyerMode::A ? KeyerMode::B
                : cfg->mode == KeyerMode::B ? KeyerMode::Ultimatic : KeyerMode::A;
      break;
    case 2: cfg->toneHz = cfg->toneHz + 50 > TONE_MAX ? TONE_MIN : cfg->toneHz + 50; break;
    case 3: cfg->sidetone = !cfg->sidetone; break;
    case 4: cfg->kochLevel = cfg->kochLevel >= KOCH_MAX ? KOCH_MIN : cfg->kochLevel + 1; break;
    case 5: cfg->echoLen = cfg->echoLen >= ECHOLEN_MAX ? ECHOLEN_MIN : cfg->echoLen + 1; break;
    case 6: cfg->hint = !cfg->hint; break;
  }
  configChanged();
}

// 設定項目の値を文字にする
void settingValue(uint8_t i, char* out, size_t n) {
  switch (i) {
    case 0: snprintf(out, n, "%u", cfg->wpm); break;
    case 1: snprintf(out, n, "%c", keyerModeChar(cfg->mode)); break;
    case 2: snprintf(out, n, "%u", cfg->toneHz); break;
    case 3: snprintf(out, n, "%s", cfg->sidetone ? "ON" : "OFF"); break;
    case 4: snprintf(out, n, "%u", cfg->kochLevel); break;
    case 5: snprintf(out, n, "%u", cfg->echoLen); break;
    default: snprintf(out, n, "%s", cfg->hint ? "ON" : "OFF"); break;
  }
}

// MENU 短押し
void onMenu() {
  switch (screen) {
    case Screen::Menu: menuIndex = (menuIndex + 1) % 3; break;
    case Screen::Echo:
      kind = kind == PromptKind::Koch ? PromptKind::Callsign
           : kind == PromptKind::Callsign ? PromptKind::Abbrev : PromptKind::Koch;
      newPrompt();
      break;
    case Screen::Free: break;
    case Screen::Settings: bumpSetting(); break;
  }
  dirty = true;
}

// OK 押し
void onOk() {
  switch (screen) {
    case Screen::Menu:
      if (menuIndex == 0) { screen = Screen::Echo; scoreOk = scoreAll = 0; newPrompt(); }
      else if (menuIndex == 1) { screen = Screen::Free; freeText[0] = '\0'; }
      else { screen = Screen::Settings; settingIndex = 0; }
      break;
    case Screen::Echo:  // 同じ問題をもう一度聞く
      typed[0] = '\0';
      trainer.resetAnswer();
      enginePlay(trainer.prompt(), cfg->wpm);
      echoState = EchoState::Playing;
      break;
    case Screen::Free: freeText[0] = '\0'; break;
    case Screen::Settings:
      if (++settingIndex >= SETTING_COUNT) {
        settingsRequestSave(*cfg);
        screen = Screen::Menu;
      }
      break;
  }
  dirty = true;
}

// ボタンを読み、短押し・長押しを判定する
void readButtons(uint32_t now) {
  bool menu = menuIn.update(now, digitalRead(PIN_BTN_MENU) == LOW);
  bool ok = okIn.update(now, digitalRead(PIN_BTN_OK) == LOW);
  if (menu && !menuPrev) { menuDownAt = now; longFired = false; }
  if (menu && !longFired && now - menuDownAt >= LONG_PRESS_MS) {
    longFired = true;
    if (screen == Screen::Settings) settingsRequestSave(*cfg);  // 変更済みの値を残さず保存する
    screen = Screen::Menu;
    dirty = true;
  }
  // エコー練習で再生中のボタンは無視（再生が重なるのを防ぐ）
  bool blocked = screen == Screen::Echo && enginePlayerBusy();
  if (!menu && menuPrev && !longFired && !blocked) onMenu();
  if (ok && !okPrev && !blocked) onOk();
  menuPrev = menu;
  okPrev = ok;
}

// エコー練習の進行
void updateEcho(uint32_t now) {
  if (echoState == EchoState::Playing && !enginePlayerBusy()) {
    echoState = EchoState::Answer;
    dirty = true;
  } else if (echoState == EchoState::Result && !enginePlayerBusy() && now - resultAt >= RESULT_WAIT_MS) {
    newPrompt();
  }
}

// 画面を描く
void draw() {
  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextSize(1);
  oled.setCursor(0, 0);
  char v[12];
  switch (screen) {
    case Screen::Menu:
      oled.printf("CW Trainer %uWPM\n\n", cfg->wpm);
      for (uint8_t i = 0; i < 3; ++i) oled.printf("%c %s\n", i == menuIndex ? '>' : ' ', MENU_ITEMS[i]);
      break;
    case Screen::Echo:
      oled.printf("Echo %s %u/%u\n", kindName(), scoreOk, scoreAll);
      if (cfg->hint) {  // ヒント：符号の並び → 出題の文字 → 自分の答え
        char pat[48];
        morsePattern(trainer.prompt(), pat, sizeof pat);
        oled.setCursor(0, 10);
        oled.print(pat);
        oled.setTextSize(2);
        oled.setCursor(0, 30);
        oled.print(trainer.prompt());
        oled.setCursor(0, 48);
        if (echoState == EchoState::Playing) oled.print("listen");
        else if (echoState == EchoState::Answer) oled.print(typed[0] ? typed : "_");
        else oled.print(trainer.isCorrect() ? "OK" : typed);
        break;
      }
      oled.setTextSize(2);
      oled.setCursor(0, 20);
      if (echoState == EchoState::Playing) oled.print("listen");
      else if (echoState == EchoState::Answer) oled.print(typed[0] ? typed : "_");
      else {
        oled.print(trainer.prompt());
        oled.setCursor(0, 42);
        oled.print(trainer.isCorrect() ? "OK" : typed);
      }
      break;
    case Screen::Free:
      oled.println("Free  (OK:clear)");
      oled.setTextSize(1);
      oled.print(freeText);
      break;
    case Screen::Settings:
      oled.println("Settings (OK:next)");
      for (uint8_t i = 0; i < SETTING_COUNT; ++i) {
        settingValue(i, v, sizeof v);
        oled.printf("%c %-8s %s\n", i == settingIndex ? '>' : ' ', SETTING_NAMES[i], v);
      }
      break;
  }
  oled.display();
}
}  // namespace

void uiBegin(Config* c, void (*onConfigChanged)()) {
  cfg = c;
  configChanged = onConfigChanged;
  trainer = EchoTrainer(micros() | 1);
  pinMode(PIN_BTN_MENU, INPUT_PULLUP);
  pinMode(PIN_BTN_OK, INPUT_PULLUP);
  Wire.setSDA(PIN_SDA);
  Wire.setSCL(PIN_SCL);
  Wire.begin();
  // OLED が無くても（初期化に失敗しても）キーヤーは動かし続ける
  oledOk = oled.begin(SSD1306_SWITCHCAPVCC, 0x3C);
}

void uiOnChar(char c) {
  if (screen == Screen::Free) {
    size_t len = strlen(freeText);
    if (len >= sizeof(freeText) - 1) {
      memmove(freeText, freeText + 21, len - 21 + 1);  // 1行（21文字）分捨てる
      len = strlen(freeText);
    }
    freeText[len] = c;
    freeText[len + 1] = '\0';
    dirty = true;
  } else if (screen == Screen::Echo && echoState == EchoState::Answer && c != ' ') {
    trainer.onChar(c);
    size_t len = strlen(typed);
    if (len < sizeof(typed) - 1) { typed[len] = c; typed[len + 1] = '\0'; }
    if (trainer.answerComplete()) {
      ++scoreAll;
      if (trainer.isCorrect()) { ++scoreOk; engineBeep(OK_BEEP_HZ, OK_BEEP_MS); }
      else enginePlay(trainer.prompt(), cfg->wpm);  // 不正解：正解を聞かせる
      echoState = EchoState::Result;
      resultAt = millis();
    }
    dirty = true;
  }
}

void uiNoteActivity(uint32_t nowMs) { lastActivity = nowMs; }

void uiUpdate(uint32_t now) {
  readButtons(now);
  if (screen == Screen::Echo) updateEcho(now);
  // 打鍵中（最後のイベントから語間＝短点7個分以内）は描画しない。描画中は HID が約 25ms 止まるため
  bool quiet = now - lastActivity >= 7u * (1200u / cfg->wpm);
  if (oledOk && dirty && quiet && now - lastDraw >= REDRAW_MS) {
    dirty = false;
    lastDraw = now;
    draw();
  }
}
