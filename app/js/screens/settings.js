// 作成：2026-11-21
// 目的：設定の画面（アプリの設定と、PC からの機器の設定の読み書き）
import { device } from '../serial.js';
import { renderStepper } from '../stepper.js';

// アプリの設定項目 [キー, 名前, 最小, 最大, 刻み]
const APP_FIELDS = [
  ['toneHz', '音の高さ (Hz)', 400, 1200, 50],
  ['charWpm', '文字の速さ (WPM)', 5, 40, 1],
  ['effWpm', '実効の速さ (WPM)', 5, 40, 1],
  ['groups', 'グループ数', 1, 10, 1],
];
// 機器の設定項目 [キー, 名前, 最小, 最大]（MODE は A/B）
const DEV_FIELDS = [
  ['WPM', '速さ (WPM)', 5, 40], ['MODE', 'モード (A/B)'], ['TONE', '音の高さ (Hz)', 400, 1200],
  ['SIDETONE', 'サイドトーン (0/1)', 0, 1], ['KOCH', 'Koch レベル', 2, 41],
  ['ECHOLEN', 'エコー文字数', 1, 5], ['HINT', 'ヒント (0/1)', 0, 1],
];
const REPLY_TIMEOUT_MS = 1000;

// 値が範囲内の整数か
function inRange(v, lo, hi) {
  return /^\d+$/.test(v) && Number(v) >= lo && Number(v) <= hi;
}

