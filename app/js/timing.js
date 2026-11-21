// 作成：2026-11-21
// 目的：WPM とファーンズワース（文字は速く・間は長く）から、音を鳴らす時刻表を作る
import { encode } from './morse.js';

// 短点の長さ ms
export function ditMs(wpm) {
  return 1200 / wpm;
}

// 字間・語間の長さ ms（ARRL の式。実効速度が文字速度以上なら標準の 3 / 7 短点）
export function farnsworthGaps(charWpm, effWpm) {
  const dit = ditMs(charWpm);
  if (effWpm >= charWpm) return { charGapMs: 3 * dit, wordGapMs: 7 * dit };
  const ta = (1000 * (60 * charWpm - 37.2 * effWpm)) / (effWpm * charWpm);
  return { charGapMs: (3 * ta) / 19, wordGapMs: (7 * ta) / 19 };
}

// 文字列を、音を鳴らす区間 {startMs, durMs} の列にする。空白は語間、未対応文字は飛ばす
export function schedule(text, charWpm, effWpm) {
  const dit = ditMs(charWpm);
  const { charGapMs, wordGapMs } = farnsworthGaps(charWpm, effWpm);
  const out = [];
  let t = 0;
  let pendingGap = 0;  // 次の音の前に空ける長さ
  for (const ch of text) {
    if (ch === ' ') {
      if (out.length) pendingGap = wordGapMs;
      continue;
    }
    const code = encode(ch);
    if (!code) continue;
    if (out.length) t += Math.max(pendingGap, charGapMs);
    pendingGap = 0;
    [...code].forEach((sym, i) => {
      if (i > 0) t += dit;
      const dur = sym === '-' ? 3 * dit : dit;
      out.push({ startMs: t, durMs: dur });
      t += dur;
    });
  }
  return out;
}
