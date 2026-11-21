// 作成：2026-11-21
// 目的：iambic キーヤーの状態機械（Idle → Sending → Space → 次の要素）
#include "keyer.h"

namespace {
// 時刻 a が b 以降か（millis のあふれに強い比較）
inline bool reached(uint32_t now, uint32_t t) { return (int32_t)(now - t) >= 0; }
}  // namespace

// 速度を 5〜40 WPM に丸めて保存する
void IambicKeyer::setWpm(uint8_t wpm) {
  if (wpm < 5) wpm = 5;
  if (wpm > 40) wpm = 40;
  wpm_ = wpm;
}

// 反対側パドルの押下をメモリに残す
// Mode A：押し始め（立ち上がり）だけ記録／Mode B：押されていれば記録
void IambicKeyer::remember(bool dit, bool dah) {
  bool ditTrigger = (mode_ == KeyerMode::B) ? dit : (dit && !prevDit_);
  bool dahTrigger = (mode_ == KeyerMode::B) ? dah : (dah && !prevDah_);
  if (current_ == '-' && ditTrigger) memDit_ = true;
  if (current_ == '.' && dahTrigger) memDah_ = true;
}

// メモリ → 両押しなら交互 → 押されている側、の順で次の要素を決める
char IambicKeyer::nextSymbol(bool dit, bool dah) {
  char s = 0;
  if (memDit_ || memDah_) {
    s = memDit_ ? '.' : '-';
    if (memDit_ && memDah_) s = (last_ == '.') ? '-' : '.';
  } else if (dit && dah) {
    s = (last_ == '.') ? '-' : '.';
  } else if (dit) {
    s = '.';
  } else if (dah) {
    s = '-';
  }
  memDit_ = memDah_ = false;
  return s;
}

// 要素の長さを今の速度で確定し、送信を始める
void IambicKeyer::start(char symbol, uint32_t nowMs) {
  uint16_t dit = ditMs();
  elemLen_ = (symbol == '.') ? dit : dit * 3;
  current_ = symbol;
  last_ = symbol;
  toneEnd_ = nowMs + elemLen_;
  spaceEnd_ = toneEnd_ + dit;
  state_ = State::Sending;
}

// 毎ループの処理
KeyerEvent IambicKeyer::update(uint32_t nowMs, bool dit, bool dah) {
  KeyerEvent ev;

  if (state_ == State::Sending && reached(nowMs, toneEnd_)) {
    ev.ended = true;
    ev.symbol = current_;
    ev.durationMs = elemLen_;
    state_ = State::Space;
  }
  if (state_ == State::Space && reached(nowMs, spaceEnd_)) {
    state_ = State::Idle;
  }

  if (state_ == State::Idle && !ev.ended) {
    // 要素間スペースが明けたら次の要素を決める（同じ呼び出しで終了した場合は次回に回す）
    char s = nextSymbol(dit, dah);
    if (s) {
      start(s, nowMs);
      ev.started = true;
      if (!ev.ended) ev.symbol = s;
    }
  }

  if (state_ != State::Idle) remember(dit, dah);

  prevDit_ = dit;
  prevDah_ = dah;
  return ev;
}
