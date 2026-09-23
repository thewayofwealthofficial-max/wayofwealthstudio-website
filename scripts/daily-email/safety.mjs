// Automatic safety checks. With no human approving the send, nothing goes to the list
// unless it passes every check here. A draft that fails is regenerated (with the problems
// fed back to the model) and, after three failures, the day is skipped and Joel is told why.

const BANNED = [
  'hustle', 'grind', 'side hustle', 'boss babe', 'manifest', 'abundance', 'attract wealth', 'money magnet',
  'passive income', 'financial freedom', 'toxic positivity', 'growth hack', 'you got this', 'level up',
  'vibration', 'frequency', 'law of attraction', 'journey', 'breakthrough', 'unlock', 'heal your money story',
  'delve', 'unpack', 'tapestry', 'holistic', 'mindset', 'level 4', 'game changer', 'game-changer',
];
const SPAMMY = ['act now', 'limited time', 'click here', 'guarantee', 'free money', 'urgent', 'last chance', '100%', '!!'];
const RESEARCH_WORDS = /\b(studies show|study shows|research shows|research says|according to|survey|scientists?|a recent study)\b/i;

export function clean(s) {
  return String(s || '').replace(/\s*—\s*/g, ', ').replace(/\s*–\s*/g, ', ').replace(/[ \t]+\n/g, '\n').trim();
}

export function checkDraft({ subject, preview, body_plain }, { ctaUrl, intelText = '' } = {}) {
  const problems = [];
  const all = `${subject}\n${preview}\n${body_plain}`;
  const lower = all.toLowerCase();

  if (/\bJess\b/.test(all)) problems.push('Mentions the internal persona name "Jess".');
  if (/[—]/.test(all)) problems.push('Contains an em dash.');
  for (const w of BANNED) if (lower.includes(w)) problems.push(`Uses banned word or phrase "${w}".`);
  for (const w of SPAMMY) if (lower.includes(w)) problems.push(`Spam-style phrase "${w}".`);

  const words = body_plain.trim().split(/\s+/).length;
  if (words < 100) problems.push(`Body too short (${words} words, need 100 to 260).`);
  if (words > 260) problems.push(`Body too long (${words} words, need 100 to 260).`);

  const sWords = subject.trim().split(/\s+/).length;
  if (subject.length > 70 || sWords < 3 || sWords > 11) problems.push('Subject line should be 3 to 11 words and under 70 characters.');
  if (/[A-Z]{4,}/.test(subject)) problems.push('Subject shouts in capitals.');
  if (/!/.test(subject)) problems.push('Subject uses an exclamation mark.');

  if (RESEARCH_WORDS.test(body_plain)) problems.push('Makes a research or study claim, which is not allowed unless it came from the input.');
  const figures = body_plain.match(/(?:£|\$|€)\s?\d[\d,.]*|\d[\d,.]*\s?(?:%|per ?cent)/gi) || [];
  for (const f of figures) {
    if (!intelText.includes(f.trim())) problems.push(`Contains a figure "${f.trim()}" that is not in the input. No invented numbers.`);
  }

  const links = body_plain.match(/https?:\/\/\S+/g) || [];
  for (const l of links) if (ctaUrl && !l.startsWith(ctaUrl)) problems.push(`Contains a link other than the call link: ${l}`);

  if (!/\bJoel\s*$/i.test(body_plain.trim())) problems.push('Must end with the sign-off "Joel".');
  if (/\b(investment advice|you should invest|buy shares|buy (?:this )?fund|put your money in)\b/i.test(all)) problems.push('Reads like regulated investment advice.');
  if (/\b(pay less tax|avoid tax|tax loophole|claim (?:this|it) as an expense)\b/i.test(all)) problems.push('Reads like tax advice.');

  return problems;
}
