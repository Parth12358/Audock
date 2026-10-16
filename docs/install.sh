#!/bin/sh
# Audock installer for macOS and Linux.
#
#   curl -fsSL https://parth12358.github.io/Audock/install.sh | sh
#
# Installs the release binary as ~/.local/bin/audock (no sudo needed) and checks that it runs.
#   AUDOCK_INSTALL_DIR=/usr/local/bin   install somewhere else (may need sudo)
#   AUDOCK_VERSION=v0.2.0               pin a release instead of the latest
set -eu

REPO="Parth12358/Audock"
DIR="${AUDOCK_INSTALL_DIR:-$HOME/.local/bin}"
VER="${AUDOCK_VERSION:-latest}"
OS="$(uname -s)"
ARCH="$(uname -m)"

from_source() {
  echo "audock: there is no prebuilt binary for $OS/$ARCH yet. Run it from source (needs Python 3):"
  echo "  git clone https://github.com/$REPO.git ~/audock-src"
  echo "  mkdir -p \"$DIR\" && ln -sf ~/audock-src/tools/audock \"$DIR/audock\""
  exit 1
}

case "$OS/$ARCH" in
  Linux/x86_64 | Linux/amd64) ASSET=audock-linux-x86_64 ;;
  Darwin/arm64) ASSET=audock-macos-arm64 ;;
  Darwin/x86_64 | Linux/aarch64 | Linux/arm64) from_source ;;
  *) echo "audock: unsupported platform $OS/$ARCH" >&2; exit 1 ;;
esac

if [ "$VER" = latest ]; then
  URL="https://github.com/$REPO/releases/latest/download/$ASSET"
else
  URL="https://github.com/$REPO/releases/download/$VER/$ASSET"
fi

TMP="$(mktemp "${TMPDIR:-/tmp}/audock.XXXXXX")"
trap 'rm -f "$TMP"' EXIT INT TERM

echo "Downloading $ASSET ($VER)…"
fail() { echo "audock: download failed — is $VER a published release? See https://github.com/$REPO/releases" >&2; exit 1; }
if command -v curl >/dev/null 2>&1; then
  curl -fSL --progress-bar -o "$TMP" "$URL" || fail
elif command -v wget >/dev/null 2>&1; then
  wget -qO "$TMP" "$URL" || fail
else
  echo "audock: need curl or wget to download" >&2; exit 1
fi

chmod 755 "$TMP"
if [ "$OS" = Darwin ]; then
  xattr -d com.apple.quarantine "$TMP" 2>/dev/null || true  # unsigned binary: skip Gatekeeper prompt
fi
if ! "$TMP" --help >/dev/null 2>&1; then
  echo "audock: the downloaded binary did not run on this machine" >&2; exit 1
fi

mkdir -p "$DIR"
mv "$TMP" "$DIR/audock"
echo "Installed $DIR/audock"

case ":$PATH:" in
  *":$DIR:"*) ;;
  *) echo
     echo "$DIR is not on your PATH yet. Add this line to ~/.zshrc or ~/.bashrc, then open a new terminal:"
     echo "  export PATH=\"$DIR:\$PATH\"" ;;
esac
echo
echo "Next, in a new or existing Obsidian vault:"
echo "  audock init --dry-run   # preview; writes nothing"
echo "  audock init"
