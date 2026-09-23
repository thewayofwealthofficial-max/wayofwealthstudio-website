# Daily subscriber email: fully automatic, sent through Resend

Every morning (06:47 UTC) this drafts one email in Joel's voice, checks it automatically, and sends it
to the list through Resend. No approval step. Joel gets a Telegram message with exactly what went out.

## Flow
1. **Sync**: MailerLite subscribers are copied into the Resend audience "General". Anyone who unsubscribed
   or bounced is stored as unsubscribed, and anyone who unsubscribes in Resend is unsubscribed in MailerLite.
2. **Intel** (optional): competitor email angles from Gmail. Angles only, never copied. If Gmail is down it
   drafts from Joel's core themes instead.
3. **Draft**: Anthropic, using `voice.mjs`.
4. **Safety checks** (`safety.mjs`): no persona name, no em dashes, no banned words, no invented numbers or
   research claims, no advice, only the call link, ends "Joel", sensible length. A failed draft is
   regenerated with the problems fed back. Three failures = the day is skipped and Joel is told.
5. **Send** as a Resend broadcast with an unsubscribe link, then Telegram Joel.

## Switch and modes
- **Scheduled sends only run when the repo variable `DAILY_EMAIL_ENABLED` is `true`.** Set anything else to pause.
- Manual run (Actions > Daily Subscriber Email > Run workflow): `dry` (send nothing), `test` (send to the
  private "Test" audience, Joel only), `live` (send to the list now).
- It never sends twice in one day.

## Files
`send-daily.mjs` orchestrator, `voice.mjs` voice and rules (edit this to change how it sounds),
`safety.mjs` checks, `resend.mjs` client, `sync-list.mjs` + `run-sync.mjs` list sync, `anthropic.mjs` drafting.

## Secrets (repo Settings > Secrets)
`RESEND_API_KEY` (email list sending ONLY), `ANTHROPIC_API_KEY`, `MAILERLITE_API` (for the sync),
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, and optionally `GMAIL_CLIENT_ID` / `GMAIL_CLIENT_SECRET` /
`GMAIL_REFRESH_TOKEN` for competitor intel. Optional variable `DAILY_EMAIL_FOOTER_ADDRESS` (postal address
shown in the footer).
