// 作成：2026-11-21
// 目的：画面上の文字ボタンに並べる文字のテスト
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { keypadChars } from '../js/keypad.js';

test('キーパッドの文字', () => {
  assert.deepEqual(keypadChars(3), ['K', 'M', 'U']);
  assert.equal(keypadChars('all').length, 41);
});
