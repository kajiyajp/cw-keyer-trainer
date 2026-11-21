// 作成：2026-11-21
// 目的：送信練習の画面（お題を打つ → 解読結果・正誤・リズムのずれを表示）
import { makeRng, kochText, callsign } from '../generators.js';
import { accuracy } from '../scoring.js';
import { addHistory } from '../storage.js';
import { decodeMarks, HidRecorder, finishDelayMs, withinTolerance } from '../decoder.js';
import { device } from '../serial.js';

const ABBREVS = ['CQ', 'DE', 'TU', '73', 'RST', 'UR', '5NN', 'QTH', 'OP'];

// 送信画面を el に組み立てる
export function mountSend(el, ctx) {
  const { progress, save } = ctx;
  const rng = makeRng(Date.now() ^ 0x1234);
  const hid = new HidRecorder();
  let kind = 'koch';
  let prompt = '';
  let serialMarks = [];
  let lastEnd = null;   // シリアル：直前の要素が終わった時刻
  let finishTimer = null;
  let finished = false;  // 締めたあとは、新しいお題かやり直しまで入力を受け付けない

  el.innerHTML = `
    <div class="seg" data-id="kinds">
      <button type="button" data-kind="koch" class="on">Koch 文字</button>
      <button type="button" data-kind="call">コールサイン</button>
      <button type="button" data-kind="abbr">略語</button>
    </div>
    <div class="panel">
      <div class="muted" data-id="source"></div>
      <p class="big" data-id="prompt" style="text-align:center">―</p>
      <div class="row">
        <button type="button" class="primary" data-id="new">新しいお題</button>
        <button type="button" class="btn" data-id="done">完了</button>
        <button type="button" class="btn" data-id="retry">やり直し</button>
      </div>
      <p class="mono" data-id="live"></p>
    </div>
    <div class="panel" data-id="result" hidden>
      <p data-id="verdict"></p>
      <canvas data-id="chart"></canvas>
      <table data-id="stats"></table>
    </div>`;
  const $ = (id) => el.querySelector(`[data-id="${id}"]`);
  const visible = () => !el.hidden;

  // 解読に使う速さ（シリアル接続中は機器の WPM）
  const wpm = () => Number(device.config?.WPM) || progress.settings.charWpm;

  // 入力元の表示を更新する
  const showSource = () => {
    $('source').textContent = device.connected
      ? `入力：機器（シリアル）　速さ ${wpm()} WPM`
      : `入力：USB キーボード（F13）　速さ ${wpm()} WPM（設定の「文字の速さ」を機器と合わせてください）`;
  };

  // 今までの打鍵を marks にする
  const marks = () => (device.connected ? serialMarks : hid.marks());

  // 打鍵の途中経過を表示し、締めのタイマーを掛け直す
  const touched = () => {
    $('live').textContent = decodeMarks(marks(), wpm()).text;
    clearTimeout(finishTimer);
    finishTimer = setTimeout(finish, finishDelayMs(wpm(), wpm()));
  };

  // 記録を消す
  const clear = () => {
    clearTimeout(finishTimer);
    hid.reset();
    serialMarks = [];
    lastEnd = null;
    finished = false;
    $('live').textContent = '';
    $('result').hidden = true;
  };

  // 新しいお題
  const newPrompt = () => {
    prompt = kind === 'koch' ? kochText(progress.kochLevel, 1, rng)
      : kind === 'call' ? callsign(rng)
      : ABBREVS[Math.floor(rng() * ABBREVS.length)];
    $('prompt').textContent = prompt;
    clear();
    // 本体の Settings で WPM が変わっていることがあるので読み直す
    if (device.connected) device.send('GET CONFIG').catch(() => {});
  };

  // 締めて結果を出す
  const finish = () => {
    clearTimeout(finishTimer);
    if (finished) return;
    const m = marks();
    if (!prompt || !m.some((x) => x.on)) return;
    finished = true;
    const w = wpm();
    const res = decodeMarks(m, w);
    const acc = accuracy(prompt, res.text);
    addHistory(progress, 'send', acc);
    save();
    $('verdict').innerHTML = `<span class="big ${acc >= 0.9 ? 'ok' : 'ng'}">${Math.round(acc * 100)}%</span>
      <span class="mono">　打った文字：${res.text || '（なし）'}</span>`;
    renderStats(res.stats, w);
    $('result').hidden = false;
    drawChart($('chart'), res.elements, w);
  };

  // 集計を表にする（理想の値と並べる）
  const renderStats = (s, w) => {
    const dit = 1200 / w;
    const f = (v) => (v == null ? '―' : Math.round(v));
    const rows = [
      ['短点の長さ', f(s.dotAvg), Math.round(dit)],
      ['長点の長さ', f(s.dashAvg), Math.round(dit * 3)],
      ['長点 ÷ 短点', s.ratio == null ? '―' : s.ratio.toFixed(2), '3.00'],
      ['符号の中の間', f(s.elemGapAvg), Math.round(dit)],
      ['文字の間', f(s.charGapAvg), Math.round(dit * 3)],
    ];
    $('stats').innerHTML = '<tr><th></th><th>あなた (ms)</th><th>理想 (ms)</th></tr>'
      + rows.map((r) => `<tr><td>${r[0]}</td><td>${r[1]}</td><td>${r[2]}</td></tr>`).join('');
  };

  // HID（F13）。シリアル接続中は二重になるので使わない
  document.addEventListener('keydown', (e) => {
    if (e.code !== 'F13' || !visible()) return;
    e.preventDefault();
    if (e.repeat || device.connected || finished) return;
    hid.down();
  });
  document.addEventListener('keyup', (e) => {
    if (e.code !== 'F13') return;
    // 別のタブにいる間に離されたら、押下中の状態だけ捨てる（次の符号を失わないため）
    if (!visible()) { hid.cancel(); return; }
    e.preventDefault();
    if (device.connected || finished) return;
    hid.up();
    touched();
  });
  // ページが裏に回る・フォーカスが外れると keyup が届かないので、押下中の状態を捨てる
  document.addEventListener('visibilitychange', () => { if (document.hidden) hid.cancel(); });
  window.addEventListener('blur', () => hid.cancel());

  // シリアル：E 行の長さを on、前の要素の終わりからの空きを off にする
  device.listen((msg) => {
    if (msg.type === 'CONFIG') showSource();
    if (msg.type !== 'E' || !visible() || finished) return;
    const now = performance.now();
    const start = now - msg.ms;
    if (lastEnd !== null) serialMarks.push({ on: false, ms: Math.max(0, start - lastEnd) });
    serialMarks.push({ on: true, ms: msg.ms });
    lastEnd = now;
    touched();
  });
  device.watch(() => { clear(); showSource(); });

  $('new').addEventListener('click', newPrompt);
  $('done').addEventListener('click', finish);
  $('retry').addEventListener('click', clear);
  for (const b of $('kinds').querySelectorAll('button')) {
    b.addEventListener('click', () => {
      kind = b.dataset.kind;
      for (const x of $('kinds').querySelectorAll('button')) x.classList.toggle('on', x === b);
      newPrompt();
    });
  }
  showSource();
  newPrompt();
}

