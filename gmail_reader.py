#!/usr/bin/env python3
"""gmail-reader — a small, reusable, READ-ONLY Gmail CLI.

The only OAuth scope ever requested is gmail.readonly. A token minted with
this scope physically cannot send, delete, or modify mail — the Gmail API
will reject any such call. This is the hard guarantee, not a convention.

Files (all kept next to this script):
  credentials.json  OAuth client secret you download from Google Cloud Console
  token.json        cached user token, created on first `auth` (gitignore this!)

Commands:
  auth                         Run the one-time OAuth flow; cache the token.
  whoami                       Print the authorized address + granted scopes.
  search "QUERY" [--max N]     List messages matching a Gmail search query.
  download "QUERY" --out DIR   Download all attachments from matching messages.
                               Writes a manifest.csv mapping each file to its
                               sender / subject / date / message id.

QUERY uses normal Gmail search syntax, e.g.:
  'has:attachment subject:slides after:2026/01/01 before:2026/05/01'
  'from:student@example.edu has:attachment filename:pptx'
"""
import argparse
import base64
import csv
import os
import re
import sys
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# READ-ONLY. Do not widen this. gmail.readonly cannot send/delete/modify.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

HERE = os.path.dirname(os.path.abspath(__file__))
CREDS_FILE = os.path.join(HERE, "credentials.json")
TOKEN_FILE = os.path.join(HERE, "token.json")


def get_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDS_FILE):
                sys.exit(
                    f"Missing {CREDS_FILE}.\n"
                    "Download an OAuth *Desktop app* client secret from Google\n"
                    "Cloud Console and save it there, then run: gmail-reader auth"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        os.chmod(TOKEN_FILE, 0o600)
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def cmd_auth(args):
    get_service()
    print("Authorized. Token cached at", TOKEN_FILE)


def cmd_whoami(args):
    svc = get_service()
    prof = svc.users().getProfile(userId="me").execute()
    print("Address:", prof.get("emailAddress"))
    print("Total messages:", prof.get("messagesTotal"))
    print("Scopes:", " ".join(SCOPES), "(read-only)")


def _header(msg, name):
    for h in msg.get("payload", {}).get("headers", []):
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _iter_message_ids(svc, query, max_results):
    got = 0
    page_token = None
    while True:
        resp = (
            svc.users()
            .messages()
            .list(userId="me", q=query, pageToken=page_token, maxResults=500)
            .execute()
        )
        for m in resp.get("messages", []):
            yield m["id"]
            got += 1
            if max_results and got >= max_results:
                return
        page_token = resp.get("nextPageToken")
        if not page_token:
            return


def cmd_search(args):
    svc = get_service()
    n = 0
    for mid in _iter_message_ids(svc, args.query, args.max):
        msg = (
            svc.users()
            .messages()
            .get(userId="me", id=mid, format="metadata",
                 metadataHeaders=["From", "Subject", "Date"])
            .execute()
        )
        n += 1
        print(f"[{mid}] {_header(msg,'Date')}")
        print(f"    From:    {_header(msg,'From')}")
        print(f"    Subject: {_header(msg,'Subject')}")
    print(f"\n{n} message(s) matched: {args.query!r}")


def _safe(s, fallback="unknown"):
    s = re.sub(r"[^\w.\-@ ]+", "_", (s or "")).strip().strip(".")
    return s[:120] or fallback


def _walk_parts(part):
    if not part:
        return
    yield part
    for sub in part.get("parts", []) or []:
        yield from _walk_parts(sub)


def cmd_download(args):
    svc = get_service()
    out = os.path.abspath(os.path.expanduser(args.out))
    os.makedirs(out, exist_ok=True)
    manifest_path = os.path.join(out, "manifest.csv")
    rows = []
    total_files = 0

    for mid in _iter_message_ids(svc, args.query, args.max):
        msg = svc.users().messages().get(userId="me", id=mid, format="full").execute()
        sender = _header(msg, "From")
        subject = _header(msg, "Subject")
        date = _header(msg, "Date")

        for part in _walk_parts(msg.get("payload")):
            filename = part.get("filename")
            body = part.get("body", {})
            if not filename:
                continue
            att_id = body.get("attachmentId")
            if att_id:
                att = (
                    svc.users().messages().attachments()
                    .get(userId="me", messageId=mid, id=att_id).execute()
                )
                data = att.get("data", "")
            else:
                data = body.get("data", "")
            if not data:
                continue
            raw = base64.urlsafe_b64decode(data.encode("utf-8"))
            # Prefix with sender + message id to keep collisions apart and
            # make per-student grouping obvious.
            who = _safe(re.sub(r".*<|>.*", "", sender) or sender, "sender")
            fname = f"{who}__{mid[:8]}__{_safe(filename)}"
            dest = os.path.join(out, fname)
            with open(dest, "wb") as f:
                f.write(raw)
            total_files += 1
            rows.append({
                "file": fname, "from": sender, "subject": subject,
                "date": date, "message_id": mid, "orig_filename": filename,
            })

    with open(manifest_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "file", "from", "subject", "date", "message_id", "orig_filename"])
        w.writeheader()
        w.writerows(rows)

    print(f"Downloaded {total_files} attachment(s) from "
          f"{len({r['message_id'] for r in rows})} message(s) to {out}")
    print(f"Manifest: {manifest_path}")


def main():
    p = argparse.ArgumentParser(prog="gmail-reader", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("auth", help="Run one-time OAuth flow").set_defaults(func=cmd_auth)
    sub.add_parser("whoami", help="Show authorized address + scopes").set_defaults(func=cmd_whoami)

    sp = sub.add_parser("search", help="List messages matching a Gmail query")
    sp.add_argument("query")
    sp.add_argument("--max", type=int, default=200)
    sp.set_defaults(func=cmd_search)

    dp = sub.add_parser("download", help="Download attachments from matching messages")
    dp.add_argument("query")
    dp.add_argument("--out", required=True, help="Output directory")
    dp.add_argument("--max", type=int, default=200)
    dp.set_defaults(func=cmd_download)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
