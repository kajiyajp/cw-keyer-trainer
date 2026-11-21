// 作成：2026-11-21
// 目的：−／＋ボタンの値計算のテスト（端で止まり、折り返さない）
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { stepValue } from '../js/stepper.js';

test('上限・下限で止まる', () => {
  assert.equal(stepValue(1200, 50, 400, 1200), 1200);
  assert.equal(stepValue(400, -50, 400, 1200), 400);
});
test('範囲内なら刻みだけ動く', () => {
  assert.equal(stepValue(700, 50, 400, 1200), 750);
  assert.equal(stepValue(20, -1, 5, 40), 19);
});
