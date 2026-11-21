// 作成：2026-11-21
// 目的：受信・筆記の出題を作る（Koch 文字列・コールサイン・定型 QSO・筆記 4 択）
import { KOCH_ORDER, encode, toDisplay } from './morse.js';

const DOMESTIC = ['JA', 'JE', 'JF', 'JG', 'JH', 'JI', 'JJ', 'JK', 'JL', 'JM', 'JN', 'JO', 'JP', 'JQ', 'JR', 'JS'];
const FOREIGN = ['W', 'K', 'N', 'G', 'F', 'DL', 'VK', 'HL', 'BV'];
const RST = ['599', '579', '559', '589'];
const NAMES = ['HIRO', 'TARO', 'KEN', 'YUKI', 'MIKE', 'JOHN', 'BOB'];
const QTHS = ['TOKYO', 'OSAKA', 'NAGOYA', 'SAPPORO', 'FUKUOKA', 'SENDAI', 'KOBE'];
const QSO_TEMPLATES = [
  'CQ CQ CQ DE {my} {my} K',
  '{dx} DE {my} GM UR RST {rst} {rst} NAME {name} {name} QTH {qth} {qth} HW? {dx} DE {my} K',
  '{my} DE {dx} R TNX FER CALL UR RST {rst} NAME {name} QTH {qth} 73 {my} DE {dx} TU',
];
const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';

// xorshift32 の乱数。0 以上 1 未満を返す関数を作る
export function makeRng(seed) {
  let s = (seed >>> 0) || 1;
  return () => {
    s ^= s << 13; s >>>= 0;
    s ^= s >>> 17;
    s ^= s << 5; s >>>= 0;
    return s / 4294967296;
  };
}

// 配列から1つ選ぶ
function pick(arr, rng) {
  return arr[Math.floor(rng() * arr.length)];
}

// Koch 文字の 5 文字グループを groups 個、空白でつなぐ
export function kochText(level, groups, rng) {
  const lv = Math.min(Math.max(level, 2), KOCH_ORDER.length);
  const chars = KOCH_ORDER.slice(0, lv);
  const out = [];
  for (let g = 0; g < groups; g++) {
    let s = '';
    for (let i = 0; i < 5; i++) s += pick(chars, rng);
    out.push(s);
  }
  return out.join(' ');
}

// コールサインを1つ作る（4 回に 3 回は国内）
export function callsign(rng) {
  const prefix = rng() < 0.75 ? pick(DOMESTIC, rng) : pick(FOREIGN, rng);
  let s = prefix + Math.floor(rng() * 10);
  const suffix = Math.min(2 + Math.floor(rng() * 2), 6 - s.length);
  for (let i = 0; i < suffix; i++) s += pick(LETTERS, rng);
  return s;
}

// 定型 QSO 文を1つ作る
export function qsoText(rng) {
  const v = { my: callsign(rng), dx: callsign(rng), rst: pick(RST, rng), name: pick(NAMES, rng), qth: pick(QTHS, rng) };
  return pick(QSO_TEMPLATES, rng).replace(/\{(\w+)\}/g, (_, k) => v[k]);
}

// 筆記の 4 択問題。reverse=false は符号→文字、true は文字→符号
export function writtenQuestion(rng, reverse) {
  const pool = [...KOCH_ORDER];
  const picked = [];
  while (picked.length < 4) {
    const c = pick(pool, rng);
    if (!picked.includes(c)) picked.push(c);
  }
  const answerChar = picked[0];
  const show = (c) => toDisplay(encode(c));
  // 選択肢の並びを混ぜる
  for (let i = picked.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [picked[i], picked[j]] = [picked[j], picked[i]];
  }
  return reverse
    ? { prompt: answerChar, choices: picked.map(show), answer: show(answerChar) }
    : { prompt: show(answerChar), choices: picked, answer: answerChar };
}
