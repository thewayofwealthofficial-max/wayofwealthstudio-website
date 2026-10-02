#!/usr/bin/env node
// The Friday "big swing" (Joel, 28 Sep 2026): every Friday Fred sends 5 practitioner-training organisations
// (yoga teacher trainings, breathwork certifications, reiki/energy trainings, retreat centres and studios that run
// teacher programmes), each with a ready pitch offering a free talk for their trainees, plus one bold idea.
// Since 1 Oct 2026 (Joel): also 3 podcasts that coaches and wellness practitioners listen to, each with a guest pitch.
// Joel sends them himself. Nothing is sent automatically. Kept out of the prospecting cockpit (its "do not touch" rule).
//
// Anti-invention: an organisation is kept only if its website came back in a REAL web search result, and the site
// opens. Contact routes come only from the organisation's own pages (mailto links / a contact page). Pitches use
// only Joel's fixed facts and what the organisation's own site says.
//
// ENV: ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID. DRY_RUN=1 prints instead of sending.

import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { joelVoice, leaksName } from './voice/joel-voice.mjs';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const STATE = join(ROOT, 'scripts', 'state', 'b2b', 'suggested.json');
const DRY = process.env.DRY_RUN === '1';
const { ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID } = process.env;
const MODEL = process.env.CLAUDE_MODEL || 'claude-sonnet-4-6';
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36';

// Joel's fixed facts for B2B pitches (same source as the emails: scripts/daily-email/voice.mjs JOEL_FACTS).
const JOEL = `Joel Ezekiel, founder of Way of Wealth (wayofwealthcoaching.com). MSc Behavioural Economics, Qualified Financial Planner. He coaches self-employed people on the behaviour side of money: charging for their work without guilt, and keeping what comes in (separate pots, a steady wage from lumpy income). He is a planner, not an adviser: no investment, pension, tax or product advice.`;
const PODCAST_OFFER = `to come on their podcast as a guest and talk about "The money side of your practice" (charging for your work without the guilt, and keeping what comes in). No selling to their listeners.`;
const OFFER = `a free 45-minute talk for their trainees or members: "The money side of your practice" (charging for your work without the guilt, and keeping what comes in). Online (in person only if they are in the UK). No selling on the day.`;

// One bold idea a week, in turn. Joel approved the concept on 28 Sep; these are the ideas he was shown.
const BIG_IDEAS = [
  'Record a 60-second personal video for one founder (their name, their training, your talk offer). Send it by email or DM instead of text.',
  'Offer to run the money session INSIDE their next training, free, as a bonus module for their trainees.',
  'Send one founder a one-page "money guide for your graduates" with their logo on it, as a gift, no ask.',
  'Offer a joint Instagram live with one teacher: "the money side of running retreats".',
];

// Where to look. Global Western audience (never UK-only).
const SEARCHES = [
  'yoga teacher training 200 hour school', 'breathwork facilitator certification training', 'reiki practitioner training course',
  'retreat centre yoga teacher training', 'somatic practitioner certification', 'sound healing practitioner training',
  'holistic therapist diploma training school', 'meditation teacher training certification',
];

// Podcasts the ICP listens to (Joel, 1 Oct 2026): running a coaching, wellness or private-practice business.
const PODCAST_SEARCHES = [
  'podcast for coaches growing their coaching business', 'yoga teacher business podcast', 'wellness business podcast for practitioners',
  'therapist private practice podcast', 'holistic practitioner business podcast', 'podcast for healers and energy workers business',
];

