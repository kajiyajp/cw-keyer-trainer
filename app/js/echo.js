// 作成：2026-11-21
// 目的：エコー練習の出題と判定（本体 firmware/lib/cw/trainer.cpp と同じ動き）
import { KOCH_ORDER, encode } from './morse.js';
import { callsign } from './generators.js';

// 略語の一覧（本体と同じ）
export const ABBREVS = ['CQ', 'DE', 'TU', '73', 'RST', 'UR', '5NN', 'QTH', 'OP'];

// 出題を作る。kind は 'koch' / 'call' / 'abbr'。Koch はレベルの文字から echoLen 文字（1〜5 に収める）
export function echoPrompt(kind, kochLevel, echoLen, rng) {
  if (kind === 'call') return callsign(rng);
  if (kind === 'abbr') return ABBREVS[Math.floor(rng() * ABBREVS.length)];
  const level = Math.min(Math.max(kochLevel, 2), KOCH_ORDER.length);
  const len = Math.min(Math.max(echoLen, 1), 5);
  let s = '';
  for (let i = 0; i < len; ++i) s += KOCH_ORDER[Math.floor(rng() * level)];
  return s;
}

// 文字列を "-.-. --.-" のような符号の並びにする（ヒント表示用）
export function patternOf(text) {
  return [...text].map((c) => encode(c) ?? '').filter(Boolean).join(' ');
}

// 回答に入った時刻 answerAt から字間（3 短点）以上たって届いた文字か。
// 機器は字間を待ってから C 行を送るので、それより早く届いた文字は出題の再生中に打たれたもの
export function lateEnough(now, answerAt, wpm) {
  return now - answerAt >= 3 * (1200 / wpm);
}

// 打ち返した文字を出題と比べる
export class EchoJudge {
  constructor(prompt) {
    this.prompt = prompt;
    this.answer = '';
  }

  // 解読した文字を1つ足す（空白は無視、出題の文字数で打ち切る）
  onChar(c) {
    if (!c || c === ' ' || this.complete) return;
    this.answer += c;
  }

  // 出題と同じ文字数がそろったか
  get complete() {
    return this.answer.length >= this.prompt.length;
  }

  // そろっていて、出題と一致したか
  get correct() {
    return this.complete && this.answer === this.prompt;
  }

  // 出題はそのままで回答だけ消す（もう一度聞くとき）
  reset() {
    this.answer = '';
  }
}
