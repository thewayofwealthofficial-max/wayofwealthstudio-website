// How Joel actually talks, for EVERY writer that writes in his name (Joel, 2 Oct 2026: "make sure that every single
// post/email/blog everything is using my fathom calls as context for how i speak/type").
//
// Two parts:
//   1. VOICE_FACTS: measured from 32 of his calls, 166,626 words (main project: _keep/LINGUISTIC_PROFILE.md).
//      Facts only; no client names (this repo is public). Word bans were lifted 6 Sep 2026, so the rare words are
//      described as measured facts, not banned.
//   2. His own recent Fathom lines (his speaker turns only), pulled at run time by daily-email/fathom.mjs.
//
// PRIVACY: this repo and its Action logs are PUBLIC. Passages stay in memory and go to the model only; never print
// or save them. They are for VOICE: the writer must not lift a client's details, name, numbers or story from them.
// leaksName() blocks a draft that contains the first name of anyone else on those calls.

import { recentJoelWords } from '../daily-email/fathom.mjs';

export const VOICE_FACTS = `MEASURED FROM 32 OF JOEL'S CALLS (166,626 words of him talking):
- Peer to peer, never clinical. Like a mate explaining it over a coffee at the kitchen table.
- Short sentences: median 7 words, over a third under 5. Reading level about grade 5.
- The rhythm: one longer rolling sentence that builds the reason (joined with and / but / because / so), then a short one that lands it ("That's it." "Makes sense."). Then a check-in: "right?"
- Opens with "Okay" or "So". Ends a point with "right?". Says "you know", "kind of", "a little bit", "actually", "really".
- Gives every abstract idea a physical object (a staircase, a spaceship, a potter). Does the sums out loud, working included.
- Says "we", not "you should". Hedges honestly ("I could be wrong", "correct me if I'm wrong"). Tells his own version of the reader's mistake, at his own expense. Turns shame into data ("What's that telling you?"). Never reassures with "don't be so hard on yourself".
- Says "belief" a lot (as often as "goal"). In his own speech he almost never says mindset, subconscious, framework, protocol, methodology, architecture, sovereign, abundance, manifest, vibration, healing, holistic, portfolio or allocation. (If your brief lets you use the READER's words, such as manifesting or abundance, that still stands: use them as their words, not as his.)
- No em dashes.`;

/**
 * Returns { block, names }. block goes into the writer's prompt; names feed leaksName().
 * Never throws: if Fathom is down the writer still gets VOICE_FACTS, and says so in the log.
 */
export async function joelVoice({ key = process.env.FATHOM_API_KEY, days = 30, maxPassages = 6 } = {}) {
  let passages = [], names = new Set();
  try {
    ({ passages, names } = await recentJoelWords({ key, days, maxPassages }));
  } catch (e) {
    console.log(`Fathom unavailable (${e.message}); writing from the measured voice facts only.`);
  }
  console.log(`Joel voice passages: ${passages.length} (not printed: private).`);
  const lines = passages.length
    ? `\n\nHOW JOEL ACTUALLY TALKS: his own words from recent calls. Copy his rhythm, his words and his way of explaining. These are for VOICE ONLY: never use a client's name, details, numbers or story from them, and never quote them.\n${passages.map((p, i) => `[${i + 1}] ${p.text}`).join('\n\n')}`
    : '';
  return { block: `\n\n${VOICE_FACTS}${lines}\n\nWrite it the way Joel would say it out loud, written down.`, names };
}

// First names of other people on his calls. A draft containing one is blocked.
export function leaksName(text, names) {
  for (const n of names || []) {
    if (n.length > 2 && new RegExp(`\\b${n.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`).test(text)) return n;
  }
  return null;
}
