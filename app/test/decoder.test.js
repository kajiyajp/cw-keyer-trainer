// 作成：2026-11-21
// 目的：打鍵の解読・リズム集計・HID 記録のテスト（20WPM：短点 60ms）
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { decodeMarks, HidRecorder } from '../js/decoder.js';

const m = (...xs) => xs.map(([on, ms]) => ({ on: !!on, ms }));
test('C と CQ', () => {
  assert.equal(decodeMarks(m([1,180],[0,60],[1,60],[0,60],[1,180],[0,60],[1,60]), 20).text, 'C');
  const cq = m([1,180],[0,60],[1,60],[0,60],[1,180],[0,60],[1,60],[0,180],
               [1,180],[0,60],[1,180],[0,60],[1,60],[0,60],[1,180]);
  assert.equal(decodeMarks(cq, 20).text, 'CQ');
});
test('語間', () => assert.equal(decodeMarks(m([1,60],[0,300],[1,60]), 20).text, 'E E'));
test('iPhone の揺れ（±20ms）でも正しく読む', () =>
  assert.equal(decodeMarks(m([1,200],[0,75],[1,45],[0,40],[1,160],[0,80],[1,75]), 20).text, 'C'));
test('押しっぱなし（短点 10 個分超）は捨てる', () =>
  assert.equal(decodeMarks(m([1,60],[0,180],[1,5000],[0,180],[1,60]), 20).text, 'EE'));
test('集計', () => {
  const s = decodeMarks(m([1,60],[0,60],[1,180],[0,180],[1,60]), 20).stats;
  assert.equal(s.dotAvg, 60); assert.equal(s.dashAvg, 180); assert.equal(s.ratio, 3);
  assert.equal(s.elemGapAvg, 60); assert.equal(s.charGapAvg, 180);
});
test('HidRecorder', () => {
  let t = 0; const r = new HidRecorder(() => t);
  r.down(); t = 60; r.up(); t = 120; r.down(); r.down(); t = 300; r.up();
  assert.deepEqual(r.marks(), [{ on: true, ms: 60 }, { on: false, ms: 60 }, { on: true, ms: 180 }]);
});

test('keyup を取りこぼしても、cancel 後の次の符号は失われない', () => {
  let t = 0; const r = new HidRecorder(() => t);
  // K（-.-）を打つ
  for (const [on, off] of [[180, 60], [60, 60], [180, 180]]) { r.down(); t += on; r.up(); t += off; }
  r.down();            // 押したままタブが裏に回り、keyup が来ない
  t += 3000; r.cancel();
  t += 500;
  for (const [on, off] of [[180, 60], [60, 60], [180, 0]]) { r.down(); t += on; r.up(); t += off; }
  assert.equal(decodeMarks(r.marks(), 20).text, 'K K');
});
