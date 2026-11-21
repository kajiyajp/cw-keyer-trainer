// 作成：2026-11-21
// 目的：打鍵（押した／離した時間の列）を文字にし、リズムを集計する。HID のキー押下から時間の列を作る
import { decode } from './morse.js';
import { farnsworthGaps } from './timing.js';

// 平均（空なら null）
function avg(xs) {
  return xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null;
}

// marks: [{on, ms}] を解読する。しきい値はファームと同じ（字間 2 短点・語間 5 短点）
export function decodeMarks(marks, wpm) {
  const dit = 1200 / wpm;
  const elements = [];
  const dots = [], dashes = [], elemGaps = [], charGaps = [];
  let text = '';
  let cur = '';
  // 組み立て中の符号を文字にする
  const flush = () => {
    if (cur) { text += decode(cur); cur = ''; }
  };
  for (const { on, ms } of marks) {
    if (on) {
      if (ms > 10 * dit) continue;  // 押しっぱなし（keyup の取りこぼし）は捨てる
      const symbol = ms < 2 * dit ? '.' : '-';
      cur += symbol;
      elements.push({ symbol, ms });
      (symbol === '.' ? dots : dashes).push(ms);
    } else if (ms < 2 * dit) {
      elemGaps.push(ms);
    } else {
      flush();
      if (ms >= 5 * dit) {
        if (text && !text.endsWith(' ')) text += ' ';
      } else {
        charGaps.push(ms);
      }
    }
  }
  flush();
  const dotAvg = avg(dots), dashAvg = avg(dashes);
  return {
    text: text.trimEnd(),
    elements,
    stats: {
      dotAvg, dashAvg,
      ratio: dotAvg && dashAvg ? dashAvg / dotAvg : null,
      elemGapAvg: avg(elemGaps), charGapAvg: avg(charGaps),
    },
  };
}

// キーの押下・解放の時刻から marks を作る
export class HidRecorder {
  constructor(now = () => performance.now()) {
    this.now = now;
    this.reset();
  }

  // 記録を消す
  reset() {
    this.list = [];
    this.isDown = false;
    this.lastT = null;
  }

  // 押した（押下中の連続は無視）
  down() {
    if (this.isDown) return;
    const t = this.now();
    if (this.lastT !== null) this.list.push({ on: false, ms: t - this.lastT });
    this.lastT = t;
    this.isDown = true;
  }

  // 離した
  up() {
    if (!this.isDown) return;
    const t = this.now();
    this.list.push({ on: true, ms: t - this.lastT });
    this.lastT = t;
    this.isDown = false;
  }

  // keyup を取りこぼしたとき（タブが裏に回るなど）に押下中の状態を捨てる。押下は解読で捨てられる長さにする
  cancel() {
    if (!this.isDown) return;
    this.list.push({ on: true, ms: Infinity });
    this.lastT = this.now();
    this.isDown = false;
  }

  // 記録の写しを返す
  marks() {
    return this.list.slice();
  }
}

// 何も打たなくなってから締めるまでの時間 ms（1.5 秒か、ファーンズワースの語間の長いほう）
export function finishDelayMs(charWpm, effWpm) {
  return Math.max(1500, farnsworthGaps(charWpm, effWpm).wordGapMs);
}

// 要素の長さが理想に近いか（±25% か ±20ms の広いほう。iPhone の揺れ ±10〜20ms を考慮）
export function withinTolerance(ms, ideal) {
  return Math.abs(ms - ideal) <= Math.max(0.25 * ideal, 20);
}
