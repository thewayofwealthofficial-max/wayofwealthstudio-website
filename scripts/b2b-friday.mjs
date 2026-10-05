#!/usr/bin/env node
// The Friday "big swing" (Joel, 28 Sep 2026). Repointed 5 Oct 2026 from wellness trainings to small business
// introducers (Joel: "small business groups, anything that could be regarded as an introducer... whether that's
// small businesses that can refer me and vice versa, or businesses that would hire me for their employees").
// Every Friday Fred sends:
//   - 5 REFERRAL PARTNERS: accountants and bookkeepers for sole traders and small businesses, small business
//     networks (chambers of commerce, BNI-style chapters, local business networks, coworking spaces), and business
//     coaches or consultants whose clients need the money side. Offer: a two-way referral, plus a free talk.
//   - 2 EMPLOYERS: small and mid-size businesses that might bring Joel in for staff financial wellbeing.
//   - 3 SHOWS: small business podcasts and newsletters, each with a guest pitch.
//   - one bold idea.
// Joel sends them himself. Nothing is sent automatically. Kept out of the prospecting cockpit (its "do not touch" rule).
//
// Anti-invention: an organisation is kept only if its website came back in a REAL web search result, and the site
// opens. Contact routes come only from the organisation's own pages (mailto links / a contact page). Pitches use
// only Joel's fixed facts and what the organisation's own site says. Joel has no partnerships and has not run
// staff workshops yet: the hard checks block any pitch that implies otherwise.
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

// Joel's fixed facts for B2B pitches (same source as the emails: scripts/daily-email/voice.mjs JOEL_FACTS;
// Cash Flow Plan = programme session 10). Audience per BRAND.md §1 from 2026-10-05.
const JOEL = `Joel Ezekiel, founder of Way of Wealth (wayofwealthcoaching.com). MSc Behavioural Economics, Qualified Financial Planner. He coaches self-employed people on the behaviour side of money: why money stays stressful on a decent income, and simple systems that stick (separate pots, a tax pot, a slow-month buffer, a steady wage from lumpy income). His 12-week 1:1 programme, the Money Story Method, builds each client a Cash Flow Plan. He is a planner, not an adviser: education and coaching only, no investment, pension, tax or product advice. He explains how tax works and teaches setting money aside for it, but never structures anyone's tax.`;
const TALK = `"Paying yourself when the money comes in lumps": why money stays stressful on a decent income, and simple systems that stick (a tax pot, a buffer, a steady wage). Education only, no selling on the day.`;
const OFFERS = {
  accountant: `a two-way referral: Joel handles the behaviour and the Cash Flow Plan, they handle the tax and the books, so each can send the other clients who need the other half. Also, if useful, a free 45-minute talk for their clients: ${TALK} Online (in person only if they are in the UK).`,
  network: `a free 45-minute talk for their members: ${TALK} Online (in person only if they are in the UK).`,
  coach: `a two-way referral: they handle the business side, Joel handles the money behaviour and the Cash Flow Plan, so each can send the other clients who need the other half. Also, if useful, a free 45-minute talk for their clients: ${TALK} Online.`,
  employer: `a free 45-minute online talk for their team on the behaviour side of money: why money can feel stressful even on a decent wage, and simple systems that stick (separate pots, a buffer, a plan for where each payday goes). Education only: no financial advice, no products, no selling to staff. If it is useful, he can follow up with workshops or 1:1 sessions for staff.`,
  podcast: `to come on their podcast as a guest and talk about ${TALK.replace(' Education only, no selling on the day.', '')} No selling to their listeners.`,
  newsletter: `to write one free guest piece for their newsletter on ${TALK.replace(' Education only, no selling on the day.', '')} No selling to their readers.`,
};
const kindOf = (o) => (o.type === 'podcast' || o.type === 'newsletter' || o.type === 'employer' ? o.type
  : /account|bookkeep/i.test(o.type) ? 'accountant' : /coach|consult/i.test(o.type) ? 'coach' : 'network');
const QUESTION = {
  accountant: 'would a quick call to see if this works both ways be useful?', coach: 'would a quick call to see if this works both ways be useful?',
  network: 'would this be useful for your members?', employer: 'would this be useful for your team?',
  podcast: 'would this fit your show?', newsletter: 'would this fit your newsletter?',
};
const RECIPIENT = {
  accountant: 'partner or owner of an accountancy or bookkeeping practice', network: 'organiser of a small business network or coworking space',
  coach: 'a business coach or consultant', employer: 'founder or people/HR lead of a small or mid-size business',
  podcast: 'host of a podcast', newsletter: 'writer of a newsletter',
};

