// 作成：2026-11-21
// 目的：正答率と Koch レベルのテスト
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { accuracy, nextKochLevel } from '../js/scoring.js';

test('正答率', () => {
  assert.equal(accuracy('KMKMK', 'KMKMK'), 1);
  assert.equal(accuracy('KMKMK', 'KMKM'), 0.8);
  assert.equal(accuracy('CQ DE', 'cqde'), 1);
  assert.equal(accuracy('AB', 'XXXXXX'), 0);
  assert.equal(accuracy('', ''), 1);
});
test('Koch レベル', () => {
  assert.equal(nextKochLevel(2, 0.9), 3);
  assert.equal(nextKochLevel(2, 0.89), 2);
  assert.equal(nextKochLevel(41, 1), 41);
});
