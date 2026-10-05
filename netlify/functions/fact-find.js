// Fact find for the paid "Your Cash Flow Session" (2026-10-05). Form at /your-number/fact-find.
//   POST /api/fact-find   body: JSON of the answers (see FIELDS)
// Saves the answers (Netlify Blobs, store "fact-finds"), then emails them to Joel and pings him on Telegram.
// The save happens first, so answers are never lost if the email fails. A failed email is reported back
// to the person filling it in, plainly.
//
// Netlify env: RESEND_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.

const { connectLambda, getStore } = require('@netlify/blobs');
const { rs, fromAddress } = require('./lib/sequence-core');
const { telegram } = require('./lib/magnet-events');

const TO = 'joel@wayofwealthcoaching.com'; // forwards to Joel's Gmail (see sequence-core REPLY_TO)

// [key, label, required] in the order of the form. Labels match the page word for word.
const FIELDS = [
  ['name', 'Your name', true],
  ['email', 'Your email', true],
  ['country', 'Which country do you pay tax in, and what currency are you paid in?', true],
  ['setup', 'How is your business set up?', true],
  ['website', 'Your website or Instagram', false],
  ['work', 'What do you do, and who do you do it for?', true],
  ['charge', 'What do you charge now?', true],
  ['days', 'How many days a week do you work, and how many clients or sessions in a day?', true],
  ['weeksOff', 'How many weeks off do you take a year?', true],
  ['diary', 'Roughly how full is your diary?', true],
  ['moneyIn', 'Roughly what comes into the business each month?', true],
  ['swing', 'How much does that change from month to month?', true],
  ['businessCosts', 'Business costs each month', true],
  ['personalCosts', 'Personal costs each month', true],
  ['savings', 'How much do you have in cash savings?', true],
  ['debts', 'Any monthly debt payments?', false],
  ['taxAside', 'Do you put money aside for tax as it comes in?', true],
  ['taxRate', 'Has your accountant given you a tax rate to set aside?', false],
  ['payYourself', 'Do you pay yourself a set amount on a set day?', true],
  ['enough', 'How much do you need to take home each month, after tax, for life to feel like enough?', true],
  ['savingFor', "Is there something you're saving towards?", false],
  ['calm', 'On a scale of 1 to 10, how calm do you feel about money right now?', true],
  ['anythingElse', "Is there anything else you'd like me to know before we speak?", false],
];

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const clean = (v) => (typeof v === 'string' ? v.trim().slice(0, 4000) : '');

exports.handler = async (event) => {
  const headers = { 'Cache-Control': 'no-store', 'Content-Type': 'application/json' };
  if (event.httpMethod !== 'POST') return { statusCode: 405, headers, body: JSON.stringify({ ok: false, error: 'POST only' }) };

  let b;
  try { b = JSON.parse(event.body || '{}'); } catch { return { statusCode: 400, headers, body: JSON.stringify({ ok: false, error: 'Bad request' }) }; }
  if (clean(b.company)) return { statusCode: 200, headers, body: JSON.stringify({ ok: true }) }; // honeypot: bots fill it, people don't

  const answers = {};
  for (const [key] of FIELDS) answers[key] = clean(b[key]);
  const missing = FIELDS.filter(([key, , req]) => req && !answers[key]).map(([, label]) => label);
  if (missing.length) return { statusCode: 400, headers, body: JSON.stringify({ ok: false, error: `Please answer: ${missing.join(' · ')}` }) };
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(answers.email)) return { statusCode: 400, headers, body: JSON.stringify({ ok: false, error: 'Please check your email address.' }) };

  const at = new Date().toISOString();
  connectLambda(event);
  await getStore('fact-finds').setJSON(`${at}_${answers.email.toLowerCase()}`, { at, answers });

  const rows = FIELDS.map(([key, label]) => `<p style="margin:0 0 14px"><b>${esc(label)}</b><br>${esc(answers[key] || '—').replace(/\n/g, '<br>')}</p>`).join('');
  const text = FIELDS.map(([key, label]) => `${label}\n${answers[key] || '—'}`).join('\n\n');
  const res = await rs('/emails', {
    method: 'POST',
    body: {
      from: await fromAddress(),
      to: [TO],
      reply_to: answers.email,
      subject: `Fact find: ${answers.name} (Cash Flow Session)`,
      html: `<div style="font-family:Georgia,serif;font-size:15px;line-height:1.5">${rows}<p style="color:#777">Sent ${esc(at)}</p></div>`,
      text: `${text}\n\nSent ${at}`,
    },
  });
  if (!res.ok) {
    console.error('fact-find email failed', res.status, res.text.slice(0, 300));
    return { statusCode: 502, headers, body: JSON.stringify({ ok: false, error: 'Your answers were saved, but the email to Joel did not send. Please email joel@wayofwealthcoaching.com to let him know.' }) };
  }

  try {
    await telegram(`📋 <b>Fact find in</b>: ${esc(answers.name)} (${esc(answers.email)}). Full answers in your email.`);
  } catch (e) {
    console.error('fact-find telegram failed', e.message); // email already went, so the person still gets a success
  }
  return { statusCode: 200, headers, body: JSON.stringify({ ok: true }) };
};