// One bold idea a week, in turn. Same four moves Joel approved on 28 Sep, repointed at small business introducers.
const BIG_IDEAS = [
  'Record a 60-second personal video for one accountant or founder (their name, their firm, your offer). Send it by email or LinkedIn instead of text.',
  'Offer to run the money talk free at one network\'s next members\' meeting or one firm\'s next client event.',
  'Send one accountant a one-page "paying yourself and setting tax aside" guide for their clients, with their logo on it, as a gift, no ask.',
  'Offer a joint LinkedIn live with one accountant or bookkeeper: "the books side and the behaviour side of the tax bill".',
];

// Where to look. UK first, global Western allowed (never UK-only).
const SEARCHES = [
  'accountant for sole traders and small businesses UK', 'bookkeeper for self-employed and freelancers', 'small business accountants for creatives and freelancers',
  'chamber of commerce small business members events', 'local business networking group breakfast meeting', 'coworking space for freelancers and small businesses community events',
  'business coach for small business owners', 'small business consultant for service businesses',
];
const EMPLOYER_SEARCHES = [
  'small business employee wellbeing programme UK', 'SME staff wellbeing financial wellbeing benefits', 'independent company careers page employee wellbeing benefits UK',
  'B Corp small business employee benefits', 'small company best places to work UK wellbeing',
];
// Shows small business owners listen to or read.
const SHOW_SEARCHES = [
  'small business podcast UK', 'podcast for freelancers and self-employed', 'podcast for small business owners money and growth',
  'newsletter for freelancers and small business owners', 'sole trader small business newsletter UK',
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

const COUNTRIES = 'UK first (aim for at least half from the UK), then Ireland, US, Canada, Australia, New Zealand, South Africa, Europe';

// One search pass: Claude runs real web searches; only sites that appeared in the results are kept.
async function search(prompt, exclude, maxUses) {
  const j = await claude({
    max_tokens: 4000,
    tools: [{ type: 'web_search_20250305', name: 'web_search', max_uses: maxUses }],
    messages: [{ role: 'user', content: `${prompt}\nSkip these domains: ${exclude.slice(-150).join(', ') || 'none'}.\nUse ONLY websites that appeared in your search results; never guess a URL.` }],
  });
  const seen = new Set((j.content || []).filter((b) => b.type === 'web_search_tool_result').flatMap((b) => (Array.isArray(b.content) ? b.content : []).map((x) => host(x.url || ''))));
  const text = (j.content || []).filter((b) => b.type === 'text').map((b) => b.text).join('\n');
  const platform = /(^|\.)(apple\.com|spotify\.com|youtube\.com|amazon\.\w+|podchaser\.com|listennotes\.com|linkedin\.com|facebook\.com|instagram\.com|yell\.com|yelp\.\w+|trustpilot\.com|unbiased\.co\.uk|glassdoor\.\w+|indeed\.\w+|substack\.com)$/;
  return (firstJson(text).orgs || []).filter((o) => o.url && seen.has(host(o.url)) && !platform.test(host(o.url)) && !exclude.includes(host(o.url)));
}

// Referral partners: people whose clients or members are small business owners.
const findPartners = (exclude) => search(`Find independent organisations that could refer small business owners and self-employed people to a money coach, and that he could refer clients back to: accountancy and bookkeeping practices that serve sole traders, freelancers and small businesses; small business networks (chambers of commerce, BNI-style chapters, local business networking groups, coworking spaces with a member community); and independent business coaches or consultants for small service businesses. Countries: ${COUNTRIES}. Run web searches such as:\n${SEARCHES.map((s) => '- ' + s).join('\n')}\n\nSkip: big national or global firms and franchises (Big Four, top-20 accountancy firms, national chains), directories and listing sites, marketplaces, financial advisers and wealth managers.\nPick 10, a mix of the three kinds.\nOutput only JSON: {"orgs":[{"name":"","url":"homepage URL from the results","type":"accountant | bookkeeper | chamber of commerce | business network | coworking space | business coach | consultant","country":"","why":"one line from what the result says, e.g. accountants for sole traders and limited companies"}]}`, exclude, 8);

// Employers: small and mid-size businesses that might bring Joel in for staff financial wellbeing.
const findEmployers = (exclude) => search(`Find independent small and mid-size businesses (roughly 10 to 250 staff) whose own website shows they invest in staff wellbeing or benefits, so they might bring in a money coach for a staff talk. Countries: ${COUNTRIES}. Run web searches such as:\n${EMPLOYER_SEARCHES.map((s) => '- ' + s).join('\n')}\n\nSkip: big corporates and household names, recruitment agencies, wellbeing vendors and benefits platforms, HR software companies, financial services firms, directories and listing sites.\nPick 6.\nOutput only JSON: {"orgs":[{"name":"","url":"homepage URL from the results","type":"employer","country":"","why":"one line from what the result says, e.g. design agency with a staff wellbeing page"}]}`, exclude, 6);

// Shows: small business podcasts and newsletters.
const findShows = (exclude) => search(`Find independent podcasts and newsletters whose audience is small business owners, freelancers or self-employed people. Countries: ${COUNTRIES}. Run web searches such as:\n${SHOW_SEARCHES.map((s) => '- ' + s).join('\n')}\n\nSkip: celebrity shows, general personal-finance or investing shows, big media networks. Use the show's OWN website, not Apple, Spotify or Substack pages.\nPick 8.\nOutput only JSON: {"orgs":[{"name":"","url":"the show's own website from the results","type":"podcast | newsletter","country":"","why":"one line from what the result says, e.g. weekly show for UK freelancers"}]}`, exclude, 6);

// Hard checks on every pitch. A pitch that breaks one is dropped, never sent to Joel.
function pitchProblem(p, voice, org) {
  const t = `${p.subject}\n${p.body}`;
  // Joel has not coached practitioners (kept from the wellness version), and has no partners, staff workshops or talks to point to yet.
  if (/\b(?:work|works|working|specialis\w*|coach(?:es)?)\b[^.\n]{0,40}\b(?:practitioners?|healers?|teachers?|facilitators?)\b/i.test(t)) return 'pitch implies Joel works with practitioners';
  if (/\bI(?:'ve| have)\s+(?:already\s+|also\s+|recently\s+)?(?:worked|partnered|run|ran|delivered|spoken|given|trained|helped|coached|referred)\b/i.test(t)) return 'pitch claims a track record';
  if (/\b(?:other|several|many|a few)\s+(?:accountants?|bookkeepers?|firms?|practices|companies|businesses|employers|networks|chambers|coaches)\b|\b(?:my|our)\s+(?:partners?|partner firms?|referral partners?)\b|\bpartnered with\b/i.test(t)) return 'pitch implies existing partners';
  if (/\bI(?:'ve| have)?\s+(?:just\s+)?(?:listened|watched|read|heard|enjoyed|loved|been listening|been following|been reading)\b/i.test(t)) return 'pitch claims Joel consumed their content';
  if (/\b(?:many|most|lots of|so many)\s+(?:of\s+)?(?:your\s+)?(?:new\s+)?\w*\s*(?:clients|members|employees|staff|owners|businesses|freelancers|listeners|readers|graduates|students)\b|that suggests|\b(?:comes up|crops up)\s+(?:a lot|all the time|often|again and again)|\bI\s+(?:hear|see)\s+(?:this|it)\s+(?:a lot|all the time|often)/i.test(t)) return 'pitch makes a guessed claim';
  // Planner, not adviser (TEACHING_SCOPE.md): no advice wording unless denied, no tax saving, no products, no figures.
  for (const m of t.matchAll(/\b(?:financial\s+)?advi(?:ce|ser|sor|se|sing)\b/gi)) if (!/\b(?:not|no|never|without)\b[^.\n]{0,25}$/i.test(t.slice(Math.max(0, m.index - 40), m.index))) return 'pitch uses advice wording';
  if (/\b(?:save|saving|reduce|cut|lower|less)\b[^.\n]{0,20}\btax(?:es)?\b|\btax[- ](?:efficien\w*|planning|saving|relief|loophole)|\bpay less tax\b/i.test(t)) return 'pitch promises tax saving or tax planning';
  if (/\b(?:ISA|LISA|SIPP|401k|pensions?|invest\w*|mortgages?|insurance|funds?|shares)\b/i.test(t)) return 'pitch names a product or investment';
  if (/\d/.test(t.replace(/\b12[- ]week\b|\b45[- ]minute\b|\b1:1\b/gi, ''))) return 'pitch contains a figure';
  if (!/\bJoel\s*$/.test(String(p.body).trim())) return 'pitch does not sign off "Joel"';
  if (leaksName(t, [...voice.names].filter((n) => !org.about?.includes(n)))) return "pitch names someone from Joel's private calls";
  return null;
}

async function pitchFor(org, voice) {
  const kind = kindOf(org);
  const j = await claude({
    max_tokens: 700,
    system: `You write ONE short outreach email from Joel to the ${RECIPIENT[kind]}.\nWHO JOEL IS: ${JOEL}\nTHE OFFER: ${OFFERS[kind]}\nRULES: 90 to 130 words. Plain, warm, British spelling, no em dashes, short sentences. Open with one specific, TRUE detail from their own website text below (never invent one). Say who Joel is in one line. Make the offer. End with one easy question: ${QUESTION[kind]} Describe Joel ONLY as "a Qualified Financial Planner with an MSc in Behavioural Economics who coaches self-employed people on the behaviour side of money"; you may add that his 12-week 1:1 programme builds each client a Cash Flow Plan. NEVER say or imply he has partners, a referral network, other firms he works with, staff workshops or talks he has already given, or that he works with, specialises in, or has coached practitioners, healers, teachers or facilitators. Never guess or interpret anything about their clients, members, staff, listeners or business (no "that suggests", no "many of your clients struggle"); only restate what their own site says. Never say or imply Joel has listened to, watched, read, enjoyed or loved anything of theirs (he has not); say "your site says" instead. Planner, not adviser: never use the words advice or adviser about what Joel does, never mention saving or reducing tax, never name a product, pension or investment. No statistics, no numbers or digits (not even ones from their site), no client results, no claims about what "most" or "many" people feel, no price, no links. No dashes of any kind, in the subject or the body. Sign off "Joel". Output only JSON {"subject":"...","body":"..."}.${voice.block}\nThis is a first email to a stranger, so keep his voice but go light on "like" and "you know". The rules above still win.`,
    messages: [{ role: 'user', content: `ORGANISATION: ${org.name} (${org.type}, ${org.country})\nWHY THEY FIT: ${org.why}\nTHEIR OWN WEBSITE TEXT:\n${org.about}` }],
  });
  const p = firstJson((j.content || []).map((b) => b.text || '').join(''));
  p.body = String(p.body || '').replace(/\s*[—–]\s*/g, ', ');
  p.subject = String(p.subject || '').replace(/\s*[—–-]\s+/g, ': ');
  const bad = pitchProblem(p, voice, org);
  if (bad) throw new Error(bad);
  return p;
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
  const done = state.map((s) => s.domain);

  // Keep up to n from one search: the site opens, has a public contact route, and the pitch passes every hard check.
  async function keep(label, find, n, extra = {}) {
    const out = [];
    try {
      const found = await find(done);
      console.log(`${label}: ${found.length} found in real search results.`);
      for (const o of found) {
        if (out.length === n) break;
        try {
          const c = await contactFor(o.url);
          if (!c || (!c.email && !c.contactPage)) continue; // no public way to reach them
          const org = { ...o, ...c, ...extra };
          org.pitch = await pitchFor(org, voice);
          out.push(org);
          done.push(host(o.url));
        } catch (e) { console.log(`  dropped ${host(o.url)}: ${String(e.message).slice(0, 120)}`); } // one bad site never stops the run
      }
    } catch (e) { console.error(`${label} search failed:`, e.message); }
    console.log(`${label}: ${out.length} kept.`);
    return out;
  }
  const partners = await keep('Referral partners', findPartners, 5);
  const employers = await keep('Employers', findEmployers, 2, { type: 'employer' });
  const shows = await keep('Podcasts and newsletters', findShows, 3);
  if (!partners.length && !employers.length && !shows.length) { await telegram('🎯 Friday big swing: no suitable partners, employers or shows found this week. Nothing to send.'); return; }

  const week = Math.floor(Date.now() / (7 * 864e5));
  const idea = BIG_IDEAS[week % BIG_IDEAS.length];
  const card = (tag, o) => `${tag}. ${o.name} (${o.type}, ${o.country})\nWhy: ${o.why}\nWebsite: ${o.url}\nContact: ${o.email || o.contactPage}\n\nSubject: ${o.pitch.subject}\n\n${o.pitch.body}`;
  await telegram(`🎯 FRIDAY BIG SWING\nOne yes = a steady way in to small business owners. Pick one or two and send them yourself.\n\n💡 Bold idea this week: ${idea}`);
  if (partners.length) await telegram('🤝 REFERRAL PARTNERS: two-way referral or a free talk');
  for (const [i, o] of partners.entries()) await telegram(card(i + 1, o));
  if (employers.length) await telegram('🏢 EMPLOYERS: a free talk for their staff');
  for (const [i, o] of employers.entries()) await telegram(card(`E${i + 1}`, o));
  if (shows.length) await telegram('🎙️ PODCASTS AND NEWSLETTERS: ask to come on as a guest');
  for (const [i, o] of shows.entries()) await telegram(card(`P${i + 1}`, o));

  if (!DRY) {
    const date = new Date().toISOString().slice(0, 10);
    state.push(...[...partners, ...employers, ...shows].map((o) => ({ date, domain: host(o.url), name: o.name, type: o.type, country: o.country })));
    await mkdir(dirname(STATE), { recursive: true });
    await writeFile(STATE, JSON.stringify(state, null, 2) + '\n');
  }
}

main().catch(async (e) => {
  console.error('FATAL:', e.message);
  if (!DRY && TELEGRAM_BOT_TOKEN) { try { await telegram(`❌ Friday big swing failed: ${e.message.slice(0, 200)}`); } catch {} }
  process.exit(1);
});
