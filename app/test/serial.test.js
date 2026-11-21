// 作成：2026-11-21
// 目的：シリアル行の解釈と行の組み立てのテスト
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseLine, LineSplitter } from '../js/serial.js';

test('行の解釈', () => {
  assert.deepEqual(parseLine('E . 62'), { type: 'E', symbol: '.', ms: 62 });
  assert.deepEqual(parseLine('C A'), { type: 'C', ch: 'A' });
  assert.equal(parseLine('CONFIG WPM=15 MODE=A TONE=1200 SIDETONE=1 KOCH=2 ECHOLEN=1 HINT=1').values.TONE, '1200');
  assert.deepEqual(parseLine('OK'), { type: 'OK' });
  assert.equal(parseLine('???'), null);
});
test('分割された行・CRLF', () => {
  const s = new LineSplitter();
  assert.deepEqual(s.push('E . 6'), []);
  assert.deepEqual(s.push('2\r\nC '), ['E . 62']);
  assert.deepEqual(s.push('A\r\nOK\r\n'), ['C A', 'OK']);
});
