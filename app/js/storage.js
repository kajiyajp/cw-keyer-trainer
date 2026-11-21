// 作成：2026-11-21
// 目的：進捗と設定を localStorage に保存する（使えない環境では初期値のまま動く）

const KEY = 'procw.progress';
const HISTORY_MAX = 200;

// 初期値を作る
export function defaultProgress() {
  return {
    kochLevel: 2,
    history: [],
    settings: { toneHz: 700, charWpm: 20, effWpm: 10, groups: 5, echoLen: 1, hint: true },
  };
}

// 数値を範囲に収める。数でなければ既定値
function clampNum(v, lo, hi, def) {
  const n = Math.round(Number(v));
  return Number.isFinite(n) ? Math.min(Math.max(n, lo), hi) : def;
}

// 読み込む。読めない・壊れている・例外のときは初期値。値は範囲に収める
// （localStorage は参照しただけで例外になる環境があるので、参照も try の中で行う）
export function loadProgress(store) {
  const base = defaultProgress();
  try {
    const raw = (store ?? globalThis.localStorage)?.getItem(KEY);
    if (!raw) return base;
    const p = JSON.parse(raw);
    const s = { ...base.settings, ...(p.settings ?? {}) };
    const charWpm = clampNum(s.charWpm, 5, 40, base.settings.charWpm);
    return {
      kochLevel: clampNum(p.kochLevel, 2, 41, base.kochLevel),
      history: Array.isArray(p.history) ? p.history.slice(0, HISTORY_MAX) : [],
      settings: {
        toneHz: clampNum(s.toneHz, 400, 1200, base.settings.toneHz),
        charWpm,
        effWpm: clampNum(s.effWpm, 5, charWpm, Math.min(base.settings.effWpm, charWpm)),
        groups: clampNum(s.groups, 1, 10, base.settings.groups),
        echoLen: clampNum(s.echoLen, 1, 5, base.settings.echoLen),
        hint: s.hint !== false,
      },
    };
  } catch {
    return base;
  }
}

// 保存する。失敗しても無視する
export function saveProgress(p, store) {
  try {
    (store ?? globalThis.localStorage)?.setItem(KEY, JSON.stringify(p));
  } catch {
    // 保存できない環境（プライベートブラウズなど）では何もしない
  }
}

// 結果を履歴の先頭に足す（最大 200 件）
export function addHistory(p, mode, acc) {
  p.history.unshift({ date: new Date().toISOString(), mode, acc });
  p.history.length = Math.min(p.history.length, HISTORY_MAX);
}
