// Joel's own words, pulled from his recent Fathom call recordings.
//
// PRIVACY: this repo and its Action logs are PUBLIC. Nothing from here may be written to a
// file or printed to the log. Passages live in memory only and go to the model; the safety
// check then blocks any draft that contains a client's name.

const API = 'https://api.fathom.ai/external/v1';
const JOEL = /^joel\b/i;

async function get(key, path) {
  const res = await fetch(API + path, { headers: { 'X-Api-Key': key } });
  if (!res.ok) throw new Error(`Fathom ${res.status}`);
  return res.json();
}

// Consecutive Joel segments joined into one passage.
function joelPassages(transcript) {
  const out = [];
  let cur = null;
  for (const seg of transcript || []) {
    const isJoel = JOEL.test(seg?.speaker?.display_name || '');
    if (isJoel) {
      if (!cur) cur = { start: seg.timestamp, text: '' };
      cur.text += (cur.text ? ' ' : '') + String(seg.text || '').trim();
    } else if (cur) {
      out.push(cur);
      cur = null;
    }
  }
  if (cur) out.push(cur);
  return out;
}

// Rough "is this a story?" score: first person, past tense, a moment.
function storyScore(t) {
  const hits = (t.match(/\b(I remember|when I was|I was|I had|I used to|my (?:mum|dad|mom|family|partner|friend)|years ago|back then|I lost|I realised|I realized|I felt|one day)\b/gi) || []).length;
  return hits;
}

/**
 * Returns { passages: [{date, text}], names: Set<string> } from the last `days` of calls.
 * `names` holds every non-Joel speaker and invitee first name, so the safety check can block them.
 */
export async function recentJoelWords({ key, days = 21, maxPassages = 12 }) {
  if (!key) return { passages: [], names: new Set() };
  const since = new Date(Date.now() - days * 86400e3).toISOString();
  const passages = [];
  const names = new Set();
  let cursor = null;
  for (let page = 0; page < 5; page++) {
    const q = `?include_transcript=true&created_after=${encodeURIComponent(since)}${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ''}`;
    const j = await get(key, '/meetings' + q);
    for (const m of j.items || []) {
      const date = String(m.recording_start_time || m.created_at || '').slice(0, 10);
      for (const seg of m.transcript || []) {
        const n = seg?.speaker?.display_name || '';
        if (n && !JOEL.test(n)) names.add(n.split(/\s+/)[0]);
      }
      for (const inv of m.calendar_invitees || []) {
        const n = String(inv?.name || '').split(/\s+/)[0];
        if (n && !JOEL.test(n)) names.add(n);
      }
      for (const p of joelPassages(m.transcript)) {
        const words = p.text.split(/\s+/).length;
        if (words < 70 || words > 450) continue;
        passages.push({ date, text: p.text, score: storyScore(p.text) });
      }
    }
    cursor = j.next_cursor;
    if (!cursor) break;
  }
  passages.sort((a, b) => b.score - a.score);
  return {
    passages: passages.filter((p) => p.score > 0).slice(0, maxPassages).map(({ date, text }) => ({ date, text })),
    names: new Set([...names].filter((n) => n.length > 2)),
  };
}
