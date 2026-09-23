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
