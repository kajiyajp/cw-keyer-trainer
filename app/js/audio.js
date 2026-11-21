// 作成：2026-11-21
// 目的：Web Audio で時刻表どおりに符号を鳴らす（端末のスピーカー）
import { schedule } from './timing.js';

const RAMP = 0.005;  // 音の立ち上がり・立ち下がり 5ms（プツッという音を防ぐ）

export class Player {
  constructor() {
    this.ctx = null;
    this.osc = null;
    this.timer = null;
    this.finish = null;
    this.gen = 0;  // play / stop のたびに増やす。待っている間に変わったら古い play は鳴らさない
  }

  // 音声を有効にする（iOS はユーザー操作の中で呼ぶ必要がある。消音モードでも鳴らす設定にする）
  async unlock() {
    try {
      if (navigator.audioSession) navigator.audioSession.type = 'playback';
    } catch {
      // 対応していないブラウザでは何もしない
    }
    if (!this.ctx) this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    if (this.ctx.state !== 'running') await this.ctx.resume();
  }

  // 再生中か
  get playing() {
    return this.osc !== null;
  }

  // 文字列を鳴らす。鳴り終わる（または stop される）と解決する
  play(text, charWpm, effWpm, hz) {
    return this.run(schedule(text, charWpm, effWpm), hz);
  }

  // 短い音を 1 つ鳴らす（エコー練習の正解音）。鳴り終わる（または stop される）と解決する
  beep(hz, ms) {
    return this.run([{ startMs: 0, durMs: ms }], hz);
  }

  // 時刻表 segs（[{startMs, durMs}]）どおりに鳴らす。前の音は止める
  async run(segs, hz) {
    this.stop();
    const gen = this.gen;
    await this.unlock();
    if (gen !== this.gen) return;  // 待っている間に別の play / stop が来た
    if (!segs.length) return;
    const ctx = this.ctx;
    const t0 = ctx.currentTime + 0.05;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.frequency.value = hz;
    gain.gain.setValueAtTime(0, t0);
    for (const s of segs) {
      const a = t0 + s.startMs / 1000;
      const b = a + s.durMs / 1000;
      gain.gain.setValueAtTime(0, a);
      gain.gain.linearRampToValueAtTime(0.5, a + RAMP);
      gain.gain.setValueAtTime(0.5, b - RAMP);
      gain.gain.linearRampToValueAtTime(0, b);
    }
    osc.connect(gain).connect(ctx.destination);
    osc.start(t0);
    this.osc = osc;
    const last = segs[segs.length - 1];
    const totalMs = 50 + last.startMs + last.durMs + 50;
    return new Promise((resolve) => {
      this.finish = resolve;
      this.timer = setTimeout(() => this.stop(), totalMs);
    });
  }

  // すぐに止める
  stop() {
    this.gen++;
    clearTimeout(this.timer);
    this.timer = null;
    if (this.osc) {
      try { this.osc.stop(); } catch { /* 既に止まっている */ }
      this.osc.disconnect();
      this.osc = null;
    }
    const f = this.finish;
    this.finish = null;
    if (f) f();
  }
}
