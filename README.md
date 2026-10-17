# agy-account

Headless, seamless Google account switcher for Google Antigravity CLI (`agy`) on Windows.

## Why this exists
By default, switching accounts in Antigravity requires running `/logout` and going through the browser OAuth consent flow each time.

However, Antigravity stores your OAuth credentials (including a persistent Google OAuth `refresh_token`) in **Windows Credential Manager** under `gemini:antigravity`. 

`agy-account` snapshots each account's credential blob once, and then allows you to swap active accounts instantly in the background without opening the browser.

## Installation on Any Windows Machine

1. Clone or copy this repository anywhere on your PC (e.g. `C:\Projects\agy-account`).
2. Run `install.bat` (or double-click it in File Explorer).
   - It automatically detects the location and writes the shim into `%LOCALAPPDATA%\agy\bin\agy-account.bat`.
   - Because `%LOCALAPPDATA%\agy\bin` is already in `PATH` by default with Antigravity CLI, `agy-account` immediately becomes available in all terminals.

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