async function claude(body) {
  const r = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'x-api-key': ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
    body: JSON.stringify({ model: MODEL, ...body }),
  });
  if (!r.ok) throw new Error(`Anthropic ${r.status}: ${(await r.text()).slice(0, 200)}`);
  return r.json();
}
function firstJson(text) {
  const s = text.indexOf('{'); let depth = 0, inStr = false, esc = false;
  for (let i = s; s >= 0 && i < text.length; i++) {
    const c = text[i];
    if (inStr) { if (esc) esc = false; else if (c === '\\') esc = true; else if (c === '"') inStr = false; continue; }
    if (c === '"') inStr = true; else if (c === '{') depth++; else if (c === '}' && --depth === 0) return JSON.parse(text.slice(s, i + 1));
  }
  throw new Error('no JSON in reply');
}
const host = (u) => { try { return new URL(u).hostname.replace(/^www\./, ''); } catch { return ''; } };

async function findOrgs(exclude) {
  const j = await claude({
    max_tokens: 4000,
    tools: [{ type: 'web_search_20250305', name: 'web_search', max_uses: 8 }],
    messages: [{ role: 'user', content: `Find independent organisations that TRAIN wellness practitioners: yoga teacher training schools, breathwork certifications, reiki or energy-healing trainings, somatic or sound-healing certifications, meditation teacher trainings, and retreat centres or studios that run teacher programmes. Countries: UK, Ireland, US, Canada, Australia, New Zealand, South Africa, Europe. Run web searches such as:\n${SEARCHES.map((s) => '- ' + s).join('\n')}\n\nSkip: big chains and franchises, directories and listing sites (Yoga Alliance, Retreat Guru, BookYogaRetreats and similar), marketplaces, and these domains: ${exclude.slice(-150).join(', ') || 'none'}.\nPick 10. Use ONLY websites that appeared in your search results; never guess a URL.\nOutput only JSON: {"orgs":[{"name":"","url":"homepage URL from the results","type":"yoga teacher training | breathwork certification | reiki training | somatic | sound healing | meditation | retreat centre | other","country":"","why":"one line from what the result says, e.g. runs a 200-hour teacher training"}]}` }],
  });
  const seen = new Set((j.content || []).filter((b) => b.type === 'web_search_tool_result').flatMap((b) => (Array.isArray(b.content) ? b.content : []).map((x) => host(x.url || ''))));
  const text = (j.content || []).filter((b) => b.type === 'text').map((b) => b.text).join('\n');
  return (firstJson(text).orgs || []).filter((o) => o.url && seen.has(host(o.url)) && !exclude.includes(host(o.url)));
}

// Contact route from the organisation's own pages only.
async function contactFor(url) {
  const out = { email: '', contactPage: '' };
  const get = async (u) => { const r = await fetch(u, { headers: { 'User-Agent': UA }, redirect: 'follow', signal: AbortSignal.timeout(15000) }); return r.ok ? r.text() : ''; };
  const home = await get(url);
  if (!home) return null;
  const pick = (h) => (h.match(/mailto:([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})/i) || [])[1] || '';
  out.email = pick(home);
  const cp = (home.match(/href="([^"]*contact[^"]*)"/i) || [])[1];
  if (cp) {
    out.contactPage = new URL(cp, url).toString();
    if (!out.email) { try { out.email = pick(await get(out.contactPage)); } catch { /* page only */ } }
  }
  out.about = home.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/gi, ' ').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').slice(0, 2500);
  return out;
}

