// 作成：2026-11-21
// 目的：符号表（encode / decode / toDisplay / KOCH_ORDER）のテスト
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { KOCH_ORDER, encode, decode, toDisplay } from '../js/morse.js';

test('encode/decode', () => {
  assert.equal(encode('A'), '.-'); assert.equal(encode('a'), '.-');
  assert.equal(encode('='), '-...-'); assert.equal(encode('#'), null);
  assert.equal(decode('-.-'), 'K'); assert.equal(decode('.........'), '*');
});
test('Koch の全文字が符号化できる', () => {
  assert.equal(KOCH_ORDER.length, 41);
  for (const c of KOCH_ORDER) assert.notEqual(encode(c), null);
});
test('表示用', () => assert.equal(toDisplay('-.-.'), '－・－・'));
