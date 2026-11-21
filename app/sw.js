// 作成：2026-11-21
// 目的：アプリのファイルを保存し、オフラインでも開けるようにする。
// 取得はネットワーク優先（公開し直した版がすぐ届く）で、つながらないときだけ保存した版を使う
const CACHE = 'procw-v2';
const FILES = [
  './', 'index.html', 'style.css', 'manifest.webmanifest',
  'icons/icon-192.png', 'icons/icon-512.png', 'icons/apple-touch-icon.png',
  'js/main.js', 'js/morse.js', 'js/timing.js', 'js/generators.js', 'js/scoring.js',
  'js/decoder.js', 'js/serial.js', 'js/storage.js', 'js/audio.js', 'js/keypad.js',
  'js/stepper.js', 'js/echo.js', 'js/screens/echo.js',
  'js/screens/receive.js', 'js/screens/written.js', 'js/screens/send.js', 'js/screens/settings.js',
];

// 入れたときに全ファイルを保存する
self.addEventListener('install', (e) => {
  // ブラウザの HTTP キャッシュではなく、サーバーから取り直して保存する
  e.waitUntil(caches.open(CACHE)
    .then((c) => c.addAll(FILES.map((f) => new Request(f, { cache: 'reload' }))))
    .then(() => self.skipWaiting()));
});

// 古い番号の保存を消す
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

// まずサーバーから取り、成功したら保存を更新する。つながらなければ保存した版を返す
self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET' || new URL(e.request.url).origin !== self.location.origin) return;
  e.respondWith(fetch(e.request)
    .then((res) => {
      if (res.ok) {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
      }
      return res;
    })
    .catch(() => caches.match(e.request, { ignoreSearch: true })));
});
