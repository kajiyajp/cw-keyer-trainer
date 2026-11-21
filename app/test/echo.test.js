// 作成：2026-11-21
// 目的：エコー練習の出題と判定のテスト（本体の EchoTrainer と同じ動き）
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ABBREVS, echoPrompt, patternOf, EchoJudge } from '../js/echo.js';
import { makeRng } from '../js/generators.js';

test('Koch はレベルの文字から echoLen 文字', () => {
  const rng = makeRng(1);
  for (let i = 0; i < 20; ++i) assert.match(echoPrompt('koch', 2, 3, rng), /^[KM]{3}$/);
  assert.equal(echoPrompt('koch', 10, 5, rng).length, 5);
});
test('略語は本体と同じ一覧から', () => {
  const rng = makeRng(2);
  assert.deepEqual(ABBREVS, ['CQ', 'DE', 'TU', '73', 'RST', 'UR', '5NN', 'QTH', 'OP']);
  for (let i = 0; i < 20; ++i) assert.ok(ABBREVS.includes(echoPrompt('abbr', 2, 1, rng)));
});
test('コールサインは英数字だけ', () => {
  assert.match(echoPrompt('call', 2, 1, makeRng(3)), /^[A-Z0-9]+$/);
});
test('符号の並び', () => {
  assert.equal(patternOf('CQ'), '-.-. --.-');
});
test('空白は無視し、出題の文字数で打ち切る', () => {
  const j = new EchoJudge('CQ');
  for (const c of ['C', ' ', 'Q', 'X']) j.onChar(c);
  assert.equal(j.answer, 'CQ');
  assert.ok(j.complete);
  assert.ok(j.correct);
});
test('違う文字なら そろっても不正解。reset で回答だけ消える', () => {
  const j = new EchoJudge('CQ');
  j.onChar('C'); assert.ok(!j.complete);
  j.onChar('K');
  assert.ok(j.complete);
  assert.ok(!j.correct);
  j.reset();
  assert.equal(j.answer, '');
  assert.equal(j.prompt, 'CQ');
});
test('回答に入った直後（字間 3 短点以内）に届いたシリアル文字は再生中の打鍵として捨てる', async () => {
  const { lateEnough } = await import('../js/echo.js');
  // 20WPM：短点 60ms、3 短点 180ms
  assert.equal(lateEnough(1100, 1000, 20), false);
  assert.equal(lateEnough(1180, 1000, 20), true);
});
