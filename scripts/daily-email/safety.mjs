// Automatic safety checks. Nothing goes to the list unless it passes every check here.
// A draft that fails is regenerated with the problems fed back; after three failures the
// send is skipped and Joel is told why.

// AI tells and hype only. Joel lifted vocabulary bans on 2026-09-06; spiritual words are
// allowed (Joel dropped the "never claim manifesting works" rule on 2026-09-24).
const BANNED = [
  'hustle', 'grind', 'side hustle', 'boss babe', 'money magnet', 'passive income', 'toxic positivity',
  'growth hack', 'you got this', 'level up', 'journey', 'breakthrough', 'unlock', 'heal your money story',
  'delve', 'unpack', 'tapestry', 'holistic', 'level 4', 'game changer', 'game-changer',
  // Joel's email prompt (EMAIL_COPY.md, 5 Oct 2026): generic AI English.
  "in today's world", 'are you tired of', 'crushing it', 'smash your goals', 'transform', 'dive in', "it's not just",
];
const SPAMMY = ['act now', 'limited time', 'click here', 'free money', 'urgent', '100%', '!!'];
const RESEARCH_WORDS = /\b(studies show|study shows|research shows|research says|according to|survey|scientists?|a recent study)\b/i;

const WORDS = { letter: [150, 340], post: [150, 340], fridays: [330, 640] };

export function clean(s) {
  return String(s || '').replace(/\s*—\s*/g, ', ').replace(/\s*–\s*/g, ', ').replace(/[ \t]+\n/g, '\n').trim();
}

const norm = (s) => String(s).toLowerCase().replace(/[^a-z0-9£$€% ]+/g, ' ').replace(/\s+/g, ' ').trim();

// Joel, 27 Sep: borrowing the competitor's wording is fine up to about 15% of the email, with no single copied
// stretch longer than 12 words (whole sentences and paragraphs are where copyright bites). Words count as
// "copied" when they sit inside any 6-word run that also appears in the competitor email.
function copiedRun(body, shapeText) {
  if (!shapeText) return null;
  const b = norm(body).split(' ').filter(Boolean);
  const s = ` ${norm(shapeText)} `;
  const covered = new Array(b.length).fill(false);
  for (let i = 0; i + 6 <= b.length; i++) {
    if (s.includes(` ${b.slice(i, i + 6).join(' ')} `)) for (let k = i; k < i + 6; k++) covered[k] = true;
  }
  let longest = 0, cur = 0, start = 0, bestStart = 0;
  covered.forEach((c, i) => { if (c) { if (!cur) start = i; cur++; if (cur > longest) { longest = cur; bestStart = start; } } else cur = 0; });
  const share = b.length ? covered.filter(Boolean).length / b.length : 0;
  if (longest > 12) return `a ${longest}-word stretch copied: "${b.slice(bestStart, bestStart + longest).join(' ')}"`;
  if (share > 0.15) return `${Math.round(share * 100)}% of the words copied (limit 15%)`;
  return null;
}

