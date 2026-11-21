// 作成：2026-11-21
// 目的：オフラインのエコー練習（出題を作り、打ち返した文字を採点する）
#pragma once
#include <stdint.h>

enum class PromptKind : uint8_t { Koch, Callsign, Abbrev };

class EchoTrainer {
 public:
  explicit EchoTrainer(uint32_t seed) : rng_(seed ? seed : 1) {}
  // 出題文字列（大文字）を作り、回答をリセットする。kochLen は Koch の文字数（1〜5 に収める）
  const char* nextPrompt(PromptKind k, uint8_t kochLevel, uint8_t kochLen = 5);
  // 出題はそのままで回答だけ消す（もう一度聞くとき）
  void resetAnswer() { ansLen_ = 0; answer_[0] = '\0'; }
  // 解読した文字を1つずつ渡す（' ' は無視）
  void onChar(char c);
  // 出題と同じ文字数がそろったか
  bool answerComplete() const { return ansLen_ >= promptLen_; }
  // 回答が出題と一致したか
  bool isCorrect() const;
  // 現在の出題
  const char* prompt() const { return prompt_; }

 private:
  // xorshift32 乱数（native と実機で同じ結果にするため自前）
  uint32_t next();
  // 0〜n-1 の乱数
  uint32_t below(uint32_t n) { return next() % n; }
  // 出題文字列の末尾に1文字足す
  void push(char c);

  static constexpr int MAX = 8;
  uint32_t rng_;
  char prompt_[MAX + 1] = {0};
  char answer_[MAX + 1] = {0};
  uint8_t promptLen_ = 0;
  uint8_t ansLen_ = 0;
};
