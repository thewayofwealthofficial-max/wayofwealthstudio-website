// Joel's own words from his 2.5-hour solo money talk to camera (22 Sep 2026), cut into 72 passages of 100-300 words
// (Joel, 5 Oct 2026: "you should have more than enough material to write almost 100% in my voice").
// Left out before encrypting: his family's health, his old employer, research figures not in TEACHING_SCOPE.md,
// money splits, lines aimed at the old wellness audience, and asides about drawings on screen.
//
// PRIVACY: this repo and its logs are PUBLIC, so the passages are stored encrypted (talk-passages.enc) and unlocked
// at run time with the VOICE_KEY secret. Never print or save them. Full transcript: main project
// _keep/JOEL_TALK_2026-09-22.md. To rebuild, re-encrypt with the same key (wow-website/.env VOICE_KEY).

import { readFileSync } from 'node:fs';
import { createDecipheriv, createHash } from 'node:crypto';

let cache = null;

/** Opens one of the encrypted JSON files in this folder with VOICE_KEY. */
export function openBox(file, key = process.env.VOICE_KEY) {
  const box = JSON.parse(readFileSync(new URL(`./${file}`, import.meta.url), 'utf8'));
  const d = createDecipheriv('aes-256-gcm', Buffer.from(key, 'base64'), Buffer.from(box.iv, 'base64'));
  d.setAuthTag(Buffer.from(box.tag, 'base64'));
  return JSON.parse(Buffer.concat([d.update(Buffer.from(box.data, 'base64')), d.final()]).toString('utf8'));
}

/** All talk passages as [{date, text}], or [] when VOICE_KEY isn't set (the writers still run on Fathom alone). */
export function talkPassages(key = process.env.VOICE_KEY) {
  if (cache) return cache;
  if (!key) { console.log('VOICE_KEY not set: no talk passages.'); return []; }
  cache = openBox('talk-passages.enc', key);
  return cache;
}

/** n talk passages that rotate by day, so each run sees a different slice. `skip(p)` drops ones used recently. */
export function pickTalk(n, { day = Math.floor(Date.now() / 864e5), skip = () => false } = {}) {
  const all = talkPassages().filter((p) => !skip(p));
  if (!all.length) return [];
  const start = (day * 7) % all.length;
  return Array.from({ length: Math.min(n, all.length) }, (_, i) => all[(start + i) % all.length]);
}

export const hashText = (s) => createHash('sha256').update(s).digest('hex').slice(0, 16);
