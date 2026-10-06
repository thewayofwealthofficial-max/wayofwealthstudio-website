// How much of a draft is Joel's own words (0 to 1): the share of the draft's words that sit in a 3-word run found in
// his passages. Spoken filler is taken out of both sides first, so tidying it doesn't count against him.
// Joel, 5 Oct 2026: the old check passed a draft holding ONE 5-word phrase of his.

const norm = (s) => String(s).toLowerCase().replace(/[^a-z0-9£$€% ]+/g, ' ').replace(/\s+/g, ' ').trim();
const FILLER = /\b(um+|uh+|erm|you know|i mean|sort of|kind of|so basically|basically|like|yeah|okay|ok|right)\b/g;

export function joelShare(draft, source) {
  const toks = (s) => norm(s).replace(FILLER, ' ').split(' ').filter(Boolean);
  const b = toks(draft), p = ` ${toks(source).join(' ')} `;
  if (b.length < 3) return 0;
  const hit = new Array(b.length).fill(false);
  for (let i = 0; i + 3 <= b.length; i++) if (p.includes(` ${b.slice(i, i + 3).join(' ')} `)) hit[i] = hit[i + 1] = hit[i + 2] = true;
  return hit.filter(Boolean).length / b.length;
}
