#!/usr/bin/env bash
# Parse Compose dotenv files with Compose, never execute them as shell code.
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
configure_stack() {
    command -v docker >/dev/null || fail 'Docker with Compose is required'
    local selected=${1:-.env} requested_db=${2:-} resolved key value
    [[ -f "$selected" ]] || fail 'Selected environment file does not exist'
    export APP_ENV_FILE="$(cd "$(dirname "$selected")" && pwd)/$(basename "$selected")"
    compose=(docker compose --env-file "$APP_ENV_FILE" -f "$repo/docker-compose.yml")
    resolved=$(docker compose --env-file "$APP_ENV_FILE" -f - config --environment <<'COMPOSE'
name: baani-configuration-probe
services:
  probe:
    image: scratch
COMPOSE
    ) || fail 'Invalid Compose environment'
    while IFS='=' read -r key value; do
        case "$key" in
            COMPOSE_PROJECT_NAME) [[ "$value" == baani-configuration-probe ]] || export "$key=$value" ;;
            PROJECT_NAME|DEPLOY_ENV|IMAGE_NAME|APP_IMAGE_TAG|VPS_STORAGE_ROOT|APP_DATA_ROOT|MEDIA_DATA_DIR|MYSQL_DATA_DIR|PORT|APP_PORT|DATABASE_URL|MYSQL_DATABASE|MYSQL_USER|MYSQL_PASSWORD|MYSQL_ROOT_PASSWORD|SECRET_KEY|ALLOWED_HOSTS)
                export "$key=$value" ;;
        esac
    done <<< "$resolved"
    export PROJECT_NAME=${PROJECT_NAME:-baani-electricals} DEPLOY_ENV=${DEPLOY_ENV:-production}
    export COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-$PROJECT_NAME-$DEPLOY_ENV}
    [[ "$COMPOSE_PROJECT_NAME" =~ ^[a-z0-9][a-z0-9_-]*$ && "$PROJECT_NAME" =~ ^[a-z0-9][a-z0-9_-]*$ && "$DEPLOY_ENV" =~ ^[a-z0-9][a-z0-9_-]*$ ]] || fail 'Invalid project or environment name'
    export IMAGE_NAME=${IMAGE_NAME:-$PROJECT_NAME} PORT=${PORT:-${APP_PORT:-8004}}
    [[ "$PORT" =~ ^[0-9]+$ && ${#PORT} -le 5 ]] && ((10#$PORT > 0 && 10#$PORT < 65536)) || fail 'PORT must be 1-65535'
    if [[ -z ${VPS_STORAGE_ROOT:-} && $(uname -s) == Darwin ]]; then export VPS_STORAGE_ROOT="$HOME/docker-apps"; fi
    export APP_DATA_ROOT=${APP_DATA_ROOT:-${VPS_STORAGE_ROOT:-/srv/apps}/$PROJECT_NAME/$DEPLOY_ENV}
    [[ "$APP_DATA_ROOT" == /* && "$APP_DATA_ROOT" != / ]] || fail 'Storage root must be an absolute project directory'
    export MEDIA_DATA_DIR=${MEDIA_DATA_DIR:-$APP_DATA_ROOT/media} MYSQL_DATA_DIR=${MYSQL_DATA_DIR:-$APP_DATA_ROOT/mysql}
    [[ "$MEDIA_DATA_DIR" == /* && "$MEDIA_DATA_DIR" != / && "$MYSQL_DATA_DIR" == /* && "$MYSQL_DATA_DIR" != / ]] || fail 'Storage paths must be absolute and cannot be /'
    case "${requested_db:-${DATABASE_URL%%:*}}" in
        sqlite|sqlite3) export DATABASE_ENGINE=sqlite3 DATABASE_URL=sqlite:////data/db.sqlite3 ;;
        mysql) export DATABASE_ENGINE=mysql; [[ ${DATABASE_URL:-} == mysql://* ]] || fail 'Set DATABASE_URL to a MySQL URL for --db mysql' ;;
        *) fail 'Select sqlite or mysql and configure DATABASE_URL' ;;
    esac
    "${compose[@]}" config --quiet
}
validate_release_settings() {
    [[ -n ${SECRET_KEY:-} && "$SECRET_KEY" != replace-with-a-unique-secret-key ]] || fail 'Set a private SECRET_KEY'
    [[ -n ${ALLOWED_HOSTS:-} ]] || fail 'Set ALLOWED_HOSTS'
    if [[ $DATABASE_ENGINE == mysql ]]; then
        [[ -n ${MYSQL_PASSWORD:-} && -n ${MYSQL_ROOT_PASSWORD:-} ]] || fail 'Set MYSQL_PASSWORD and MYSQL_ROOT_PASSWORD'
        [[ ${MYSQL_USER:-baani} != root ]] || fail 'MYSQL_USER must be a non-root application account'
    fi
}
