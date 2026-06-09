#!/usr/bin/env bash
#
# Interactive installer for the OlleBo mapserver on a local machine via Docker.
# Writes .env, creates host data directories, and brings the stack up.

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

err()  { printf '\033[31m%s\033[0m\n' "$*" >&2; }
info() { printf '\033[36m%s\033[0m\n' "$*"; }
ok()   { printf '\033[32m%s\033[0m\n' "$*"; }

# --- prerequisites -----------------------------------------------------------

if ! command -v docker >/dev/null 2>&1; then
  err "docker is not installed or not on PATH. Install Docker first: https://docs.docker.com/get-docker/"
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  err "docker compose v2 is required but not available. Install Docker Desktop or the docker-compose-plugin package."
  exit 1
fi

info "Installing the OlleBo mapserver in: $repo_root"
echo

# --- existing .env -----------------------------------------------------------

env_file="$repo_root/.env"
if [[ -f "$env_file" ]]; then
  read -r -p ".env already exists. Overwrite? [y/N] " overwrite
  if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
    info "Keeping existing .env. Skipping prompts."
    skip_prompts=1
  else
    skip_prompts=0
  fi
else
  skip_prompts=0
fi

# --- prompts -----------------------------------------------------------------

prompt() {
  # prompt VAR_NAME "Question" "default"
  local var="$1" question="$2" default="${3:-}" answer=""
  if [[ -n "$default" ]]; then
    read -r -p "$question [$default]: " answer
    answer="${answer:-$default}"
  else
    read -r -p "$question: " answer
  fi
  printf -v "$var" '%s' "$answer"
}

if [[ "$skip_prompts" -eq 0 ]]; then
  echo "Paste values from your ollebo.com mapserver entry. Press enter to accept defaults."
  echo

  prompt OLLEBO_KEY        "OLLEBO_KEY (from ollebo.com — leave blank if you don't have one yet)" ""
  prompt OLLEBO_SPACE_ID   "OLLEBO_SPACE_ID" "local"
  prompt TERRACOTTA_PUBLIC_URL \
                           "TERRACOTTA_PUBLIC_URL (browser-facing tile URL; use your ngrok/cloudflared https URL if exposing externally)" \
                           "http://localhost:5001"
  prompt API               "API (ollebo.com API base)" "https://www.ollebo.com/api/v1"

  cat > "$env_file" <<EOF
# Written by install/docker-install.sh
OLLEBO_KEY=${OLLEBO_KEY}
OLLEBO_SPACE_ID=${OLLEBO_SPACE_ID}
TERRACOTTA_PUBLIC_URL=${TERRACOTTA_PUBLIC_URL}
API=${API}
TERRACOTTA_DB_PATH=/data/db/terracotta.sqlite
TERRACOTTA_PROVIDER=sqlite
EOF
  ok "Wrote $env_file"
fi

# --- host data directories ---------------------------------------------------

for dir in maps cogs db; do
  if [[ ! -d "$repo_root/$dir" ]]; then
    mkdir -p "$repo_root/$dir"
    ok "Created $repo_root/$dir"
  fi
done

# --- bring up the stack ------------------------------------------------------

echo
info "Building images and starting containers (docker compose up -d --build)..."
docker compose up -d --build

echo
ok "Mapserver is up."
echo
echo "  Web UI:           http://localhost:8888"
echo "  Tile server:      http://localhost:5001"
echo "  Drop .tif files:  $repo_root/maps/"
echo
echo "Stop with:    docker compose down"
echo "Restart with: docker compose up -d"
echo "Logs:         docker compose logs -f"
