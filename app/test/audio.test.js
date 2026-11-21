// 作成：2026-11-21
// 目的：再生が重ならないこと（再生中にもう一度・止めるを押したとき）のテスト。AudioContext は偽物で代用
import { test } from 'node:test';
import assert from 'node:assert/strict';

const oscs = [];
// 偽の AudioContext（resume は少し遅れて終わる。iOS で裏から戻ったときを再現）
class FakeCtx {
  constructor() { this.state = 'suspended'; this.currentTime = 0; this.destination = {}; }
  resume() { return new Promise((r) => setTimeout(() => { this.state = 'running'; r(); }, 10)); }
  createOscillator() {
    const o = { frequency: {}, stopped: false, start() {}, stop() { this.stopped = true; }, connect: (g) => g, disconnect() {} };
    oscs.push(o);
    return o;
  }
  createGain() { return { gain: { setValueAtTime() {}, linearRampToValueAtTime() {} }, connect: () => ({}) }; }
}
globalThis.window = { AudioContext: FakeCtx };
const { Player } = await import('../js/audio.js');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

test('続けて play しても鳴っているのは 1 つだけ', async () => {
  oscs.length = 0;
  const p = new Player();
  p.play('E', 20, 20, 700);
  p.play('E', 20, 20, 700);
  await sleep(40);
  assert.equal(oscs.filter((o) => !o.stopped).length, 1);
  p.stop();
});
test('play の直後に stop したら鳴らない', async () => {
  oscs.length = 0;
  const p = new Player();
  p.ctx = null;
  p.play('E', 20, 20, 700);
  p.stop();
  await sleep(40);
  assert.equal(oscs.filter((o) => !o.stopped).length, 0);
});
test('beep は 1600Hz の音を 1 つだけ鳴らし、鳴り終わると解決する', async () => {
  oscs.length = 0;
  const p = new Player();
  p.play('E', 20, 20, 700);
  const done = p.beep(1600, 50);
  await sleep(40);
  const live = oscs.filter((o) => !o.stopped);
  assert.equal(live.length, 1);
  assert.equal(live[0].frequency.value, 1600);
  await done;
  assert.equal(p.playing, false);
});
