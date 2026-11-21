// 作成：2026-11-21
// 目的：送信練習の判定まわり（締めるまでの時間・グラフの許容幅）のテスト
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { finishDelayMs, withinTolerance } from '../js/decoder.js';

test('締めるまでの時間は 1.5 秒以上、ファーンズワースの語間が長ければそちら', () => {
  assert.equal(finishDelayMs(20, 20), 1500);
  assert.equal(finishDelayMs(5, 5), 1680);
  assert.ok(finishDelayMs(20, 5) > 3000);
});
test('グラフの許容幅は ±25% か ±20ms の広いほう（iPhone の揺れを考慮）', () => {
  assert.equal(withinTolerance(78, 60), true);   // +18ms：25% では外れるが 20ms 以内
  assert.equal(withinTolerance(85, 60), false);
  assert.equal(withinTolerance(220, 180), true);  // +40ms は 25%（45ms）以内
  assert.equal(withinTolerance(230, 180), false); // +50ms は外れ
});