async function findPodcasts(exclude) {
  const j = await claude({
    max_tokens: 4000,
    tools: [{ type: 'web_search_20250305', name: 'web_search', max_uses: 6 }],
    messages: [{ role: 'user', content: `Find independent podcasts whose listeners are coaches or wellness practitioners running their own business: coaching business podcasts, yoga or wellness business podcasts, therapist private-practice podcasts, holistic or healer business podcasts. Countries: UK, Ireland, US, Canada, Australia, New Zealand, South Africa, Europe. Run web searches such as:\n${PODCAST_SEARCHES.map((s) => '- ' + s).join('\n')}\n\nSkip: celebrity shows, general personal-finance shows, big media networks, and these domains: ${exclude.slice(-150).join(', ') || 'none'}. Use the podcast's OWN website, not Apple or Spotify pages.\nPick 8. Use ONLY websites that appeared in your search results; never guess a URL.\nOutput only JSON: {"orgs":[{"name":"podcast name","url":"the podcast's own website from the results","country":"","why":"one line from what the result says, e.g. weekly show for yoga teachers running studios"}]}` }],
  });
  const seen = new Set((j.content || []).filter((b) => b.type === 'web_search_tool_result').flatMap((b) => (Array.isArray(b.content) ? b.content : []).map((x) => host(x.url || ''))));
  const text = (j.content || []).filter((b) => b.type === 'text').map((b) => b.text).join('\n');
  const platform = /(^|\.)(apple\.com|spotify\.com|youtube\.com|amazon\.\w+|podchaser\.com|listennotes\.com)$/;
  return (firstJson(text).orgs || []).filter((o) => o.url && seen.has(host(o.url)) && !platform.test(host(o.url)) && !exclude.includes(host(o.url)));
}

async function pitchFor(org, voice) {
  const j = await claude({
    max_tokens: 700,
    system: `You write ONE short outreach email from Joel to the ${org.type === 'podcast' ? 'host of a podcast' : 'founder or team of a practitioner-training organisation'}.\nWHO JOEL IS: ${JOEL}\nTHE OFFER: ${org.type === 'podcast' ? PODCAST_OFFER : OFFER}\nRULES: 90 to 130 words. Plain, warm, British spelling, no em dashes, short sentences. Open with one specific, TRUE detail from their own website text below (never invent one). Say who Joel is in one line. Make the offer. End with one easy question (e.g. would this be useful for your next intake? or, for a podcast, would this fit your show?).Describe Joel ONLY as "a Qualified Financial Planner with an MSc in Behavioural Economics who coaches self-employed people on the behaviour side of money"; NEVER say or imply he works with, specialises in, or has coached practitioners, healers, teachers or facilitators. Never guess or interpret anything about their students, listeners, business or graduates (no "that suggests", no "many new teachers struggle", no "exactly where X gets complicated"); only restate what their own site says. Never say or imply Joel has listened to, watched, read, enjoyed or loved anything of theirs (he has not); say "your site says" instead. No statistics, no client results, no claims about what "most" or "many" people feel, no price, no links. No dashes of any kind, in the subject or the body. Sign off "Joel". Output only JSON {"subject":"...","body":"..."}.${voice.block}\nThis is a first email to a stranger, so keep his voice but go light on "like" and "you know". The rules above still win.`,
    messages: [{ role: 'user', content: `ORGANISATION: ${org.name} (${org.type}, ${org.country})\nWHY THEY FIT: ${org.why}\nTHEIR OWN WEBSITE TEXT:\n${org.about}` }],
  });
  const p = firstJson((j.content || []).map((b) => b.text || '').join(''));
  p.body = String(p.body || '').replace(/\s*[—–]\s*/g, ', ');
  p.subject = String(p.subject || '').replace(/\s*[—–-]\s+/g, ': ');
  // Hard checks: Joel has not coached practitioners yet, and no guessed claims about their people.
  if (/\b(?:work|works|working|specialis\w*|coach(?:es)?)\b[^.\n]{0,40}\b(?:practitioners?|healers?|teachers?|facilitators?)\b/i.test(p.body)) throw new Error('pitch implies Joel works with practitioners');
  if (/\bI(?:'ve| have)?\s+(?:just\s+)?(?:listened|watched|read|heard|enjoyed|loved|been listening|been following)\b/i.test(p.body)) throw new Error('pitch claims Joel consumed their content');
  if (/\b(?:many|most)\s+(?:new|newly)?\s*\w*\s*(?:teachers|facilitators|practitioners|graduates|students|listeners)\b|that suggests/i.test(p.body)) throw new Error('pitch makes a guessed claim');
  if (leaksName(`${p.subject} ${p.body}`, [...voice.names].filter((n) => !org.about?.includes(n)))) throw new Error("pitch names someone from Joel's private calls");
  return p;
}

async function telegram(text) {
  if (DRY) { console.log(text + '\n'); return; }
  for (let i = 0; i < text.length; i += 3900) {
    const r = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ chat_id: TELEGRAM_CHAT_ID, text: text.slice(i, i + 3900), disable_web_page_preview: true }),
    });
    if (!r.ok) throw new Error(`Telegram ${r.status}`);
  }
}

