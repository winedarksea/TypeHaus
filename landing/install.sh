#!/bin/sh
# Type:Haus bootstrapper: installs the `haus` CLI (build · check · render · serve).
# Modeled on the MinimapPR installer, but pipx-based — Type:Haus does not use uv.
# Usage:
#   curl -LsSf https://type-house.com/install.sh | sh
#   curl -LsSf https://type-house.com/install.sh | sh -s -- --base   # skip the server extras
set -eu

EXTRA="server"
for arg in "$@"; do
  case "$arg" in
    --base) EXTRA="" ;;
  esac
done

PACKAGE_SPEC="typehaus"
if [ -n "$EXTRA" ]; then
  PACKAGE_SPEC="typehaus[${EXTRA}]"
fi

# Interactive prompts must read from the controlling TTY, since stdin is the
# piped script itself when run as `curl ... | sh`.
TTY="/dev/tty"
if [ ! -r "$TTY" ]; then
  TTY=""
fi

info() { printf '==> %s\n' "$1"; }
err() { printf 'error: %s\n' "$1" >&2; }

prompt_yes_no() {
  # $1 = prompt text, default is "no"
  if [ -z "$TTY" ]; then
    echo "n"
    return
  fi
  reply=""
  if ! { printf '%s [y/N] ' "$1" > "$TTY"; read -r reply < "$TTY"; } 2>/dev/null; then
    echo "n"
    return
  fi
  case "$reply" in
    y|Y|yes|YES) echo "y" ;;
    *) echo "n" ;;
  esac
}

# ---------------------------------------------------------------------------
# 1. Find a Python 3.11+ interpreter
# ---------------------------------------------------------------------------
PY=""
for cand in python3.13 python3.12 python3.11 python3 python; do
  if command -v "$cand" >/dev/null 2>&1; then
    if "$cand" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)' 2>/dev/null; then
      PY="$cand"
      break
    fi
  fi
done
if [ -z "$PY" ]; then
  err "Python 3.11+ is required but was not found. Install it from https://python.org and re-run."
  exit 1
fi
info "Using $($PY --version 2>&1) at $(command -v "$PY")"

# ---------------------------------------------------------------------------
# 2. Ensure pipx (isolated CLI installs; no uv, no global site-packages churn)
# ---------------------------------------------------------------------------
if ! command -v pipx >/dev/null 2>&1; then
  info "pipx not found, installing it for the current user..."
  "$PY" -m pip install --user --quiet pipx || {
    err "could not install pipx via pip. Install pipx manually, then re-run."
    exit 1
  }
  "$PY" -m pipx ensurepath >/dev/null 2>&1 || true
fi

PIPX="pipx"
command -v pipx >/dev/null 2>&1 || PIPX="$PY -m pipx"

# pipx installs shims to ~/.local/bin by default; make sure it's on PATH for this script.
LOCAL_BIN="${PIPX_BIN_DIR:-$HOME/.local/bin}"
case ":$PATH:" in
  *":$LOCAL_BIN:"*) ;;
  *) PATH="$LOCAL_BIN:$PATH" ;;
esac
export PATH

# ---------------------------------------------------------------------------
# 3. Install Type:Haus
# ---------------------------------------------------------------------------
info "Installing $PACKAGE_SPEC (this can take a minute for the geometry deps)..."
# shellcheck disable=SC2086
$PIPX install --force "$PACKAGE_SPEC"

if ! command -v haus >/dev/null 2>&1; then
  err "haus was installed but is not yet on PATH."
  err "Add $LOCAL_BIN to your PATH (or restart your shell), then run: haus --help"
fi

# ---------------------------------------------------------------------------
# 4. Optional: scaffold + launch a house now
# ---------------------------------------------------------------------------
want_launch="$(prompt_yes_no 'Create a starter house and open the editor now?')"
if [ "$want_launch" = "y" ]; then
  HOUSE_DIR="$HOME/type-haus-starter"
  if [ ! -d "$HOUSE_DIR" ]; then
    info "Scaffolding $HOUSE_DIR..."
    haus new "$HOUSE_DIR" || err "haus new failed; you can run it yourself later."
  fi
  if [ -d "$HOUSE_DIR" ]; then
    info "Starting the editor at http://127.0.0.1:8000 ..."
    ( haus serve "$HOUSE_DIR" & )
    sleep 2
    URL="http://127.0.0.1:8000"
    case "$(uname -s 2>/dev/null || echo unknown)" in
      Darwin) open "$URL" >/dev/null 2>&1 || true ;;
      Linux) xdg-open "$URL" >/dev/null 2>&1 || true ;;
    esac
  fi
fi

# ---------------------------------------------------------------------------
# 5. Next steps
# ---------------------------------------------------------------------------
cat <<EOF

Type:Haus is installed.

  New house:  haus new my-house
  Edit:       haus serve my-house      # 2D/3D editor at http://127.0.0.1:8000
  Build:      haus build my-house      # -> out/model.json (+ IFC)
  Check:      haus check my-house
  Browser:    https://type-house.com/app   (no install — runs the engine in-browser)
  Uninstall:  pipx uninstall typehaus

EOF
