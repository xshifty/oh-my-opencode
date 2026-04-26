#!/usr/bin/env bash
set -euo pipefail

# Discover OpenCode config directory
OPENCODE_CONFIG="${OPENCODE_CONFIG:-}"

discover_opencode_config() {
  # Respect explicit override via env var or CLI arg
  if [ -n "${OPENCODE_CONFIG:-}" ]; then
    return 0
  fi

  # Try default path first
  if [ -d "$HOME/.config/opencode" ]; then
    OPENCODE_CONFIG="$HOME/.config/opencode"
    return 0
  fi

  # Check XDG_CONFIG_HOME
  local xdg_config="${XDG_CONFIG_HOME:-$HOME/.config}"
  if [ -d "$xdg_config/opencode" ]; then
    OPENCODE_CONFIG="$xdg_config/opencode"
    return 0
  fi

  # Try macOS Application Support
  if [ -d "$HOME/Library/Application Support/opencode" ]; then
    OPENCODE_CONFIG="$HOME/Library/Application Support/opencode"
    return 0
  fi

  # Search common locations
  for dir in \
    "$HOME/.config/opencode" \
    "$XDG_CONFIG_HOME/opencode" \
    "$HOME/Library/Application Support/opencode"; do
    if [ -d "$dir" ]; then
      OPENCODE_CONFIG="$dir"
      return 0
    fi
  done

  echo "OpenCode config directory not found." >&2
  echo "Default locations checked:" >&2
  echo "  $HOME/.config/opencode" >&2
  echo "  ${XDG_CONFIG_HOME:-$HOME/.config}/opencode" >&2
  echo "  $HOME/Library/Application Support/opencode" >&2
  return 1
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENTS_DIR="$SCRIPT_DIR/agents"

if [ ! -d "$AGENTS_DIR" ]; then
  echo "Error: agents/ directory not found at $AGENTS_DIR" >&2
  exit 1
fi

# Parse CLI args (env var takes precedence)
while [ $# -gt 0 ]; do
  case "$1" in
    --target) OPENCODE_CONFIG="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# Discover config dir (env var > CLI arg > auto-discover)
discover_opencode_config || {
  echo "" >&2
  echo "You can set OPENCODE_CONFIG env var and re-run:" >&2
  echo '  export OPENCODE_CONFIG=~/.config/opencode' >&2
  echo '  ./install.sh' >&2
  exit 1
}

echo "Installing to $OPENCODE_CONFIG ..."

# Create config dir if it doesn't exist
if [ ! -d "$OPENCODE_CONFIG" ]; then
  mkdir -p "$OPENCODE_CONFIG"
  echo "Created $OPENCODE_CONFIG"
fi

# Symlink each top-level item from agents/ into opencode config
for item in "$AGENTS_DIR"/*; do
  name="$(basename "$item")"

  # Skip scripts and templates — handled explicitly below for clarity
  case "$name" in
    scripts|templates) continue ;;
  esac

  target="$OPENCODE_CONFIG/$name"

  if [ -L "$target" ] || [ -e "$target" ]; then
    rm -f "$target"
  fi

  ln -s "$item" "$target"
  echo "  $name -> symlinked"
done

# Explicitly symlink scripts/ and templates/ folders
for folder in scripts templates; do
  src="$AGENTS_DIR/$folder"
  target="$OPENCODE_CONFIG/$folder"

  if [ -d "$src" ]; then
    if [ -L "$target" ] || [ -e "$target" ]; then
      rm -rf "$target"
    fi
    ln -s "$src" "$target"
    echo "  $folder/ -> symlinked (scripts/templates)"
  fi
done

echo ""
echo "Done. OpenCode config directory: $OPENCODE_CONFIG"
