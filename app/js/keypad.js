// 作成：2026-11-21
// 目的：画面上の文字ボタン（iPhone は機器をつなぐと画面のキーボードが出ないため）
import { KOCH_ORDER } from './morse.js';

const ALL = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,?/=';

// 並べる文字。数値なら Koch の先頭 level 文字、'all' なら全部
export function keypadChars(level) {
  if (level === 'all') return [...ALL];
  return [...KOCH_ORDER.slice(0, Math.min(Math.max(level, 2), KOCH_ORDER.length))];
}

// 文字ボタンと「空白」「1字消す」を描く。押すと onKey(文字)。空白は ' '、消すは '\b'
export function renderKeypad(el, chars, onKey) {
  el.replaceChildren();
  el.className = 'keypad';
  const add = (label, value, cls) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = label;
    if (cls) b.className = cls;
    b.addEventListener('click', () => onKey(value));
    el.append(b);
  };
  for (const c of chars) add(c, c);
  add('空白', ' ', 'wide');
  add('⌫', '\b', 'wide');
}