// 設定画面を el に組み立てる
export function mountSettings(el, ctx) {
  const { progress, save } = ctx;
  const s = progress.settings;

  el.innerHTML = `
    <div class="panel" data-id="app">
      <h2 style="font-size:16px;margin:0 0 8px">アプリ</h2>
      ${APP_FIELDS.map(([k, name]) => `
        <div class="field"><span>${name}</span><div data-app="${k}"></div></div>`).join('')}
      <div class="field"><span>Koch レベル</span><div data-id="koch"></div></div>
      <div class="field"><span>エコー文字数</span><div class="seg" data-id="echoLen">
        ${[1, 2, 3, 4, 5].map((n) => `<button type="button" data-v="${n}">${n}</button>`).join('')}</div></div>
      <div class="field"><span>エコーのヒント</span><div class="seg" data-id="hint">
        <button type="button" data-v="1">ON</button><button type="button" data-v="0">OFF</button></div></div>
      <p class="muted">実効の速さを文字の速さより遅くすると、文字はそのままで間だけ長くなります（ファーンズワース）。</p>
    </div>
    <div class="panel" data-id="dev"></div>`;
  const $ = (id) => el.querySelector(`[data-id="${id}"]`);

  // −／＋ボタンを並べる（キーボードなしで変えられる）
  const steppers = {};
  for (const [k, , lo, hi, step] of APP_FIELDS) {
    steppers[k] = renderStepper(el.querySelector(`[data-app="${k}"]`), {
      value: s[k], lo, step,
      hi: k === 'effWpm' ? () => s.charWpm : hi,  // 実効の速さは文字の速さまで
      onChange: (v) => {
        s[k] = v;
        if (s.effWpm > s.charWpm) s.effWpm = s.charWpm;
        save();
        fillApp();
      },
    });
  }
  const koch = renderStepper($('koch'), {
    value: progress.kochLevel, lo: 2, hi: 41,
    onChange: (v) => { progress.kochLevel = v; save(); },
  });

  // ボタンの並び（エコー文字数・ヒント）で 1 つ選ぶ
  const segPick = (id, get, set) => {
    const box = $(id);
    const mark = () => { for (const b of box.querySelectorAll('button')) b.classList.toggle('on', b.dataset.v === String(get())); };
    for (const b of box.querySelectorAll('button')) b.addEventListener('click', () => { set(Number(b.dataset.v)); save(); mark(); });
    return mark;
  };
  const markLen = segPick('echoLen', () => s.echoLen, (v) => { s.echoLen = v; });
  const markHint = segPick('hint', () => (s.hint ? 1 : 0), (v) => { s.hint = v === 1; });

  // 表示を今の値に合わせる（ほかの画面で Koch レベルが上がったときなど）
  const fillApp = () => {
    for (const [k] of APP_FIELDS) steppers[k].set(s[k]);
    koch.set(progress.kochLevel);
    markLen();
    markHint();
  };
  fillApp();
  // 設定タブを開くたびに最新の値を出す（受信で Koch レベルが上がっていることがある）
  new MutationObserver(() => { if (!el.hidden) fillApp(); }).observe(el, { attributes: true, attributeFilter: ['hidden'] });

  const dev = $('dev');
  if (!device.supported) {
    dev.innerHTML = `<h2 style="font-size:16px;margin:0 0 8px">機器</h2>
      <p class="muted">このブラウザからは機器の設定を変えられません。本体の Settings 画面か、PC の Chrome / Edge から設定してください。</p>`;
    return;
  }
  dev.innerHTML = `
    <h2 style="font-size:16px;margin:0 0 8px">機器（USB シリアル）</h2>
    <div class="row"><button type="button" class="primary" data-id="conn"></button><span class="muted" data-id="state"></span></div>
    <div data-id="fields" style="margin-top:8px">
      ${DEV_FIELDS.map(([k, name]) => `<label class="field">${name}<input type="text" data-dev="${k}" autocomplete="off"></label>`).join('')}
      <div class="row" style="margin-top:8px">
        <button type="button" class="btn" data-id="read">読み込み</button>
        <button type="button" class="primary" data-id="write">書き込み</button>
        <button type="button" class="btn" data-id="sync">アプリの速さを機器に合わせる</button>
      </div>
      <p data-id="msg"></p>
    </div>`;
  const input = (k) => el.querySelector(`[data-dev="${k}"]`);
  let waiter = null;  // OK / ERR を待っている関数

  // 接続状態を表示に反映する
  const showState = () => {
    $('conn').textContent = device.connected ? '切断' : '機器と接続';
    $('state').textContent = device.connected ? '接続中' : '未接続';
    $('fields').hidden = !device.connected;
  };

  // CONFIG の値を入力欄に入れる
  const fillDev = (values) => {
    for (const [k] of DEV_FIELDS) {
      input(k).value = values[k] ?? '';
      input(k).classList.remove('ng');
    }
  };

  device.listen((msg) => {
    if (msg.type === 'CONFIG') fillDev(msg.values);
    if ((msg.type === 'OK' || msg.type === 'ERR') && waiter) waiter(msg.type);
  });
  device.watch(showState);

  // 1 行送って OK / ERR を待つ（返事がなければ 'TIMEOUT'）
  const request = (line) => new Promise((resolve) => {
    const timer = setTimeout(() => { waiter = null; resolve('TIMEOUT'); }, REPLY_TIMEOUT_MS);
    waiter = (r) => { clearTimeout(timer); waiter = null; resolve(r); };
    device.send(line);
  });

  $('conn').addEventListener('click', async () => {
    try {
      if (device.connected) await device.disconnect();
      else await device.connect();
    } catch (e) {
      $('state').textContent = `接続できませんでした（${e.message}）`;
    }
  });
  $('read').addEventListener('click', () => device.send('GET CONFIG'));
  $('sync').addEventListener('click', () => {
    const w = Number(device.config?.WPM);
    if (!w) return;
    s.charWpm = w;
    if (s.effWpm > w) s.effWpm = w;
    save();
    fillApp();
    $('msg').textContent = `アプリの文字の速さを ${w} WPM にしました`;
  });
  $('write').addEventListener('click', async () => {
    // 送る前に範囲を確かめる
    let bad = false;
    for (const [k, , lo, hi] of DEV_FIELDS) {
      const v = input(k).value.trim().toUpperCase();
      const ok = k === 'MODE' ? v === 'A' || v === 'B' : inRange(v, lo, hi);
      input(k).classList.toggle('ng', !ok);
      bad ||= !ok;
    }
    if (bad) { $('msg').innerHTML = '<span class="ng">赤い項目の値が範囲外です</span>'; return; }
    const cur = device.config ?? {};
    for (const [k] of DEV_FIELDS) {
      const v = input(k).value.trim().toUpperCase();
      if (cur[k] === v) continue;
      const r = await request(`SET ${k} ${v}`);
      if (r !== 'OK') {
        input(k).classList.add('ng');
        $('msg').innerHTML = `<span class="ng">${k} を書き込めませんでした（${r}）</span>`;
        return;
      }
    }
    const r = await request('SAVE');
    $('msg').innerHTML = r === 'OK' ? '<span class="ok">保存しました</span>' : `<span class="ng">保存できませんでした（${r}）</span>`;
    device.send('GET CONFIG');
  });
  showState();
}
