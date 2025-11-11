#!/usr/bin/env bash
set -euo pipefail

# --- CONFIG: set via flags or env vars ---
DOCKERHUB_USER="${DOCKERHUB_USER:-0504202509}"
IMAGE_NAME="${IMAGE_NAME:-charge-qkd}"
PUSH="true"                                               # default: push after build
USE_BUILDX="${USE_BUILDX:-false}"                         # set true to build multi-arch
PLATFORMS="${PLATFORMS:-linux/amd64}"                     # e.g. "linux/amd64,linux/arm64"
DOCKER_HOST="${DOCKER_HOST:-ssh://amir@home-nuc.local}"
EXTRA_BUILD_ARGS=()                                       # e.g. ("--build-arg" "FOO=bar")
# ----------------------------------------

usage() {
  cat <<EOF
Usage: $(basename "$0") -u <dockerhub_user> [-i <image_name>] [--no-push] [--buildx] [--platforms <list>] [-H <docker_host>]
Examples:
  DOCKERHUB_TOKEN=... DOCKERHUB_USER=you ./build.sh -i myproj
  ./build.sh -u you -i myproj --no-push
  ./build.sh -u you -i myproj --buildx --platforms "linux/amd64,linux/arm64"
  ./build.sh -u you -i myproj -H ssh://me@my-remote
EOF
}

# --- parse args ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    -u|--user) DOCKERHUB_USER="$2"; shift 2;;
    -i|--image) IMAGE_NAME="$2"; shift 2;;
    --no-push) PUSH="false"; shift;;
    --buildx) USE_BUILDX="true"; shift;;
    --platforms) PLATFORMS="$2"; shift 2;;
    -H|--host) DOCKER_HOST="$2"; export DOCKER_HOST; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 1;;
  esac
done

if [[ -z "${DOCKERHUB_USER}" ]]; then
  echo "ERROR: Docker Hub user is required (-u or DOCKERHUB_USER env)." >&2
  exit 1
fi

IMAGE="${DOCKERHUB_USER}/${IMAGE_NAME}"

# --- Git metadata (robust even if not exactly on a tag) ---
is_git_repo=true
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || is_git_repo=false

if $is_git_repo; then
  BRANCH="$(git rev-parse --abbrev-ref HEAD)"
  SHA="$(git rev-parse --short=12 HEAD)"
  REMOTE_URL="$(git config --get remote.origin.url || true)"
  DATE_ISO="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  if git describe --tags --exact-match >/dev/null 2>&1; then
    EXACT_TAG="$(git describe --tags --exact-match)"
    VERSION="$EXACT_TAG"
    LAST_TAG="$EXACT_TAG"
  else
    LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo 0.0.0)"
    VERSION="${LAST_TAG}-${BRANCH}-${SHA}"
  fi
else
  BRANCH="no-git"
  SHA="$(date +%s)"
  REMOTE_URL=""
  DATE_ISO="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  LAST_TAG="0.0.0"
  VERSION="0.0.0-standalone-${SHA}"
fi

# --- Tag strategy ---
# Always: :<version> and :<branch>-<sha>
# If branch is main/master: also :latest
TAGS=("${IMAGE}:${VERSION}")
if [[ "${BRANCH}" == "main" || "${BRANCH}" == "master" ]]; then
  TAGS+=("${IMAGE}:latest")
fi

echo "Building image:"
printf '  %s\n' "${TAGS[@]}"
echo

# --- Build command ---
LABELS=(
  "--label" "org.opencontainers.image.created=${DATE_ISO}"
  "--label" "org.opencontainers.image.revision=${SHA}"
  "--label" "org.opencontainers.image.version=${VERSION}"
  "--label" "org.opencontainers.image.source=${REMOTE_URL}"
  "--label" "org.opencontainers.image.ref.name=${BRANCH}"
)

if [[ "${USE_BUILDX}" == "true" ]]; then
  # buildx multi-arch
  docker buildx create --use >/dev/null 2>&1 || true
  docker buildx build \
    "${LABELS[@]}" \
    "${EXTRA_BUILD_ARGS[@]}" \
    --platform "${PLATFORMS}" \
    $(printf -- ' -t %q' "${TAGS[@]}") \
    --push="${PUSH}" \
    .
else
  # classic single-arch
  docker build \
    "${LABELS[@]}" \
    "${EXTRA_BUILD_ARGS[@]}" \
    $(printf -- ' -t %q' "${TAGS[@]}") \
    .
  if [[ "${PUSH}" == "true" ]]; then
    for t in "${TAGS[@]}"; do docker push "$t"; done
  fi
fi

echo
echo "Done. Built tags:"
printf '  %s\n' "${TAGS[@]}"

if [[ "${PUSH}" == "true" ]]; then
  echo "Pushed to Docker Hub."
else
  echo "Not pushed (use --no-push to skip, default is push when using buildx)."
fi
