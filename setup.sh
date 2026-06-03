#!/bin/bash
# Portable setup for gmail-reader. Run from anywhere after cloning:
#   ./setup.sh            # create venv + install deps
#   ./setup.sh --link     # also symlink `gmail-reader` onto your PATH
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

PYTHON="${PYTHON:-python3}"
echo "Creating venv with $($PYTHON --version)..."
"$PYTHON" -m venv .venv
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet -r requirements.txt
chmod +x gmail-reader
echo "Dependencies installed."

if [ "$1" = "--link" ]; then
  # Pick the first writable, PATH-listed bin dir; fall back to ~/.local/bin.
  TARGET=""
  for d in "$HOME/bin" "$HOME/.local/bin" /usr/local/bin; do
    case ":$PATH:" in *":$d:"*) [ -d "$d" ] && [ -w "$d" ] && TARGET="$d" && break;; esac
  done
  if [ -z "$TARGET" ]; then
    TARGET="$HOME/.local/bin"; mkdir -p "$TARGET"
    echo "Note: $TARGET may not be on your PATH. Add it with:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
  fi
  ln -sf "$HERE/gmail-reader" "$TARGET/gmail-reader"
  echo "Linked: $TARGET/gmail-reader -> $HERE/gmail-reader"
fi

echo
echo "Next: add an OAuth Desktop client secret as credentials.json here,"
echo "then run:  ./gmail-reader auth   (see README.md)"
