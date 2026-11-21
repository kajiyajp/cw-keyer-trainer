// 作成：2026-11-21
// 目的：筆記（試験対策）の画面。符号と文字の対応を 4 択で 10 問
import { makeRng, writtenQuestion } from '../generators.js';
import { addHistory } from '../storage.js';

const COUNT = 10;

// 筆記画面を el に組み立てる
export function mountWritten(el, ctx) {
  const { progress, save } = ctx;
  const rng = makeRng(Date.now() ^ 0x5a5a);
  let reverse = false;
  let n = 0, score = 0, q = null, answered = false;

  el.innerHTML = `
    <div class="seg" data-id="dirs">
      <button type="button" data-rev="0" class="on">符号 → 文字</button>
      <button type="button" data-rev="1">文字 → 符号</button>
    </div>
    <div class="panel">
      <div class="muted" data-id="progress"></div>
      <p class="big" data-id="prompt" style="text-align:center"></p>
      <div class="choices" data-id="choices"></div>
      <p data-id="feedback"></p>
      <div class="row"><button type="button" class="primary" data-id="next">はじめる</button></div>
    </div>`;
  const $ = (id) => el.querySelector(`[data-id="${id}"]`);

  // 1 問出す
  const ask = () => {
    q = writtenQuestion(rng, reverse);
    answered = false;
    $('progress').textContent = `${n + 1} / ${COUNT} 問　正解 ${score}`;
    $('prompt').textContent = q.prompt;
    $('feedback').textContent = '';
    $('next').hidden = true;
    const box = $('choices');
    box.replaceChildren();
    for (const c of q.choices) {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'btn';
      b.textContent = c;
      b.addEventListener('click', () => choose(c, b));
      box.append(b);
    }
  };

  // 選んだ答えを判定する
  const choose = (c, btn) => {
    if (answered) return;
    answered = true;
    const ok = c === q.answer;
    if (ok) score++;
    btn.classList.add(ok ? 'ok' : 'ng');
    $('feedback').innerHTML = ok ? '<span class="ok">正解</span>' : `<span class="ng">不正解</span>　正しくは <b>${q.answer}</b>`;
    n++;
    $('next').textContent = n < COUNT ? '次へ' : '結果を見る';
    $('next').hidden = false;
  };

  // 次へ／結果／やり直し
  const next = () => {
    if (n < COUNT) return ask();
    const acc = score / COUNT;
    addHistory(progress, 'written', acc);
    save();
    $('progress').textContent = '';
    $('prompt').textContent = `${score} / ${COUNT}`;
    $('choices').replaceChildren();
    $('feedback').textContent = acc >= 0.9 ? 'よくできました' : '間違えた符号を見直してから、もう一度どうぞ';
    $('next').textContent = 'もう一度';
    n = 0; score = 0;
  };
  $('next').addEventListener('click', next);

  for (const b of $('dirs').querySelectorAll('button')) {
    b.addEventListener('click', () => {
      reverse = b.dataset.rev === '1';
      for (const x of $('dirs').querySelectorAll('button')) x.classList.toggle('on', x === b);
      n = 0; score = 0;
      ask();
    });
  }
}
