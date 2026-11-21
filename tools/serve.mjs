// 作成：2026-11-22
// 目的：app/ を PC の localhost で配信する（追加のインストール不要。Node の標準機能だけ）
// 使い方：node tools/serve.mjs [ポート番号]（既定 8000）
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { extname, join, normalize, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(fileURLToPath(new URL('../app', import.meta.url)));
const PORT = Number(process.argv[2] ?? 8000);

// 拡張子ごとの Content-Type
const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.webmanifest': 'application/manifest+json',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
};

// URL のパスを app/ の中のファイルパスに直す。app/ の外を指すときは null を返す
function toFilePath(urlPath) {
  let p;
  try { p = decodeURIComponent(urlPath.split('?')[0]); } catch { return null; }
  if (p.endsWith('/')) p += 'index.html';
  const file = normalize(join(ROOT, p));
  return file === ROOT || file.startsWith(ROOT + sep) ? file : null;
}

// 1 つのリクエストに答える
async function handle(req, res) {
  const file = toFilePath(req.url);
  if (!file) { res.writeHead(403).end('Forbidden'); return; }
  try {
    if (!(await stat(file)).isFile()) throw new Error('not a file');
    const body = await readFile(file);
    res.writeHead(200, { 'Content-Type': TYPES[extname(file)] ?? 'application/octet-stream', 'Cache-Control': 'no-cache' });
    res.end(body);
  } catch {
    res.writeHead(404).end('Not Found');
  }
}

const server = createServer(handle);
server.on('error', (e) => {
  if (e.code === 'EADDRINUSE') console.error(`ポート ${PORT} は使用中です。別の番号を指定してください（例：-Port 8001）`);
  else console.error(e.message);
  process.exit(1);
});
server.listen(PORT, '127.0.0.1', () => {
  console.log(`http://localhost:${PORT}/ で配信中（Chrome / Edge で開く。止めるときは Ctrl+C）`);
});
