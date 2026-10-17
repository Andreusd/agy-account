# agy-account

Headless, seamless Google account switcher for Google Antigravity CLI (`agy`) on Windows.

## Why this exists
By default, switching accounts in Antigravity requires running `/logout` and going through the browser OAuth consent flow each time.

However, Antigravity stores your OAuth credentials (including a persistent Google OAuth `refresh_token`) in **Windows Credential Manager** under `gemini:antigravity`. 

`agy-account` snapshots each account's credential blob once, and then allows you to swap active accounts instantly in the background without opening the browser.

## Commands

```bash
# List all saved profiles and show the active one
agy-account list

# Save currently active account (alias is optional; defaults to the email username before '@')
agy-account save [alias]

# Switch instantly to a saved profile by alias or email
agy-account switch <alias>

# Delete a saved profile
agy-account delete <alias>

# Show the active email
agy-account current
```

## Storage Locations
- **Windows Credential Manager**:
  - Active: `gemini:antigravity`
  - Backup profiles: `gemini:antigravity:profile:<alias>`
- **Filesystem profiles**:
  - `%USERPROFILE%\.gemini\antigravity-accounts\<alias>.json`
