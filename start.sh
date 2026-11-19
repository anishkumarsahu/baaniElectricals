#!/usr/bin/env bash
# Local server and Docker Compose launcher. Migrations are always explicit.
set -euo pipefail
caller_dir=$PWD
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$repo"
host=127.0.0.1
port=8004
port_set=false
host_set=false
workers=2
timeout=120
env_file=
action=
db=
prod=false
sync=false
check=false
test_suite=false
migrate=false
collect=false
no_run=false
noreload=false
dry_run=false
help() {
    cat <<'HELP'
Baani Electricals launcher
Usage: ./start.sh [options]
  --host HOST, --port PORT    Listener (default 127.0.0.1:8004)
  --prod                      Use Gunicorn (default host 0.0.0.0)
  --workers N, --timeout N    Gunicorn settings (defaults 2, 120)
  --env PATH                  Environment file; Docker defaults to .env
  --sync, --check, --test     Sync dependencies, check Django, or run tests
  --migrate, --collectstatic  Run explicit local preparation steps
  --no-run, --noreload        Skip server startup, or disable development reload
  --dry-run                   Print local commands without executing them
  --docker-build              Build the image
  --docker-up                 Build, check, migrate and verify a release
  --docker-migrate            Use --docker-up for guarded migrations
  --docker-logs               Follow stack logs
  --docker-down               Stop stack without deleting volumes
  --db sqlite|mysql           Docker database selection (default from DATABASE_URL)
  --help                      Show this help

Docker commands use the selected env file for both Compose and containers.
For MySQL configure DATABASE_URL and MYSQL_* in that file and use --db mysql.
Before migrations, stop application writers and back up the database.
HELP
}
need_value() { [[ -n ${2:-} && $2 != -* ]] || { printf '%s requires a value\n' "$1" >&2; exit 1; }; }
positive() { [[ $2 =~ ^[0-9]+$ && ${#2} -le 5 ]] && ((10#$2 > 0)) || { printf '%s requires a positive integer\n' "$1" >&2; exit 1; }; }
while (($#)); do
    case $1 in
        -h|--help) help; exit 0 ;;
        -b|--host|--bind) need_value "$1" "${2:-}"; host=$2; host_set=true; shift 2 ;;
        -p|--port) need_value "$1" "${2:-}"; positive "$1" "$2"; ((10#$2 <= 65535)) || { echo 'Port must be 1-65535' >&2; exit 1; }; port=$2; port_set=true; shift 2 ;;
        -w|--workers) need_value "$1" "${2:-}"; positive "$1" "$2"; workers=$2; shift 2 ;;
        --timeout) need_value "$1" "${2:-}"; positive "$1" "$2"; timeout=$2; shift 2 ;;
        -e|--env|--env-file) need_value "$1" "${2:-}"; env_file=$2; shift 2 ;;
        --db) need_value "$1" "${2:-}"; case $2 in sqlite|sqlite3) db=sqlite ;; mysql) db=mysql ;; *) echo 'Choose sqlite or mysql' >&2; exit 1 ;; esac; shift 2 ;;
        --docker-build|--docker-up|--docker-migrate|--docker-logs|--docker-down) [[ -z $action ]] || { echo 'Choose one Docker action' >&2; exit 1; }; action=$1; shift ;;
        --prod|--production) prod=true; shift ;;
        -s|--sync) sync=true; shift ;;
        -c|--check) check=true; shift ;;
        -t|--test) test_suite=true; shift ;;
        -m|--migrate) migrate=true; shift ;;
        --collectstatic) collect=true; shift ;;
        -n|--no-run) no_run=true; shift ;;
        --noreload) noreload=true; shift ;;
        -d|--dry-run) dry_run=true; shift ;;
        *) printf 'Unknown option: %s\n' "$1" >&2; exit 1 ;;
    esac
done
if [[ -n $env_file && $env_file != /* ]]; then env_file="$caller_dir/$env_file"; fi
if [[ -n $action ]]; then
    [[ $sync == false && $check == false && $test_suite == false && $migrate == false && $collect == false && $no_run == false && $noreload == false && $prod == false && $dry_run == false && $host_set == false ]] || { echo 'Local options cannot be combined with Docker actions' >&2; exit 1; }
    if [[ $port_set == true ]]; then export PORT="$port"; fi
    exec bash "$repo/scripts/docker-deploy.sh" "$action" "$env_file" "$db"
fi
[[ -z $db || $db == sqlite ]] || { echo '--db is only supported for Docker; set DATABASE_URL for local use' >&2; exit 1; }
uv_args=(uv run)
if [[ -n $env_file ]]; then
    [[ -f $env_file ]] || { echo 'Selected environment file does not exist' >&2; exit 1; }
    uv_args+=(--env-file "$env_file")
fi
run() {
    if [[ $dry_run == true ]]; then printf '[dry-run]'; printf ' %q' "$@"; printf '\n'; else "$@"; fi
}
if [[ $sync == true ]]; then run uv sync; fi
if [[ $check == true ]]; then run "${uv_args[@]}" python manage.py check; fi
if [[ $test_suite == true ]]; then run "${uv_args[@]}" python manage.py test; fi
if [[ $migrate == true ]]; then run "${uv_args[@]}" python manage.py migrate --noinput; fi
if [[ $collect == true ]]; then run "${uv_args[@]}" python manage.py collectstatic --noinput; fi
[[ $no_run == false ]] || exit 0
if [[ $prod == true ]]; then
    if [[ $host_set == false ]]; then host=0.0.0.0; fi
    cmd=("${uv_args[@]}" gunicorn baani.wsgi:application --bind "$host:$port" --workers "$workers" --timeout "$timeout")
else
    cmd=("${uv_args[@]}" python manage.py runserver "$host:$port")
    if [[ $noreload == true ]]; then cmd+=(--noreload); fi
fi
if [[ $dry_run == true ]]; then run "${cmd[@]}"; else exec "${cmd[@]}"; fi
