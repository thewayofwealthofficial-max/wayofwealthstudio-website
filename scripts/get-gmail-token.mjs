// One-off Gmail re-auth helper. Mints a fresh GMAIL_REFRESH_TOKEN and (if gh is
// available) writes it straight into the GitHub Actions secret.
//
// WHY THIS EXISTS: the funnel-hack digest authenticates to Gmail with a stored
// refresh token. Google expires those (inactivity, password change, security
// event) and the digest then dies with `invalid_grant`. Run this to get a new one.
//
// USAGE (PowerShell, from the wow-website folder):
//   $env:GMAIL_CLIENT_ID="<client id>"; $env:GMAIL_CLIENT_SECRET="<client secret>"; node scripts/get-gmail-token.mjs
//
// You get CLIENT_ID / CLIENT_SECRET from Google Cloud Console →
// APIs & Services → Credentials → your OAuth 2.0 Client.
//
// The script opens a browser, you click "Allow" on YOUR Google account, and it
// captures the token automatically. Nothing is pasted by hand.

import http from 'node:http';
import { exec } from 'node:child_process';
import { spawnSync } from 'node:child_process';

const PORT = 4571;
const REDIRECT_URI = `http://localhost:${PORT}`;
const SCOPE = 'https://www.googleapis.com/auth/gmail.readonly';

const clientId = process.env.GMAIL_CLIENT_ID;
const clientSecret = process.env.GMAIL_CLIENT_SECRET;

if (!clientId || !clientSecret) {
  console.error('\nMissing GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET env vars.');
  console.error('Set them first, e.g. (PowerShell):');
  console.error('  $env:GMAIL_CLIENT_ID="..."; $env:GMAIL_CLIENT_SECRET="..."; node scripts/get-gmail-token.mjs\n');
  process.exit(1);
}

const authUrl =
  'https://accounts.google.com/o/oauth2/v2/auth?' +
  new URLSearchParams({
    client_id: clientId,
    redirect_uri: REDIRECT_URI,
    response_type: 'code',
    scope: SCOPE,
    access_type: 'offline',
    prompt: 'consent', // force a fresh refresh_token every time
  }).toString();

function openBrowser(url) {
  const cmd =
    process.platform === 'win32' ? `start "" "${url}"` :
    process.platform === 'darwin' ? `open "${url}"` :
    `xdg-open "${url}"`;
  exec(cmd, () => {});
}

async function exchangeCode(code) {
  const res = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      code,
      client_id: clientId,
      client_secret: clientSecret,
      redirect_uri: REDIRECT_URI,
      grant_type: 'authorization_code',
    }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(`Token exchange failed: ${res.status} ${JSON.stringify(data)}`);
  return data;
}

function trySetGithubSecret(token) {
  const r = spawnSync('gh', ['secret', 'set', 'GMAIL_REFRESH_TOKEN', '--body', token], {
    stdio: 'pipe',
    encoding: 'utf8',
    shell: true,
  });
  return r.status === 0;
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, REDIRECT_URI);
  const code = url.searchParams.get('code');
  const err = url.searchParams.get('error');

  if (err) {
    res.end(`Authorisation failed: ${err}. You can close this tab.`);
    console.error(`\n✗ Authorisation denied: ${err}\n`);
    server.close();
    process.exit(1);
  }
  if (!code) {
    res.end('Waiting for Google authorisation…');
    return;
  }

  try {
    const tokens = await exchangeCode(code);
    res.end('✓ Done. New Gmail token captured. You can close this tab and return to the terminal.');

    if (!tokens.refresh_token) {
      console.error('\n✗ Google did not return a refresh_token. Revoke prior access at');
      console.error('  https://myaccount.google.com/permissions and run this again.\n');
      server.close();
      process.exit(1);
    }

    console.log('\n✓ New refresh token obtained.');
    const ok = trySetGithubSecret(tokens.refresh_token);
    if (ok) {
      console.log('✓ Written to GitHub secret GMAIL_REFRESH_TOKEN. You are done.');
    } else {
      console.log('\n⚠ Could not set the GitHub secret automatically (gh not found / not in repo).');
      console.log('Copy this value into the GMAIL_REFRESH_TOKEN secret manually:\n');
      console.log(tokens.refresh_token + '\n');
    }
  } catch (e) {
    res.end('Something went wrong. Check the terminal.');
    console.error('\n✗ ' + e.message + '\n');
  } finally {
    server.close();
    process.exit(0);
  }
});

server.listen(PORT, () => {
  console.log('\nOpening Google sign-in in your browser…');
  console.log('If it does not open, paste this URL manually:\n');
  console.log(authUrl + '\n');
  console.log(`Listening on ${REDIRECT_URI} — sign in with the Gmail account the digest reads.`);
  openBrowser(authUrl);
});
