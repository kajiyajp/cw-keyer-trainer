// 作成：2026-11-21
// 目的：進捗と設定の保存のテスト（保存できない環境でも動くこと）
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { loadProgress, saveProgress } from '../js/storage.js';

test('保存できないときは初期値で動く', () => {
  const broken = { getItem() { throw new Error('x'); }, setItem() { throw new Error('x'); } };
  assert.equal(loadProgress(broken).kochLevel, 2);
  assert.doesNotThrow(() => saveProgress(loadProgress(broken), broken));
});
test('壊れた JSON は初期値', () => {
  assert.equal(loadProgress({ getItem: () => '{oops', setItem() {} }).settings.toneHz, 700);
});
test('保存して読み戻す', () => {
  const mem = new Map(); const s = { getItem: (k) => mem.get(k) ?? null, setItem: (k, v) => mem.set(k, v) };
  const p = loadProgress(s); p.kochLevel = 7; saveProgress(p, s);
  assert.equal(loadProgress(s).kochLevel, 7);
});

test('localStorage の参照自体が例外を投げても起動できる', () => {
  const desc = Object.getOwnPropertyDescriptor(globalThis, 'localStorage');
  Object.defineProperty(globalThis, 'localStorage', { configurable: true, get() { throw new Error('SecurityError'); } });
  try {
    assert.equal(loadProgress().kochLevel, 2);
    assert.doesNotThrow(() => saveProgress(loadProgress()));
  } finally {
    if (desc) Object.defineProperty(globalThis, 'localStorage', desc);
    else delete globalThis.localStorage;
  }
});
test('保存値が範囲外なら収める', () => {
  const s = { getItem: () => JSON.stringify({ kochLevel: 99, settings: { charWpm: 'x', toneHz: 5000 } }), setItem() {} };
  const p = loadProgress(s);
  assert.equal(p.kochLevel, 41);
  assert.equal(p.settings.charWpm, 20);
  assert.equal(p.settings.toneHz, 1200);
});
test('古い保存値に echoLen と hint がなければ初期値', () => {
  const p = loadProgress({ getItem: () => JSON.stringify({ settings: { toneHz: 700 } }), setItem() {} });
  assert.equal(p.settings.echoLen, 1);
  assert.equal(p.settings.hint, true);
});
test('echoLen は 1〜5 に収め、hint の false は残す', () => {
  const read = (s) => loadProgress({ getItem: () => JSON.stringify({ settings: s }), setItem() {} }).settings;
  assert.equal(read({ echoLen: 9 }).echoLen, 5);
  assert.equal(read({ echoLen: 0 }).echoLen, 1);
  assert.equal(read({ hint: false }).hint, false);
});
