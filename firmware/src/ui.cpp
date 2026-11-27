// 作成：2026-11-21
// 目的：オフライン画面の実装。つまみ1つで操作：回す＝選ぶ／値を変える、押す＝決定、長押し＝メニューへ戻る
//       つまみの LED：エコー練習の正解＝青・不正解＝赤を短く点灯、設定画面の間＝赤
#include "ui.h"
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Wire.h>
#include <string.h>
#include "debounce.h"
#include "encoder.h"
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
constexpr uint16_t OK_BEEP_HZ = 1600;  // 打鍵音（初期値 3000Hz）と違う高さにして区別する
constexpr uint16_t OK_BEEP_MS = 50;
constexpr uint16_t LED_FLASH_MS = 300;  // 正解・不正解の LED を点ける長さ

Adafruit_SSD1306 oled(128, 64, &Wire, -1);
bool oledOk = false;
Config* cfg = nullptr;
void (*configChanged)() = nullptr;

Screen screen = Screen::Menu;
uint8_t menuIndex = 0;
const char* const MENU_ITEMS[] = {"Echo", "Free", "Settings"};
uint8_t settingIndex = 0;
// ConfigItem の並びと同じ順
const char* const SETTING_NAMES[] = {"WPM", "MODE", "TONE", "SIDETONE", "KOCH", "ECHO LEN", "HINT"};
constexpr uint8_t SETTING_COUNT = (uint8_t)ConfigItem::Count;

EchoTrainer trainer(1);
PromptKind kind = PromptKind::Koch;
EchoState echoState = EchoState::Playing;
uint32_t resultAt = 0;
uint16_t scoreOk = 0, scoreAll = 0;
char typed[12] = {0};

// 自由打鍵の表示：エコー練習と同じ文字サイズ 2（12×16 ドット）で 1 行 10 文字 × 3 行。
// 末尾に追加し、画面がいっぱいになったら 1 行（10 文字）分を前から捨てて上へ送る
constexpr uint8_t FREE_COLS = 10, FREE_ROWS = 3;
char freeText[FREE_COLS * FREE_ROWS + 1] = {0};

Debouncer swIn(20);
bool swPrev = false, longFired = false;
uint32_t swDownAt = 0;
QuadratureDecoder knob;
volatile int16_t knobSteps = 0;  // 割り込みで数えたクリック数（右回り＝＋）
uint32_t flashUntil = 0;         // 正解・不正解の LED を消す時刻
uint8_t flashPin = 0;            // 点けている LED（0＝なし）
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

