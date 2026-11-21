// 作成：2026-11-21
// 目的：出題（Koch・コールサイン・QSO・筆記）のテスト
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { makeRng, kochText, callsign, qsoText, writtenQuestion } from '../js/generators.js';

test('同じ seed なら同じ出題', () => assert.equal(kochText(5, 3, makeRng(1)), kochText(5, 3, makeRng(1))));
test('Koch：使う文字とグループ', () => {
  const t = kochText(2, 4, makeRng(3));
  assert.match(t, /^[KM]{5}( [KM]{5}){3}$/);
  assert.match(kochText(1, 1, makeRng(3)), /^[KM]{5}$/);
});
test('コールサインの形', () => {
  const r = makeRng(9);
  for (let i = 0; i < 200; i++) {
    const c = callsign(r);
    assert.ok(c.length <= 6);
    assert.match(c, /^([A-Z]{1,2})[0-9][A-Z]{2,3}$/);
  }
});
test('QSO 文に穴埋めが残らない', () => {
  const r = makeRng(5);
  for (let i = 0; i < 50; i++) assert.doesNotMatch(qsoText(r), /[{}]/);
});
test('筆記問題', () => {
  const r = makeRng(2);
  for (const rev of [false, true]) for (let i = 0; i < 50; i++) {
    const q = writtenQuestion(r, rev);
    assert.equal(new Set(q.choices).size, 4);
    assert.ok(q.choices.includes(q.answer));
  }
});
