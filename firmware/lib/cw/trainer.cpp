// 作成：2026-11-21
// 目的：エコー練習の実装
#include "trainer.h"
#include <string.h>
#include "morse.h"

namespace {
const char* const ABBREVS[] = {"CQ", "DE", "TU", "73", "RST", "UR", "5NN", "QTH", "OP"};
constexpr int ABBREV_COUNT = sizeof(ABBREVS) / sizeof(ABBREVS[0]);
const char* const FOREIGN_PREFIX[] = {"W", "K", "DL", "VK"};
}  // namespace

// xorshift32
uint32_t EchoTrainer::next() {
  rng_ ^= rng_ << 13;
  rng_ ^= rng_ >> 17;
  rng_ ^= rng_ << 5;
  return rng_;
}

// 1文字追加する
void EchoTrainer::push(char c) {
  if (promptLen_ < MAX) {
    prompt_[promptLen_++] = c;
    prompt_[promptLen_] = '\0';
  }
}

// 種類に応じて出題を作る
const char* EchoTrainer::nextPrompt(PromptKind k, uint8_t kochLevel, uint8_t kochLen) {
  promptLen_ = 0;
  prompt_[0] = '\0';
  ansLen_ = 0;
  answer_[0] = '\0';

  if (k == PromptKind::Koch) {
    uint8_t n = (uint8_t)strlen(KOCH_ORDER);
    if (kochLevel < 2) kochLevel = 2;
    if (kochLevel > n) kochLevel = n;
    if (kochLen < 1) kochLen = 1;
    if (kochLen > 5) kochLen = 5;
    for (int i = 0; i < kochLen; ++i) push(KOCH_ORDER[below(kochLevel)]);
  } else if (k == PromptKind::Callsign) {
    // 4回に3回は国内（J[AHR]数字+英字2〜3）、残りは海外
    if (below(4) != 0) {
      push('J');
      push("AHR"[below(3)]);
    } else {
      for (const char* p = FOREIGN_PREFIX[below(4)]; *p; ++p) push(*p);
    }
    push((char)('0' + below(10)));
    int suffix = 2 + (int)below(2);
    if (promptLen_ + suffix > 6) suffix = 6 - promptLen_;
    for (int i = 0; i < suffix; ++i) push((char)('A' + below(26)));
  } else {
    for (const char* p = ABBREVS[below(ABBREV_COUNT)]; *p; ++p) push(*p);
  }
  return prompt_;
}

// 回答に1文字追加する
void EchoTrainer::onChar(char c) {
  if (c == ' ' || c == 0) return;
  if (ansLen_ < promptLen_) {
    answer_[ansLen_++] = c;
    answer_[ansLen_] = '\0';
  }
}

// 出題と回答を比べる
bool EchoTrainer::isCorrect() const {
  return answerComplete() && strcmp(prompt_, answer_) == 0;
}
