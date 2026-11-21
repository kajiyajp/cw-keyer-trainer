// 作成：2026-11-21
// 目的：受信練習の画面（聞いて書き取る）
import { KOCH_ORDER } from '../morse.js';
import { makeRng, kochText, callsign, qsoText } from '../generators.js';
import { accuracy, nextKochLevel } from '../scoring.js';
import { addHistory } from '../storage.js';
import { keypadChars, renderKeypad } from '../keypad.js';

// 受信画面を el に組み立てる
export function mountReceive(el, ctx) {
  const { player, progress, save } = ctx;
  const rng = makeRng(Date.now());
  let current = '';   // 今の出題
  let checked = false;
  let kind = 'koch';  // koch / call / qso

  el.innerHTML = `
    <div class="seg" data-id="kinds">
      <button type="button" data-kind="koch" class="on">Koch</button>
      <button type="button" data-kind="call">コールサイン</button>
      <button type="button" data-kind="qso">交信文</button>
    </div>
    <div class="panel">
      <div class="muted" data-id="info"></div>
      <div class="row" style="margin-top:8px">
        <button type="button" class="primary" data-id="play">新しい問題</button>
        <button type="button" class="btn" data-id="again" disabled>もう一度</button>
        <button type="button" class="btn" data-id="stop">止める</button>
      </div>
    </div>
    <div class="panel">
      <input type="text" data-id="answer" placeholder="聞こえた文字" autocomplete="off" autocapitalize="characters" spellcheck="false">
      <div data-id="keypad" style="margin-top:8px"></div>
      <div class="row" style="margin-top:8px"><button type="button" class="primary" data-id="check" disabled>答え合わせ</button></div>
    </div>
    <div class="panel" data-id="result" hidden></div>`;
  const $ = (id) => el.querySelector(`[data-id="${id}"]`);
  const answer = $('answer');

  // 説明と文字ボタンを今の種類・レベルに合わせる
  const refresh = () => {
    const lv = progress.kochLevel;
    $('info').textContent = kind === 'koch'
      ? `Koch レベル ${lv}（使う文字：${KOCH_ORDER.slice(0, lv)}）／ 正答率 90% 以上で 1 文字増えます`
      : kind === 'call' ? 'コールサインを 5 個流します（空白は入れなくても採点できます）'
      : 'ラバースタンプ QSO（定型の交信文）を 1 文流します';
    renderKeypad($('keypad'), keypadChars(kind === 'koch' ? lv : 'all'), (k) => {
      answer.value = k === '\b' ? answer.value.slice(0, -1) : answer.value + k;
    });
  };

  // 出題を鳴らす
  const play = () => {
    const s = progress.settings;
    player.play(current, s.charWpm, s.effWpm, s.toneHz).catch(() => {
      // 音声を有効にできなかったときは鳴らさない（画面は動き続ける）
    });
  };

  $('play').addEventListener('click', () => {
    current = kind === 'koch' ? kochText(progress.kochLevel, progress.settings.groups, rng)
      : kind === 'call' ? Array.from({ length: 5 }, () => callsign(rng)).join(' ')
      : qsoText(rng);
    checked = false;
    answer.value = '';
    $('result').hidden = true;
    $('again').disabled = false;
    $('check').disabled = false;
    play();
  });
  $('again').addEventListener('click', play);
  $('stop').addEventListener('click', () => player.stop());
  $('check').addEventListener('click', () => {
    if (!current || checked) return;
    checked = true;
    player.stop();
    const acc = accuracy(current, answer.value);
    addHistory(progress, kind, acc);
    const before = progress.kochLevel;
    if (kind === 'koch') progress.kochLevel = nextKochLevel(before, acc);
    save();
    const pct = Math.round(acc * 100);
    const up = progress.kochLevel > before
      ? `<p class="ok">レベル ${progress.kochLevel} に上がりました。新しい文字：<b>${KOCH_ORDER[progress.kochLevel - 1]}</b></p>` : '';
    $('result').innerHTML = `
      <p class="big ${acc >= 0.9 ? 'ok' : 'ng'}">${pct}%</p>
      <p class="muted">正解</p><p class="mono">${current}</p>
      <p class="muted">あなたの答え</p><p class="mono">${answer.value.toUpperCase() || '（なし）'}</p>${up}`;
    $('result').hidden = false;
    $('check').disabled = true;
    refresh();
  });
  // 種類を切り替える
  for (const b of $('kinds').querySelectorAll('button')) {
    b.addEventListener('click', () => {
      kind = b.dataset.kind;
      for (const x of $('kinds').querySelectorAll('button')) x.classList.toggle('on', x === b);
      player.stop();
      current = '';
      answer.value = '';
      $('result').hidden = true;
      $('again').disabled = true;
      $('check').disabled = true;
      refresh();
    });
  }
  refresh();
}
