// Automatic safety checks. Nothing goes to the list unless it passes every check here.
// A draft that fails is regenerated with the problems fed back; after three failures the
// send is skipped and Joel is told why.

// AI tells and hype only. Joel lifted vocabulary bans on 2026-09-06; spiritual words are
// allowed as the reader's own words (the prompt forbids claiming manifesting works).
const BANNED = [
  'hustle', 'grind', 'side hustle', 'boss babe', 'money magnet', 'passive income', 'toxic positivity',
  'growth hack', 'you got this', 'level up', 'journey', 'breakthrough', 'unlock', 'heal your money story',
  'delve', 'unpack', 'tapestry', 'holistic', 'level 4', 'game changer', 'game-changer',
];
const SPAMMY = ['act now', 'limited time', 'click here', 'free money', 'urgent', '100%', '!!'];
const RESEARCH_WORDS = /\b(studies show|study shows|research shows|research says|according to|survey|scientists?|a recent study)\b/i;

const WORDS = { letter: [150, 340], post: [150, 340], fridays: [330, 640] };

export function clean(s) {
  return String(s || '').replace(/\s*—\s*/g, ', ').replace(/\s*–\s*/g, ', ').replace(/[ \t]+\n/g, '\n').trim();
}

const norm = (s) => String(s).toLowerCase().replace(/[^a-z0-9£$€% ]+/g, ' ').replace(/\s+/g, ' ').trim();

// Any run of 8 words copied from the competitor's email = copying, not shaping.
function copiedRun(body, shapeText) {
  if (!shapeText) return null;
  const b = norm(body).split(' ');
  const s = ` ${norm(shapeText)} `;
  for (let i = 0; i + 8 <= b.length; i++) {
    const run = b.slice(i, i + 8).join(' ');
    if (s.includes(` ${run} `)) return run;
  }
  return null;
}

export function checkDraft({ subject, preview, body_plain }, { type, allowedLinks = [], sourceText = '', shapeText = '', blockedNames = new Set() } = {}) {
  const problems = [];
  const all = `${subject}\n${preview}\n${body_plain}`;
  const lower = all.toLowerCase();

  if (/\bJess\b/.test(all)) problems.push('Mentions the internal persona name "Jess".');
  if (/[—]/.test(all)) problems.push('Contains an em dash.');
  for (const w of BANNED) if (lower.includes(w)) problems.push(`Uses banned word or phrase "${w}".`);
  for (const w of SPAMMY) if (lower.includes(w)) problems.push(`Spam-style phrase "${w}".`);

  const [min, max] = WORDS[type] || WORDS.letter;
  const words = body_plain.trim().split(/\s+/).length;
  if (words < min || words > max) problems.push(`Body is ${words} words; this email type needs ${min} to ${max}.`);

  const sWords = subject.trim().split(/\s+/).length;
  if (subject.length > 70 || sWords < 2 || sWords > 12) problems.push('Subject line should be 2 to 12 words and under 70 characters.');
  if (/[A-Z]{4,}/.test(subject)) problems.push('Subject shouts in capitals.');
  if (/!/.test(subject)) problems.push('Subject uses an exclamation mark.');

  if (RESEARCH_WORDS.test(body_plain)) problems.push('Makes a research or study claim, which is not allowed unless it came from the input.');
  const figures = body_plain.match(/(?:£|\$|€)\s?\d[\d,.]*k?|\d[\d,.]*\s?(?:%|per ?cent)/gi) || [];
  const src = norm(sourceText).replace(/,/g, '');
  for (const f of figures) {
    const n = norm(f).replace(/,/g, '').replace(/\s/g, '');
    if (!src.replace(/\s/g, '').includes(n)) problems.push(`Contains a figure "${f.trim()}" that is not in Joel's facts or the input. No invented numbers.`);
  }

  const links = body_plain.match(/https?:\/\/[^\s)>\]]+/g) || [];
  for (const l of links) {
    const clean = l.replace(/[.,;:]+$/, '');
    if (!allowedLinks.some((a) => clean === a || clean.startsWith(a + '#') || clean.startsWith(a + '?'))) problems.push(`Contains a link that wasn't provided: ${clean}`);
  }

  for (const n of blockedNames) {
    if (new RegExp(`\\b${n.replace(/[^A-Za-z'-]/g, '')}\\b`, 'i').test(all)) problems.push(`Contains the name "${n}" from a private call. Anonymise it.`);
  }

  const copied = copiedRun(body_plain, shapeText);
  if (copied) problems.push(`Copies the competitor's wording ("${copied}"). Copy the shape, write Joel's own words.`);

  if (/\b(I read every|I reply to every|thousands of|hundreds of|most of my clients|all of my clients|every client|guaranteed (?:results|to))\b/i.test(all)) problems.push('Makes an unverifiable claim about Joel, his clients or results.');
  if (!/\bJoel\b/.test(body_plain)) problems.push('Must be signed off "Joel".');
  if (/\b(investment advice|you should invest|buy shares|buy (?:this )?fund|put your money in)\b/i.test(all)) problems.push('Reads like regulated investment advice.');
  if (/\b(pay less tax|avoid tax|tax loophole|claim (?:this|it) as an expense)\b/i.test(all)) problems.push('Reads like tax advice.');
  if (/\bmanifest(?:ing|ation)? (?:works|will bring|brings)\b/i.test(all)) problems.push('Claims manifesting works.');

  return problems;
}
