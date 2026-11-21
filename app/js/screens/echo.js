// 作成：2026-11-21
// 目的：エコー練習の画面（出題を聞く → パドルで打ち返す → 正解音か正解の再生 → 次の問題。本体の Echo 画面と同じ流れ）
import { makeRng } from '../generators.js';
import { echoPrompt, patternOf, EchoJudge, lateEnough } from '../echo.js';
import { decodeMarks, HidRecorder } from '../decoder.js';
import { device } from '../serial.js';

const OK_BEEP_HZ = 1600;      // 本体と同じ。打鍵音の上限 1200Hz より高くして区別する
const OK_BEEP_MS = 50;
const RESULT_WAIT_MS = 1200;  // 結果の音が鳴り終わってから次の問題まで
const KIND_NAMES = { koch: 'Koch', call: 'コールサイン', abbr: '略語' };

// エコー画面を el に組み立てる。タブの出入りで呼ぶ show() / hide() を返す
export function mountEcho(el, ctx) {
  const { player, progress } = ctx;
  const s = progress.settings;
  const rng = makeRng(Date.now() ^ 0x5a5a);
  const hid = new HidRecorder();
  let kind = 'koch';
  let judge = null;
  let state = 'idle';    // idle / listen / answer / result
  let gen = 0;           // 問題を出し直す・止めるたびに増やす。古い再生の続きを捨てるため
  let used = 0;          // 解読した文字のうち、判定に渡し終えた数
  let charTimer = null;  // 文字の区切りを待つタイマー
  let nextTimer = null;  // 次の問題までのタイマー
  let ok = 0, all = 0;
  let answerAt = 0;      // 回答を受け付け始めた時刻（シリアルの再生中の打鍵を捨てるため）

  el.innerHTML = `
    <div class="seg" data-id="kinds">
      <button type="button" data-kind="koch" class="on">Koch</button>
      <button type="button" data-kind="call">コールサイン</button>
      <button type="button" data-kind="abbr">略語</button>
    </div>
    <div class="panel echo">
      <div class="row" style="justify-content:space-between">
        <span class="muted" data-id="info"></span><span data-id="score"></span>
      </div>
      <p class="mono muted" data-id="pattern"></p>
      <p class="big" data-id="prompt"></p>
      <p class="big mono" data-id="answer"></p>
      <div class="row">
        <button type="button" class="btn" data-id="again">もう一度聞く</button>
        <button type="button" class="primary" data-id="next">次の問題</button>
      </div>
    </div>
    <p class="muted" data-id="source"></p>`;
  const $ = (id) => el.querySelector(`[data-id="${id}"]`);
  const visible = () => !el.hidden;

  // 画面を今の状態に合わせる
  const render = () => {
    // 文字数を使うのは Koch だけ
    const len = kind === 'koch' ? `・${s.echoLen}文字` : '';
    $('info').textContent = `${KIND_NAMES[kind]}　Lv${progress.kochLevel}${len}・${s.charWpm}/${s.effWpm} WPM`;
    $('score').textContent = `${ok} / ${all}`;
    const p = judge?.prompt ?? '';
    const showPrompt = s.hint || state === 'result';
    $('pattern').textContent = s.hint ? patternOf(p) : '';
    $('prompt').textContent = showPrompt ? p : '';
    const a = $('answer');
    a.className = 'big mono';
    if (state === 'idle') a.textContent = '「次の問題」で始めます';
    else if (state === 'listen') a.textContent = 'listen…';
    else if (state === 'answer') a.textContent = judge.answer || '_';
    else {
      a.textContent = judge.correct ? 'OK' : judge.answer;
      a.classList.add(judge.correct ? 'ok' : 'ng');
    }
    $('again').disabled = state === 'idle';
    $('source').textContent = device.connected
      ? '入力：機器（シリアル）が解読した文字'
      : '入力：USB キーボード（F13）。キーヤーの速さを設定の「文字の速さ」と合わせてください';
  };

  // タイマーを全部止める
  const clearTimers = () => {
    clearTimeout(charTimer);
    clearTimeout(nextTimer);
    charTimer = nextTimer = null;
  };

  // 出題を鳴らし、鳴り終わったら回答を受け付ける
  const listen = async () => {
    const g = ++gen;
    clearTimers();
    judge.reset();
    hid.reset();
    used = 0;
    state = 'listen';
    render();
    await player.play(judge.prompt, s.charWpm, s.effWpm, s.toneHz).catch(() => {});
    if (g !== gen) return;  // 途中で止められた・出し直された
    hid.reset();  // 再生中の打鍵は捨てる
    answerAt = performance.now();
    state = 'answer';
    render();
  };

  // 新しい問題を出す
  const newPrompt = () => {
    judge = new EchoJudge(echoPrompt(kind, progress.kochLevel, s.echoLen, rng));
    listen();
  };

  // そろったら判定し、音を鳴らして次の問題を待つ
  const checkDone = async () => {
    render();
    if (!judge.complete) return;
    const g = gen;
    state = 'result';
    clearTimeout(charTimer);
    ++all;
    if (judge.correct) ++ok;
    render();
    if (judge.correct) await player.beep(OK_BEEP_HZ, OK_BEEP_MS).catch(() => {});
    else await player.play(judge.prompt, s.charWpm, s.effWpm, s.toneHz).catch(() => {});
    if (g !== gen) return;
    nextTimer = setTimeout(() => { if (g === gen) newPrompt(); }, RESULT_WAIT_MS);
  };

  // HID の打鍵を解読し、新しく確定した文字を判定に渡す
  const consume = () => {
    if (state !== 'answer') return;
    const text = decodeMarks(hid.marks(), s.charWpm).text.replaceAll(' ', '');
    for (const c of text.slice(used)) judge.onChar(c);
    used = text.length;
    checkDone();
  };

  // HID（F13）。シリアル接続中は機器の C 行を使うので無視する
  document.addEventListener('keydown', (e) => {
    if (e.code !== 'F13' || !visible()) return;
    e.preventDefault();
    if (e.repeat || device.connected || state !== 'answer') return;
    clearTimeout(charTimer);
    hid.down();
  });
  document.addEventListener('keyup', (e) => {
    if (e.code !== 'F13') return;
    if (!visible()) { hid.cancel(); return; }
    e.preventDefault();
    if (device.connected || state !== 'answer') return;
    hid.up();
    // 短点 2 個分あいたら 1 文字確定（本体の解読と同じしきい値）
    clearTimeout(charTimer);
    charTimer = setTimeout(consume, 2 * (1200 / s.charWpm) + 10);
  });
  document.addEventListener('visibilitychange', () => { if (document.hidden) hid.cancel(); });
  window.addEventListener('blur', () => hid.cancel());

  // シリアル：機器が解読した文字をそのまま使う
  device.listen((msg) => {
    if (msg.type !== 'C' || !visible() || state !== 'answer') return;
    const wpm = Number(device.config?.WPM) || s.charWpm;
    if (!lateEnough(performance.now(), answerAt, wpm)) return;  // 再生中に打った文字
    judge.onChar(msg.ch);
    checkDone();
  });
  device.watch(render);

  $('again').addEventListener('click', () => { if (judge && state !== 'idle') listen(); });
  $('next').addEventListener('click', newPrompt);
  for (const b of $('kinds').querySelectorAll('button')) {
    b.addEventListener('click', () => {
      kind = b.dataset.kind;
      for (const x of $('kinds').querySelectorAll('button')) x.classList.toggle('on', x === b);
      ok = all = 0;
      newPrompt();
    });
  }
  render();

  return {
    // タブに入ったとき：設定の変更を表示に反映する
    show() { render(); },
    // タブを出たとき・裏に回ったとき：音とタイマーを止め、始める前の状態に戻す
    hide() {
      ++gen;
      clearTimers();
      hid.cancel();
      judge = null;  // 前の問題の符号・文字を表示に残さない
      if (state !== 'idle') { state = 'idle'; render(); }
    },
  };
}