async function main() {
  if (!ANTHROPIC_API_KEY) throw new Error('ANTHROPIC_API_KEY not set');
  let state = [];
  try { state = JSON.parse(await readFile(STATE, 'utf8')); } catch { /* first run */ }
  // Joel's voice from his Fathom calls (scripts/voice/joel-voice.mjs), for every pitch (2 Oct 2026).
  const voice = await joelVoice();
  const candidates = await findOrgs(state.map((s) => s.domain));
  console.log(`${candidates.length} organisations found in real search results.`);
  const picked = [];
  for (const o of candidates) {
    if (picked.length === 5) break;
    try {
      const c = await contactFor(o.url);
      if (!c || (!c.email && !c.contactPage)) continue; // no public way to reach them
      const org = { ...o, ...c };
      org.pitch = await pitchFor(org, voice);
      picked.push(org);
    } catch { /* one bad site never stops the run */ }
  }
  console.log(`${picked.length} kept (site opens and has a public contact route).`);

  const pods = [];
  try {
    for (const o of await findPodcasts(state.map((s) => s.domain))) {
      if (pods.length === 3) break;
      try {
        const c = await contactFor(o.url);
        if (!c || (!c.email && !c.contactPage)) continue; // no public way to reach them
        const pod = { ...o, ...c, type: 'podcast' };
        pod.pitch = await pitchFor(pod, voice);
        pods.push(pod);
      } catch { /* one bad site never stops the run */ }
    }
  } catch (e) { console.error('Podcast search failed:', e.message); }
  console.log(`${pods.length} podcasts kept.`);
  if (!picked.length && !pods.length) { await telegram('🎯 Friday big swing: no suitable organisations or podcasts found this week. Nothing to send.'); return; }

  const week = Math.floor(Date.now() / (7 * 864e5));
  const idea = BIG_IDEAS[week % BIG_IDEAS.length];
  await telegram(`🎯 FRIDAY BIG SWING\nOne yes = a room of your ideal buyers. Pick one or two and send them yourself.\n\n💡 Bold idea this week: ${idea}`);
  for (const [i, o] of picked.entries()) {
    await telegram(`${i + 1}. ${o.name} (${o.type}, ${o.country})\nWhy: ${o.why}\nWebsite: ${o.url}\nContact: ${o.email || o.contactPage}\n\nSubject: ${o.pitch.subject}\n\n${o.pitch.body}`);
  }
  if (pods.length) await telegram('🎙️ PODCASTS: ask to come on as a guest');
  for (const [i, o] of pods.entries()) {
    await telegram(`P${i + 1}. ${o.name} (podcast, ${o.country})\nWhy: ${o.why}\nWebsite: ${o.url}\nContact: ${o.email || o.contactPage}\n\nSubject: ${o.pitch.subject}\n\n${o.pitch.body}`);
  }

  if (!DRY) {
    const date = new Date().toISOString().slice(0, 10);
    state.push(...[...picked, ...pods].map((o) => ({ date, domain: host(o.url), name: o.name, type: o.type, country: o.country })));
    await mkdir(dirname(STATE), { recursive: true });
    await writeFile(STATE, JSON.stringify(state, null, 2) + '\n');
  }
}

main().catch(async (e) => {
  console.error('FATAL:', e.message);
  if (!DRY && TELEGRAM_BOT_TOKEN) { try { await telegram(`❌ Friday big swing failed: ${e.message.slice(0, 200)}`); } catch {} }
  process.exit(1);
});