// 要素ごとの長さを棒グラフにし、理想の短点・長点の長さに線を引く
function drawChart(canvas, elements, wpm) {
  const css = getComputedStyle(document.documentElement);
  const color = (name) => css.getPropertyValue(name).trim();
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  canvas.width = w * dpr; canvas.height = h * dpr;
  const g = canvas.getContext('2d');
  g.scale(dpr, dpr);
  g.clearRect(0, 0, w, h);
  const dit = 1200 / wpm;
  const max = Math.max(dit * 4, ...elements.map((e) => e.ms));
  const y = (ms) => h - 16 - (ms / max) * (h - 24);
  const bw = Math.max(4, Math.min(24, (w - 8) / Math.max(elements.length, 1) - 4));
  elements.forEach((e, i) => {
    const ideal = e.symbol === '.' ? dit : dit * 3;
    g.fillStyle = withinTolerance(e.ms, ideal) ? color('--ok') : color('--ng');
    const x = 4 + i * (bw + 4);
    g.fillRect(x, y(e.ms), bw, h - 16 - y(e.ms));
  });
  g.strokeStyle = color('--muted');
  g.fillStyle = color('--muted');
  g.font = '11px system-ui';
  for (const [ms, label] of [[dit, '短点'], [dit * 3, '長点']]) {
    g.beginPath(); g.setLineDash([4, 4]);
    g.moveTo(0, y(ms)); g.lineTo(w, y(ms)); g.stroke();
    g.fillText(`${label} ${Math.round(ms)}ms`, w - 80, y(ms) - 3);
  }
  g.setLineDash([]);
}
