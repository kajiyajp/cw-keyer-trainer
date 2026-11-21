// 作成：2026-11-21
// 目的：速度計算と再生の時刻表のテスト
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ditMs, farnsworthGaps, schedule } from '../js/timing.js';

test('短点の長さ', () => assert.equal(ditMs(20), 60));
test('ファーンズワース：文字 20WPM・実効 10WPM', () => {
  const g = farnsworthGaps(20, 10);
  // ta = 1000*(60*20 - 37.2*10)/(10*20) = 4140ms、字間 = 3ta/19、語間 = 7ta/19
  assert.ok(Math.abs(g.charGapMs - 653.7) < 0.5);
  assert.ok(Math.abs(g.wordGapMs - 1525.3) < 0.5);
});
test('実効 ≥ 文字速度なら標準の間', () => {
  assert.deepEqual(farnsworthGaps(20, 20), { charGapMs: 180, wordGapMs: 420 });
});
test('時刻表：K と空白', () => {
  assert.deepEqual(schedule('K', 20, 20),
    [{ startMs: 0, durMs: 180 }, { startMs: 240, durMs: 60 }, { startMs: 360, durMs: 180 }]);
  const s = schedule('E E', 20, 20);
  assert.equal(s[1].startMs, 60 + 420);
  assert.deepEqual(schedule('#', 20, 20), []);
});
