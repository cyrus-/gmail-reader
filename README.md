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

### 1. Get an OAuth client secret (Google Cloud Console)
1. Go to <https://console.cloud.google.com/> and create a project (or pick one).
2. **APIs & Services → Library →** search "Gmail API" → **Enable**.
3. **APIs & Services → OAuth consent screen:**
   - User type: **External** → Create.
   - Fill app name + your email; Save.
   - **Test users:** add your own Gmail address.
     (Test mode is fine forever for personal use — no app verification needed.)
   - **Scopes:** leave blank; the CLI requests `gmail.readonly` at runtime.
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID:**
   - Application type: **Desktop app** → Create.
   - **Download JSON** and save it as **`credentials.json`** in this project
     folder (next to `gmail_reader.py`).

### 2. Authorize
```
./gmail-reader auth      # or just `gmail-reader auth` if you used --link
```
Opens a browser, you approve, and a `token.json` is cached in this folder. Once.

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
- `gmail-reader` — launcher (resolves symlinks; uses the local `.venv`)
- `setup.sh` — creates the venv, installs deps, optional `--link`
- `requirements.txt` — Python dependencies
- `credentials.json` / `token.json` — your secrets (gitignored)
