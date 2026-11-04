Agent check-ins. Claude's scheduled tasks overwrite latest.md and push to this branch;
.github/workflows/agent-checkin.yml sends it to Joel on Telegram via Fred.
First line = title (starts with "# "), the rest = body. Keep it under ~3,500 characters.
Commit messages end with [skip netlify] so no site build runs.
