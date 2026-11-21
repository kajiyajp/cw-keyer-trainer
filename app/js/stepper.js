// 作成：2026-11-21
// 目的：キーボードなしで数値を変える −／＋ボタン（iPhone に USB キーボードをつないでいても使える）

const REPEAT_DELAY_MS = 400;  // 押し続けたとき、連続で変わり始めるまで
const REPEAT_EVERY_MS = 80;   // 連続で変わる間隔

// v に delta を足し、lo〜hi に収める（端で止まり、折り返さない）
export function stepValue(v, delta, lo, hi) {
  return Math.min(Math.max(v + delta, lo), hi);
}

// el に「− 値 ＋」を描く。値が変わるたびに onChange(新しい値) を呼ぶ。戻り値の set(v) で表示を外から変える
// hi は数か、上限を返す関数（実効の速さの上限＝文字の速さ のように、ほかの値で変わるとき）
export function renderStepper(el, { value, lo, hi, step = 1, onChange }) {
  const top = () => (typeof hi === 'function' ? hi() : hi);
  el.classList.add('stepper');
  el.innerHTML = `<button type="button" class="btn" data-d="-1" aria-label="減らす">−</button>
    <output></output>
    <button type="button" class="btn" data-d="1" aria-label="増やす">＋</button>`;
  const out = el.querySelector('output');
  const minus = el.querySelector('[data-d="-1"]');
  const plus = el.querySelector('[data-d="1"]');
  let cur = value;
  let timer = null;

  // 表示と、端でのボタンの無効化を今の値に合わせる
  const show = () => {
    out.textContent = cur;
    minus.disabled = cur <= lo;
    plus.disabled = cur >= top();
  };

  // 1 段階動かす
  const bump = (dir) => {
    const next = stepValue(cur, dir * step, lo, top());
    if (next === cur) return stopRepeat();
    cur = next;
    show();
    onChange(cur);
  };

  // 連続変化を止める
  const stopRepeat = () => {
    clearTimeout(timer);
    clearInterval(timer);
    timer = null;
  };

  let repeated = false;  // 押し続けて連続で変わったか（そのあとに来る click では動かさない）

  // 1 段階はタップ（click）で動かす。スクロールで指が触れただけでは変わらず、キーボード・VoiceOver でも動く
  // 押し続けたときだけ、400ms 後から連続で変える
  for (const b of [minus, plus]) {
    const dir = Number(b.dataset.d);
    b.addEventListener('click', (e) => {
      // キーボード・VoiceOver の click（detail が 0）はいつも 1 段動かす
      if (repeated && e.detail !== 0) { repeated = false; return; }
      bump(dir);
    });
    b.addEventListener('pointerdown', () => {
      stopRepeat();
      repeated = false;
      timer = setTimeout(() => {
        repeated = true;
        bump(dir);
        timer = setInterval(() => bump(dir), REPEAT_EVERY_MS);
      }, REPEAT_DELAY_MS);
    });
    // スクロールが始まると pointercancel が来るので、そこで止まる
    for (const ev of ['pointerup', 'pointerleave', 'pointercancel']) b.addEventListener(ev, stopRepeat);
    b.addEventListener('contextmenu', (e) => e.preventDefault());
  }
  // 指を離したことがボタンに届かなかったとき（無効化された・OS のジェスチャー）の保険
  window.addEventListener('pointerup', stopRepeat);
  window.addEventListener('blur', stopRepeat);
  show();
  return {
    // 外から値を変える（onChange は呼ばない）
    set(v) { cur = v; show(); },
  };
}
