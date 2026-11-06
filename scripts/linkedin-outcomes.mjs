// What Joel did with each LinkedIn draft (6 Nov 2026), so the writer learns which shapes he posts as they are.
// The draft page (netlify/functions/linkedin-draft.js) gives him two buttons: "Approve and post" posts the text
// exactly as sent, and "Rewrite it" sends his fixes back for a new draft. So, per draft:
//   unchanged  posted exactly as Fred sent it (its id is in state/linkedin-posted.json, no rewrite asked)
//   edited     Joel asked for a rewrite (the revision is logged with revisedFrom = this id); `posted` says if the
//              rewritten one went up
//   rejected   neither posted nor rewritten within 48 hours (the link expires)
//   pending    still inside the 48 hours
// It can't see edits Joel makes on LinkedIn after posting. Shape and topic only are logged, never text.

const EXPIRES_MS = 48 * 36e5;

/** Sets `outcome` (and `posted` for edited) on every logged draft that has an id. Mutates and returns state. */
export function markOutcomes(state, postedIds, now = Date.now()) {
  const posted = new Set(postedIds || []);
  for (const s of state) {
    if (!s.id || s.revisedFrom) continue; // revisions are folded into their original
    const revisions = [];
    for (let cur = s.id, r; (r = state.find((x) => x.revisedFrom === cur)); cur = r.id) revisions.push(r);
    if (revisions.length) { s.outcome = 'edited'; s.posted = revisions.some((r) => posted.has(r.id)); }
    else if (posted.has(s.id)) s.outcome = 'unchanged';
    else s.outcome = now - Date.parse(s.sentAt || s.date) > EXPIRES_MS ? 'rejected' : 'pending';
  }
  return state;
}

/** Shapes Joel posted unchanged in the last `days`, most recent first: [{hook, structure, words, paragraphs, topic}]. */
export function preferredShapes(state, days = 30, now = Date.now()) {
  return state
    .filter((s) => s.outcome === 'unchanged' && s.shape && now - Date.parse(s.date) < days * 864e5)
    .reverse()
    .map((s) => ({ hook: s.shape.hook || null, structure: s.shape.structure || null, words: s.shape.words, paragraphs: s.shape.paragraphs, topic: s.topic || null }));
}
