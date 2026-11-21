// 作成：2026-11-21
// 目的：アプリの入口（タブ切り替え・音声の有効化・各画面の組み立て）
import { Player } from './audio.js';
import { loadProgress, saveProgress } from './storage.js';
import { mountReceive } from './screens/receive.js';
import { mountWritten } from './screens/written.js';
import { mountEcho } from './screens/echo.js';
import { mountSend } from './screens/send.js';
import { mountSettings } from './screens/settings.js';

const progress = loadProgress();
const player = new Player();
const ctx = { player, progress, save: () => saveProgress(progress) };

// タブを切り替える
function showTab(name) {
  for (const b of document.querySelectorAll('#tabs button')) b.classList.toggle('on', b.dataset.tab === name);
  for (const s of document.querySelectorAll('main > section')) s.hidden = s.id !== name;
  player.stop();
  if (name === 'echo') echo.show();
  else echo.hide();
}

for (const b of document.querySelectorAll('#tabs button')) b.addEventListener('click', () => showTab(b.dataset.tab));

// ページが裏に回ったら音を止める
document.addEventListener('visibilitychange', () => {
  if (document.hidden) { player.stop(); echo.hide(); }
});

// 「はじめる」で音声を有効化する（iOS はタップの中でないと音が出ない）
document.getElementById('startBtn').addEventListener('click', async () => {
  await player.unlock();
  document.getElementById('start').hidden = true;
});

mountReceive(document.getElementById('receive'), ctx);
mountWritten(document.getElementById('written'), ctx);
const echo = mountEcho(document.getElementById('echo'), ctx);
mountSend(document.getElementById('send'), ctx);
mountSettings(document.getElementById('settings'), ctx);

// オフラインで動かすための Service Worker を登録する
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js').catch(() => {
    // 登録できなくてもアプリはそのまま動く
  });
}
