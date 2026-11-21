// 作成：2026-11-21
// 目的：iambic キーヤー（Mode A / B、短点・長点メモリ）。時刻は引数で受け取りハードに依存しない
#pragma once
#include <stdint.h>

enum class KeyerMode : uint8_t { A, B };

// update() の結果。started：要素が始まった／ended：要素が終わった（symbol と durationMs は終わった要素のもの）
struct KeyerEvent {
  bool started = false;
  bool ended = false;
  char symbol = 0;
  uint32_t durationMs = 0;
};

class IambicKeyer {
 public:
  // 速度を設定する（5〜40 に丸める）。次の要素から反映
  void setWpm(uint8_t wpm);
  // Mode A / B を設定する
  void setMode(KeyerMode m) { mode_ = m; }
  // 毎ループ呼び、パドル状態から要素を進める
  KeyerEvent update(uint32_t nowMs, bool dit, bool dah);
  // 今トーンを鳴らすべきか
  bool keyDown() const { return state_ == State::Sending; }
  // 送信も要素間スペースも終わって待機中か
  bool idle() const { return state_ == State::Idle; }
  // 短点の長さ ms（1200 / wpm）
  uint16_t ditMs() const { return 1200 / wpm_; }

 private:
  enum class State : uint8_t { Idle, Sending, Space };

  // 次に送る要素を決める（なければ 0）
  char nextSymbol(bool dit, bool dah);
  // 要素の送信を始める
  void start(char symbol, uint32_t nowMs);
  // 送信中・間隔中の反対側パドルをメモリに記録する
  void remember(bool dit, bool dah);

  uint8_t wpm_ = 20;
  KeyerMode mode_ = KeyerMode::B;
  State state_ = State::Idle;
  char current_ = 0;        // 送信中（または直前）の要素
  char last_ = 0;           // 最後に送った要素
  uint32_t toneEnd_ = 0;    // トーン終了時刻
  uint32_t spaceEnd_ = 0;   // 要素間スペース終了時刻
  uint16_t elemLen_ = 0;    // 送信中要素の長さ
  bool memDit_ = false;
  bool memDah_ = false;
  bool prevDit_ = false;
  bool prevDah_ = false;
};
