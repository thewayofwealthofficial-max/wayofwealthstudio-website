// Minimal Anthropic Messages API client for drafting the daily email.
// Returns { subject, preview, body_plain } parsed from the model's JSON output.

export async function draftEmail({ apiKey, model, system, user, maxTokens = 1200 }) {
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model,
      max_tokens: maxTokens,
      system,
      messages: [{ role: 'user', content: user }],
    }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Anthropic API failed: ${res.status} ${text}`);
  }
  const data = await res.json();
  const text = (data.content || []).map((b) => b.text || '').join('').trim();
  return parseDraft(text);
}

// Separate pass, same as the LinkedIn robot's: a fresh call that only compares claims with Joel's words.
// Added 2 Nov 2026 after a test letter opened "Someone I work with earns well. Always has." (he never said it).
// Returns a list of problems; an empty list means every claim is backed. One retry if its reply can't be read.
export async function factCheck({ apiKey, model, facts, passages, email }) {
  const system = `You are a strict fact checker. You get Joel's own words (call transcript passages), Joel's fixed facts, and an email written from them. List every statement in the email about something that happened, a person, a number, a feeling Joel had, or what someone did, that is NOT supported by the passages or the facts. The FACTS are true and count as support. General reflections, advice and questions to the reader are fine. Also flag if the email turns Joel's own story into a client's, or a client's into Joel's, or adds details about who someone is (their job, income, age, family) that the passages don't give. Leaving out a detail, or leaving someone unnamed, is never a problem. The email copies the BUILD of a real newsletter (its opening, its sections, its sign-off): that framing is fine and needs no support, as long as every statement of fact, story or feeling comes from Joel. Keep every issue short. Output only JSON: {"items": [{"issue": "short description", "real_problem": true or false}]}`;
  const user = `FACTS:\n${facts}\n\nPASSAGES:\n${passages}\n\nEMAIL:\nSubject: ${email.subject}\n\n${email.body_plain}`;
  const ask = async () => {
    const res = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'x-api-key': apiKey, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
      body: JSON.stringify({ model, max_tokens: 3000, system, messages: [{ role: 'user', content: user }] }),
    });
    if (!res.ok) throw new Error(`Anthropic API failed: ${res.status} ${await res.text()}`);
    const text = ((await res.json()).content || []).map((b) => b.text || '').join('');
    return JSON.parse(text.slice(text.indexOf('{'), text.lastIndexOf('}') + 1));
  };
  let r;
  try { r = await ask(); } catch { r = await ask(); }
  return (r.items || []).filter((i) => i.real_problem === true).map((i) => `Not in Joel's words: ${i.issue}`);
}

function parseDraft(text) {
  let raw = text.trim().replace(/^```(?:json)?/i, '').replace(/```$/, '').trim();
  const start = raw.indexOf('{');
  const end = raw.lastIndexOf('}');
  if (start !== -1 && end !== -1) raw = raw.slice(start, end + 1);
  let obj;
  try {
    obj = JSON.parse(raw);
  } catch (e) {
    throw new Error('Could not parse model JSON: ' + e.message + '\nRaw start: ' + text.slice(0, 300));
  }
  if (!obj.subject || !obj.body_plain) throw new Error('Draft missing subject or body_plain');
  return {
    subject: String(obj.subject).trim(),
    preview: String(obj.preview || '').trim(),
    body_plain: String(obj.body_plain).trim(),
  };
}
