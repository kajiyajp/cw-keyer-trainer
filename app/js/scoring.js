// 作成：2026-11-21
// 目的：正答率の計算と Koch レベルの進級判定
import { KOCH_ORDER } from './morse.js';

// 空白を除いて大文字にする
function norm(s) {
  return s.replace(/\s+/g, '').toUpperCase();
}

// 編集距離（レーベンシュタイン距離）
function editDistance(a, b) {
  let prev = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i++) {
    const cur = [i];
    for (let j = 1; j <= b.length; j++) {
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    }
    prev = cur;
  }
  return prev[b.length];
}

// 正答率 0〜1（空白は無視）
export function accuracy(expected, got) {
  const e = norm(expected);
  if (!e.length) return 1;
  return Math.max(0, 1 - editDistance(e, norm(got)) / e.length);
}

// 正答率 90% 以上なら 1 文字増やす
export function nextKochLevel(level, acc) {
  return acc >= 0.9 ? Math.min(level + 1, KOCH_ORDER.length) : level;
}
