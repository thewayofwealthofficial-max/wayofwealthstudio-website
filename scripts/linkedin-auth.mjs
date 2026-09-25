#!/usr/bin/env node
// One-time (then every ~60 days) LinkedIn login for the blog poster.
// Run on Joel's computer: node scripts/linkedin-auth.mjs
// 1. Opens LinkedIn's "Allow" screen in the browser.
// 2. Catches the reply on http://localhost:8765/callback (must match the app's redirect URL).
// 3. Swaps it for an access token, reads Joel's member id, and saves both to GitHub secrets
//    (LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN, LINKEDIN_TOKEN_EXPIRES). Nothing is printed or committed.
// Needs LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET in .env (git-ignored) and the gh CLI logged in.

import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
import { execFileSync, exec } from 'node:child_process';
import { randomBytes } from 'node:crypto';

const env = Object.fromEntries(readFileSync(new URL('../.env', import.meta.url), 'utf8')
  .split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1)]));
const CLIENT_ID = env.LINKEDIN_CLIENT_ID, SECRET = env.LINKEDIN_CLIENT_SECRET;
if (!CLIENT_ID || !SECRET) { console.error('LINKEDIN_CLIENT_ID / LINKEDIN_CLIENT_SECRET missing from .env'); process.exit(1); }
const REDIRECT = 'http://localhost:8765/callback';
const state = randomBytes(12).toString('hex');
const authUrl = 'https://www.linkedin.com/oauth/v2/authorization?' + new URLSearchParams({
  response_type: 'code', client_id: CLIENT_ID, redirect_uri: REDIRECT, state, scope: 'openid profile w_member_social',
});

const setSecret = (name, value) => execFileSync('gh', ['secret', 'set', name], { input: value, stdio: ['pipe', 'ignore', 'inherit'] });

const server = createServer(async (req, res) => {
  const u = new URL(req.url, REDIRECT);
  if (u.pathname !== '/callback') { res.end(); return; }
  const done = (msg) => { res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' }); res.end(`<p style="font:18px sans-serif;margin:3rem">${msg}</p>`); };
  try {
    if (u.searchParams.get('error')) throw new Error(u.searchParams.get('error_description') || u.searchParams.get('error'));
    if (u.searchParams.get('state') !== state) throw new Error('State mismatch. Run the script again.');
    const tok = await fetch('https://www.linkedin.com/oauth/v2/accessToken', {
      method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ grant_type: 'authorization_code', code: u.searchParams.get('code'), redirect_uri: REDIRECT, client_id: CLIENT_ID, client_secret: SECRET }),
    }).then((r) => r.json());
    if (!tok.access_token) throw new Error('No token: ' + JSON.stringify(tok).slice(0, 200));
    const me = await fetch('https://api.linkedin.com/v2/userinfo', { headers: { authorization: `Bearer ${tok.access_token}` } }).then((r) => r.json());
    if (!me.sub) throw new Error('Could not read your profile id: ' + JSON.stringify(me).slice(0, 200));
    const expires = new Date(Date.now() + (tok.expires_in || 0) * 1000).toISOString().slice(0, 10);
    setSecret('LINKEDIN_ACCESS_TOKEN', tok.access_token);
    setSecret('LINKEDIN_PERSON_URN', `urn:li:person:${me.sub}`);
    setSecret('LINKEDIN_TOKEN_EXPIRES', expires);
    console.log(`OK: connected as ${me.name}. Token saved to GitHub secrets, expires ${expires}.`);
    done(`Connected as <b>${me.name}</b>. You can close this tab.`);
  } catch (e) {
    console.error('FAILED:', e.message);
    done('Something went wrong: ' + String(e.message).replace(/</g, '&lt;'));
  } finally { setTimeout(() => process.exit(0), 500); }
});
server.listen(8765, () => {
  console.log('Opening LinkedIn in your browser. If it does not open, visit:\n' + authUrl);
  exec(process.platform === 'win32' ? `start "" "${authUrl}"` : `open "${authUrl}"`);
});
setTimeout(() => { console.error('Timed out after 10 minutes. Run it again.'); process.exit(1); }, 600000);