export function checkDraft({ subject, preview, body_plain }, { type, phase, allowedLinks = [], sourceText = '', shapeText = '', shapeSubject = '', blockedNames = new Set(), passagesText = '', requireJoelWords = false } = {}) {
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

  // Joel's email prompt (EMAIL_COPY.md, 5 Oct 2026), Mode 1 deliverability and the ALWAYS rules.
  const sLen = [...subject.trim()].length;
  if (sLen < 30 || sLen > 50) problems.push(`Subject is ${sLen} characters; it needs 30 to 50.`);
  const pLen = [...String(preview || '').trim()].length;
  if (pLen < 40 || pLen > 90) problems.push(`Preview is ${pLen} characters; it needs 40 to 90.`);
  if (norm(preview).includes(norm(subject)) || norm(subject).includes(norm(preview))) problems.push('Preview repeats the subject. It should add to it.');
  if (/[A-Z]{4,}/.test(subject)) problems.push('Subject shouts in capitals.');
  if (/!/.test(subject)) problems.push('Subject uses an exclamation mark.');
  // Capitals: letters in all-capital words (2+ letters, common short forms allowed) under 10% in the subject, 3% in the body.
  const OK_CAPS = /^(UK|US|VAT|HMRC|QFP|MSC|PS|OK|TV|ID|PAYE|ISA|USA|EU)$/;
  const capsShare = (s) => { const letters = (s.match(/[A-Za-z]/g) || []).length; const shout = (s.match(/\b[A-Z]{2,}\b/g) || []).filter((w) => !OK_CAPS.test(w)).join('').length; return letters ? shout / letters : 0; };
  if (capsShare(subject) >= 0.1) problems.push('Subject has too many capitals (keep under 10%).');
  if (capsShare(body_plain) >= 0.03) problems.push('Body shouts in capitals (keep all-capital words under 3% of letters).');
  if ((body_plain.match(/!/g) || []).length > 1) problems.push('More than one exclamation mark in the body. Zero is best.');
  const fillers = (body_plain.match(/\b(genuinely|actually|really|literally)\b/gi) || []).length;
  if (fillers > 2) problems.push(`Uses "genuinely", "actually", "really" or "literally" ${fillers} times. Two at most.`);

  // "push_pitch" is the PHASE (the Sunday invitation in a month's last 9 days), not the type. Checking
  // type here blocked the one email the price belongs in (bug found 27 Sep).
  if (phase !== 'push_pitch' && /£\s?(1,?000|500|334)\b/.test(body_plain)) problems.push('Mentions the coaching price. The price only goes in the Sunday push email (Joel, 2026-09-25).');
  if (RESEARCH_WORDS.test(body_plain)) problems.push('Makes a research or study claim, which is not allowed unless it came from the input.');
  const figures = body_plain.match(/(?:£|\$|€)\s?\d[\d,.]*k?|\d[\d,.]*\s?(?:%|per ?cent)/gi) || [];
  const src = norm(sourceText).replace(/,/g, '');
  for (const f of figures) {
    const n = norm(f).replace(/,/g, '').replace(/\s/g, '');
    if (!src.replace(/\s/g, '').includes(n)) problems.push(`Contains a figure "${f.trim()}" that is not in Joel's facts or the input. No invented numbers.`);
  }

  const links = body_plain.match(/https?:\/\/[^\s)>\]]+/g) || [];
  const distinct = new Set(links.map((l) => l.replace(/[.,;:]+$/, '')));
  if (distinct.size > 2) problems.push(`Has ${distinct.size} different links. Two at most, one ask (Joel's email prompt).`);
  for (const l of links) {
    const clean = l.replace(/[.,;:]+$/, '');
    if (!allowedLinks.some((a) => clean === a || clean.startsWith(a + '#') || clean.startsWith(a + '?'))) problems.push(`Contains a link that wasn't provided: ${clean}`);
  }

  for (const n of blockedNames) {
    if (new RegExp(`\\b${n.replace(/[^A-Za-z'-]/g, '')}\\b`, 'i').test(all)) problems.push(`Contains the name "${n}" from a private call. Anonymise it.`);
  }

  if (/\b(suicid\w*|self[- ]harm|overdos\w*|rehab)\b/i.test(all)) problems.push('Touches suicide, self-harm, overdose or rehab. Never in a list email.');
  // Capitalised names that appear in Joel's call passages (partners, exes, friends, firms) must not reach the email.
  if (passagesText) {
    const ALLOW = new Set(['Joel', 'I', 'Money', 'Story', 'Method', 'Reset', 'Tool', 'Finance', 'Fridays', 'Way', 'Wealth', 'Friday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Saturday', 'Deliveroo', 'Uber', 'Instagram', 'Christmas', 'MSc', 'Behavioural', 'Economics', 'Qualified', 'Financial', 'Planner', 'Book', 'Know', 'Try', 'One', 'Read', 'Hey', 'P', 'S']);
    const COMMON = /^(The|And|But|So|When|There|Not|Yeah|Right|Tell|Week|God|Jesus|Okay|Yes|No|This|That|What|Why|How|Now|Then|Just|Like|January|February|March|April|May|June|July|August|September|October|November|December|Saturdays|Sundays|North|Star|Hebrew|South|Africa|Israel|Italy|America|England|London)$/;
    const midSentence = (s) => new Set((s.match(/(?<=[a-z,] )[A-Z][a-z]{2,}\b/g) || []).filter((w) => !ALLOW.has(w) && !COMMON.test(w)));
    const inCalls = midSentence(passagesText);
    for (const w of midSentence(body_plain)) if (inCalls.has(w)) problems.push(`Uses the name or place "${w}" from a private call. Leave other people and places out.`);
  }

  const copied = copiedRun(body_plain, shapeText);
  if (copied) problems.push(`Copies too much of the competitor's wording (${copied}). Short phrases are fine; keep at least 85% of the words Joel's own and no copied stretch over 12 words.`);

  if (/\b(I read every|I reply to every|thousands of|hundreds of|most of my clients|all of my clients|every client|guaranteed (?:results|to)|most people|one of the most common|I see (?:this|it) all the time|everyone I work with)\b/i.test(all)) problems.push('Makes an unverifiable claim about Joel, his clients, or "most people".');
  if (/\b(spots?|places?|spaces?)\b[^.\n]{0,25}\b(left|open|remaining|available)\b|\b(only|just) (?:a few|\d+|one|two|three) (?:spots?|places?|spaces?)\b|\b(?:just about|nearly|almost|close to) (?:at|full|there|booked)\b|\bat my (?:\d+|five) (?:people|clients|places)\b|\bfilling up\b|\bfully booked\b|\b(?:last|final) (?:spot|place|space)s?\b/i.test(all)) problems.push('States availability ("spots still open", "places left"). Only "I take on 5 people a month" is true; never say how many are left.');
  if (/\bI hear (?:this |it |that )?(?:from [^.\n]{0,40})?(?:all the time|a lot|so often|most|constantly)\b|\b(?:a lot of|lots of|many|so many) (?:people|clients|practitioners|(?:small )?business owners|freelancers|of you) (?:tell|say|ask|have told)\b|\bthe (?:objection|question) I (?:hear|get) most\b/i.test(all)) problems.push('Claims how often Joel hears something ("I hear this all the time", "a lot of people tell me"). Unverifiable, cut it.');
  if (/\b(?:5|five) (?:people|clients)\b(?! a month)/i.test(all)) problems.push('Says "5 people" without "a month". The fact is "I take on 5 people a month".');
  if (/\bhere'?s the thing\b|\bdopamine\b|\bthe truth is\b/i.test(all)) problems.push('Uses an AI tell or an unsourced brain claim ("here\'s the thing", "dopamine", "the truth is").');
  const wordNums = body_plain.match(/\b(?:two|three|four|five|six|seven|eight|nine|ten|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred)(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?\s+(?:minutes?|hours?|days?|weeks?|months?|years?|percent|per cent|pounds|times)\b/gi) || [];
  for (const w of wordNums) if (!norm(sourceText).includes(norm(w))) problems.push(`Contains a spelled-out figure "${w}" that isn't in the input. No invented numbers.`);

  if (requireJoelWords && passagesText) {
    const b = norm(body_plain).split(' ');
    const p = ` ${norm(passagesText)} `;
    let found = false;
    for (let i = 0; i + 5 <= b.length && !found; i++) if (p.includes(` ${b.slice(i, i + 5).join(' ')} `)) found = true;
    if (!found) problems.push("Doesn't use Joel's own words. Build the story from ONE of JOEL'S OWN WORDS passages and keep at least one of his phrases word for word.");
  }
  if (shapeSubject) {
    const s = norm(subject).split(' ');
    const ss = ` ${norm(shapeSubject)} `;
    for (let i = 0; i + 5 <= s.length; i++) if (ss.includes(` ${s.slice(i, i + 5).join(' ')} `)) { problems.push("Subject reuses the competitor's subject wording. Write Joel's own subject in the same style."); break; }
  }
  if (!/\bJoel\b/.test(body_plain)) problems.push('Must be signed off "Joel".');
  if (/\b(investment advice|you should invest|buy shares|buy (?:this )?fund|put your money in)\b/i.test(all)) problems.push('Reads like regulated investment advice.');
  if (/\b(pay less tax|avoid tax|tax loophole|claim (?:this|it) as an expense)\b/i.test(all)) problems.push('Reads like tax advice.');

  return problems;
}
