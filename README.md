# gmail-reader

A small, **read-only** Gmail CLI. The only OAuth scope it ever requests is
`gmail.readonly`, so the credential **physically cannot send, delete, or
modify** mail — the Gmail API rejects any such call for this token.

## Install

```
git clone <this-repo> gmail-reader
cd gmail-reader
./setup.sh            # create venv + install deps
./setup.sh --link     # (optional) also symlink `gmail-reader` onto your PATH
```

Requires Python 3.9+. Everything installs into a local `.venv` — nothing global.

## One-time Google setup

> Google recently renamed the "OAuth consent screen" to the **Google Auth
> Platform**. These steps match the current (2025+) console.

### 1. Create a project and enable the Gmail API
1. Go to <https://console.cloud.google.com/> and create a project (or pick one).
2. **APIs & Services → Library →** search "Gmail API" → **Enable**.

### 2. Configure the Google Auth Platform
3. Open **APIs & Services → OAuth consent screen** (a.k.a. Google Auth
   Platform). If you see *"Google Auth Platform not configured yet"*, click
   **Get started** and complete the wizard:
   - **App Information:** app name (e.g. `gmail-reader`) + a user support email.
   - **Audience:** choose **External**. (Internal only applies to Google
     Workspace orgs. External + test mode is free and permanent for personal
     use — no app verification needed.)
   - **Contact Information:** your email.
   - **Finish:** agree to the policy and create.
4. Still under the Google Auth Platform, open **Audience → Test users →
   Add users** and add your own Gmail address. In test mode only listed users
   can authorize; without this, `gmail-reader auth` is blocked.
   - You can ignore the "Sign in with Google" branding and the Scopes screens —
     the CLI requests the `gmail.readonly` scope itself at runtime.

### 3. Create the OAuth client (the credentials.json)
5. Open **Clients → Create client** (under the Google Auth Platform; older
   consoles list this as **Credentials → Create Credentials → OAuth client ID**).
   - Application type: **Desktop app** → Create.
   - **Download JSON** and save it as **`credentials.json`** in this project
     folder (next to `gmail_reader.py`).

### 4. Authorize
```
./gmail-reader auth      # or just `gmail-reader auth` if you used --link
```
Opens a browser, you approve (you'll see an "unverified app" notice — that's
expected for a personal test-mode app; click through via **Advanced → Go to
gmail-reader**), and a `token.json` is cached in this folder. Done once.

## Usage
```
gmail-reader whoami
gmail-reader search "has:attachment subject:slides after:2026/01/01"
gmail-reader download "has:attachment filename:pptx" --out ./slides
```
`download` saves every attachment from matching messages and writes a
`manifest.csv` (file → sender / subject / date / message id) for easy grouping.

`QUERY` is standard Gmail search syntax: `from:`, `subject:`, `has:attachment`,
`filename:pptx`, `after:YYYY/MM/DD`, `before:YYYY/MM/DD`, `label:`, etc.

## Revoking access
- Delete `token.json` to forget the cached token, and/or
- Revoke at <https://myaccount.google.com/permissions>.

## Security notes
- Scope is hard-coded to `gmail.readonly`; widening it requires editing the
  source and re-consenting.
- `credentials.json` and `token.json` are gitignored — they are personal
  secrets and must never be committed.

## Files
- `gmail_reader.py` — the CLI
- `gmail-reader` — Python launcher (resolves symlinks; uses the local `.venv`)
- `setup.sh` — creates the venv, installs deps, optional `--link`
- `requirements.txt` — Python dependencies
- `credentials.json` / `token.json` — your secrets (gitignored)