// 選んでいる設定項目の値を dir の向きに1段階動かす（端で折り返す）
void stepSetting(int8_t dir) {
  configStep(*cfg, (ConfigItem)settingIndex, dir);
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

// つまみを回した（dir＝+1 右回り／-1 左回り）
void onTurn(int8_t dir) {
  switch (screen) {
    case Screen::Menu: menuIndex = (menuIndex + 3 + dir) % 3; break;
    case Screen::Echo:  // 出題の種類を切り替える
      if (dir > 0) kind = kind == PromptKind::Koch ? PromptKind::Callsign
                        : kind == PromptKind::Callsign ? PromptKind::Abbrev : PromptKind::Koch;
      else kind = kind == PromptKind::Koch ? PromptKind::Abbrev
                : kind == PromptKind::Abbrev ? PromptKind::Callsign : PromptKind::Koch;
      newPrompt();
      break;
    case Screen::Free: break;
    case Screen::Settings: stepSetting(dir); break;
  }
  dirty = true;
}

// つまみを押した（短押し）
void onPush() {
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

// つまみの A/B が変わるたびに呼ばれる（割り込み）
void onKnobEdge() {
  knobSteps += knob.update(digitalRead(PIN_KNOB_A) == LOW, digitalRead(PIN_KNOB_B) == LOW);
}

// 割り込みで数えたクリック数を取り出す
int16_t takeKnobSteps() {
  noInterrupts();
  int16_t n = knobSteps;
  knobSteps = 0;
  interrupts();
  return n;
}

// つまみを読み、回転・短押し・長押しを判定する
void readKnob(uint32_t now) {
  bool sw = swIn.update(now, digitalRead(PIN_KNOB_SW) == LOW);
  int16_t steps = takeKnobSteps();
  if (sw && !swPrev) { swDownAt = now; longFired = false; }
  if (sw && !longFired && now - swDownAt >= LONG_PRESS_MS) {
    longFired = true;
    if (screen == Screen::Settings) settingsRequestSave(*cfg);  // 変更済みの値を残さず保存する
    screen = Screen::Menu;
    dirty = true;
  }
  // エコー練習で再生中の操作は無視（再生が重なるのを防ぐ）
  bool blocked = screen == Screen::Echo && enginePlayerBusy();
  // 短押しは離したときに判定する（長押しと区別するため）
  if (!sw && swPrev && !longFired && !blocked) onPush();
  swPrev = sw;
  if (steps == 0 || blocked) return;
  int8_t dir = steps > 0 ? 1 : -1;
  if (screen == Screen::Echo) { onTurn(dir); return; }  // 種類の切り替えは1回だけ（毎回出題し直すため）
  for (int16_t i = steps > 0 ? steps : -steps; i > 0; --i) onTurn(dir);
}

// LED を短く点ける（正解＝青、不正解＝赤）
void flashLed(uint8_t pin, uint32_t now) {
  if (flashPin && flashPin != pin) digitalWrite(flashPin, LOW);
  flashPin = pin;
  flashUntil = now + LED_FLASH_MS;
  digitalWrite(pin, HIGH);
}

// LED を画面と時刻に合わせる（青は打鍵の表示で core1 も使う）
void updateLeds(uint32_t now) {
  if (flashPin && (int32_t)(now - flashUntil) >= 0) {
    digitalWrite(flashPin, LOW);
    flashPin = 0;
  }
  if (flashPin != PIN_KNOB_RED) digitalWrite(PIN_KNOB_RED, screen == Screen::Settings ? HIGH : LOW);
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
      oled.println("Free  (push:clear)");
      oled.setTextSize(2);
      for (uint8_t row = 0; row < FREE_ROWS; ++row) {   // 1 行ずつ書く（行の途中で折り返さない）
        size_t start = row * FREE_COLS;
        if (start >= strlen(freeText)) break;
        char line[FREE_COLS + 1];
        strncpy(line, freeText + start, FREE_COLS);
        line[FREE_COLS] = '\0';
        oled.setCursor(0, 12 + row * 17);
        oled.print(line);
      }
      break;
    case Screen::Settings:
      oled.println("Settings (push:next)");
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
  pinMode(PIN_KNOB_SW, INPUT_PULLUP);
  pinMode(PIN_KNOB_A, INPUT_PULLUP);
  pinMode(PIN_KNOB_B, INPUT_PULLUP);
  pinMode(PIN_KNOB_RED, OUTPUT);
  pinMode(PIN_KNOB_BLUE, OUTPUT);
  digitalWrite(PIN_KNOB_RED, LOW);
  digitalWrite(PIN_KNOB_BLUE, LOW);
  attachInterrupt(digitalPinToInterrupt(PIN_KNOB_A), onKnobEdge, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_KNOB_B), onKnobEdge, CHANGE);
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
      memmove(freeText, freeText + FREE_COLS, len - FREE_COLS + 1);  // 1 行（10 文字）分捨てて上へ送る
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
      resultAt = millis();
      if (trainer.isCorrect()) {
        ++scoreOk;
        engineBeep(OK_BEEP_HZ, OK_BEEP_MS);
        flashLed(PIN_KNOB_BLUE, resultAt);
      } else {
        enginePlay(trainer.prompt(), cfg->wpm);  // 不正解：正解を聞かせる
        flashLed(PIN_KNOB_RED, resultAt);
      }
      echoState = EchoState::Result;
    }
    dirty = true;
  }
}

void uiNoteActivity(uint32_t nowMs) { lastActivity = nowMs; }

void uiUpdate(uint32_t now) {
  readKnob(now);
  if (screen == Screen::Echo) updateEcho(now);
  updateLeds(now);
  // 打鍵中（最後のイベントから語間＝短点7個分以内）は描画しない。描画中は HID が約 25ms 止まるため
  // ただし設定画面は、打鍵しながらつまみで TONE などを変えて確かめるので、打鍵中も描く
  bool quiet = screen == Screen::Settings || now - lastActivity >= 7u * (1200u / cfg->wpm);
  if (oledOk && dirty && quiet && now - lastDraw >= REDRAW_MS) {
    dirty = false;
    lastDraw = now;
    draw();
  }
}
