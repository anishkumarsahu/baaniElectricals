#!/usr/bin/env bash
set -euo pipefail
umask 077
action=${1:?Docker action required}
selected=${2:-}
repo=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo"
source scripts/docker-common.sh
configure_stack "${selected:-$repo/.env}" "${3:-}"
case "$action" in
    --docker-build) exec "${compose[@]}" build web ;;
    --docker-logs) exec "${compose[@]}" logs --follow --tail=100 ;;
    --docker-down) exec "${compose[@]}" --profile mysql down ;;
    --docker-migrate) fail 'Use --docker-up for the guarded release and migration workflow' ;;
    --docker-up) ;;
    *) fail 'Unknown Docker action' ;;
esac
validate_release_settings
# Never deploy a replacement or deleted migration history automatically.
deleted=$(git diff --name-only --diff-filter=D HEAD -- home/migrations activation/migrations) || fail 'Git checkout required'
[[ -z "$deleted" ]] || fail 'Deleted migration history detected; restore and review migrations before deployment'
for app in home activation; do
    [[ -f "$app/migrations/0001_initial.py" ]] || fail "Missing $app initial migration"
done
lock="/tmp/baani-deploy-$COMPOSE_PROJECT_NAME.lock"
mkdir "$lock" 2>/dev/null || fail "Deployment lock exists: $lock; investigate before removing"
paused=false
cleanup() {
    status=$?
    trap - EXIT
    if ((status != 0)) && [[ "$paused" == true ]]; then
        "${compose[@]}" stop web >/dev/null 2>&1 || true
        printf 'Release failed after downtime; web remains stopped. Inspect schema before retrying.\n' >&2
    fi
    rmdir "$lock" || true
    exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
git_revision=$(git rev-parse --verify --short=12 HEAD)
source_state=''
[[ -z "$(git status --porcelain --untracked-files=normal)" ]] || source_state=-dirty
build_id=$(od -An -N6 -tx1 /dev/urandom | tr -d ' \n')
export APP_IMAGE_TAG="release-$(date -u +%Y%m%dT%H%M%SZ)-$git_revision$source_state-$build_id"
export APP_IMAGE="$IMAGE_NAME:$APP_IMAGE_TAG"
printf 'Release: %s\nStorage: %s\n' "$APP_IMAGE" "$APP_DATA_ROOT"
"${compose[@]}" build web
"${compose[@]}" run --pull never --rm --no-deps -T storage-init
if [[ "$DATABASE_ENGINE" == mysql ]]; then
    "${compose[@]}" --profile mysql up -d --no-deps --wait --wait-timeout 240 mysql
fi
"${compose[@]}" up -d --wait --wait-timeout 240 redis
"${compose[@]}" run --pull never --rm --no-deps -T migrate check
"${compose[@]}" run --pull never --rm --no-deps -T migrate makemigrations --check --dry-run
paused=true
"${compose[@]}" --profile worker stop web worker
"${compose[@]}" run --pull never --rm --no-deps -T migrate migrate --noinput
"${compose[@]}" up -d --no-deps --no-build --force-recreate --pull never --wait --wait-timeout 240 web
paused=false
printf 'Healthy release: %s\nUse this exact image for management and rollback.\n' "$APP_IMAGE"
"${compose[@]}" ps -a
