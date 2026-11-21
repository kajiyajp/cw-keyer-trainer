// 作成：2026-11-21
// 目的：欧文モールス符号表（ファームの lib/cw/morse.cpp と同じ内容）と Koch 法の文字順

// Koch 法で文字を追加していく順番（41 文字。ファームと同じ）
export const KOCH_ORDER = 'KMURESNAPTLWI.JZ=FOY,VG5/Q92H38B?47C1D60X';

const TABLE = {
  A: '.-', B: '-...', C: '-.-.', D: '-..', E: '.', F: '..-.', G: '--.', H: '....', I: '..',
  J: '.---', K: '-.-', L: '.-..', M: '--', N: '-.', O: '---', P: '.--.', Q: '--.-', R: '.-.',
  S: '...', T: '-', U: '..-', V: '...-', W: '.--', X: '-..-', Y: '-.--', Z: '--..',
  0: '-----', 1: '.----', 2: '..---', 3: '...--', 4: '....-',
  5: '.....', 6: '-....', 7: '--...', 8: '---..', 9: '----.',
  '.': '.-.-.-', ',': '--..--', '?': '..--..', '/': '-..-.', '=': '-...-', '-': '-....-',
};
const REVERSE = Object.fromEntries(Object.entries(TABLE).map(([c, p]) => [p, c]));

// 文字を ".-" 形式の符号にする（小文字は大文字扱い）。未対応は null
export function encode(ch) {
  return TABLE[String(ch).toUpperCase()] ?? null;
}

// ".-" 形式の符号を文字にする。一致しなければ '*'
export function decode(pattern) {
  return REVERSE[pattern] ?? '*';
}

// 画面表示用に "・" と "－" に置き換える
export function toDisplay(pattern) {
  return pattern.replaceAll('.', '・').replaceAll('-', '－');
}
