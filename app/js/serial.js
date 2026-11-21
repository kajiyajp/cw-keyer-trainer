// 作成：2026-11-21
// 目的：機器とのシリアル通信（行の解釈・行の組み立て・Web Serial 接続）

// 機器から来た1行を解釈する。知らない行は null
export function parseLine(raw) {
  const line = raw.replace(/\r$/, '');
  let m;
  if ((m = /^E ([.-]) (\d+)$/.exec(line))) return { type: 'E', symbol: m[1], ms: Number(m[2]) };
  if ((m = /^C (.)/.exec(line))) return { type: 'C', ch: m[1] };
  if ((m = /^CONFIG (.*)$/.exec(line))) {
    const values = {};
    for (const kv of m[1].trim().split(/\s+/)) {
      const [k, v] = kv.split('=');
      if (k && v !== undefined) values[k] = v;
    }
    return { type: 'CONFIG', values };
  }
  if (line === 'OK') return { type: 'OK' };
  if (line === 'ERR') return { type: 'ERR' };
  return null;
}

// 分かれて届いた文字列から、完成した行だけを取り出す（\r は除く）
export class LineSplitter {
  constructor() {
    this.buf = '';
  }

  // 受け取った文字列を足し、完成した行の配列を返す
  push(chunk) {
    this.buf += chunk;
    const parts = this.buf.split('\n');
    this.buf = parts.pop();
    return parts.map((s) => s.replace(/\r$/, '')).filter((s) => s.length);
  }
}

const GET_CONFIG_TRIES = 5;
const GET_CONFIG_INTERVAL_MS = 500;

// Web Serial で機器とつなぐ（PC の Chrome / Edge のみ）
export const device = {
  supported: typeof navigator !== 'undefined' && 'serial' in navigator,
  connected: false,
  config: null,        // 最後に受け取った CONFIG の値
  port: null,
  reader: null,
  lineListeners: new Set(),
  stateListeners: new Set(),

  // 受信した行（parseLine の結果）を受け取る関数を登録する。解除する関数を返す
  listen(fn) {
    this.lineListeners.add(fn);
    return () => this.lineListeners.delete(fn);
  },

  // 接続状態の変化を受け取る関数を登録する。解除する関数を返す
  watch(fn) {
    this.stateListeners.add(fn);
    return () => this.stateListeners.delete(fn);
  },

  // 接続状態を変えて知らせる
  setState(connected) {
    this.connected = connected;
    for (const fn of this.stateListeners) fn(connected);
  },

  // ポートを選んで開き、受信を始め、CONFIG が来るまで GET CONFIG を送る
  async connect() {
    if (!this.supported || this.connected) return;
    const port = await navigator.serial.requestPort();
    await port.open({ baudRate: 115200 });
    this.port = port;
    this.setState(true);
    this.readLoop();
    for (let i = 0; i < GET_CONFIG_TRIES && this.connected; i++) {
      const before = this.config;
      await this.send('GET CONFIG');
      await new Promise((r) => setTimeout(r, GET_CONFIG_INTERVAL_MS));
      if (this.config && this.config !== before) break;
    }
  },

  // 受信ループ。ケーブルが抜けるなどで終わったら未接続にする
  async readLoop() {
    const splitter = new LineSplitter();
    const decoder = new TextDecoder();
    try {
      this.reader = this.port.readable.getReader();
      for (;;) {
        const { value, done } = await this.reader.read();
        if (done) break;
        for (const line of splitter.push(decoder.decode(value, { stream: true }))) {
          const msg = parseLine(line);
          if (!msg) continue;
          if (msg.type === 'CONFIG') this.config = msg.values;
          for (const fn of this.lineListeners) fn(msg);
        }
      }
    } catch {
      // 読み取りの失敗（抜けたなど）は未接続として扱う
    } finally {
      try { this.reader?.releaseLock(); } catch { /* 既に解放済み */ }
      this.reader = null;
      try { await this.port?.close(); } catch { /* 既に閉じている */ }
      this.port = null;
      this.config = null;
      if (this.connected) this.setState(false);
    }
  },

  // 切断する
  async disconnect() {
    try { await this.reader?.cancel(); } catch { /* 読み取りが終わっている */ }
  },

  // 1 行送る
  async send(line) {
    if (!this.port?.writable) return;
    const writer = this.port.writable.getWriter();
    try {
      await writer.write(new TextEncoder().encode(line + '\n'));
    } finally {
      writer.releaseLock();
    }
  },
};

// ケーブルが抜けたら受信ループの終了で未接続になるが、念のためイベントでも切る
if (device.supported) {
  navigator.serial.addEventListener('disconnect', (e) => {
    if (e.target === device.port) device.disconnect();
  });
}
