# Command Reference & Cheat Sheet (`COMMANDS.md`)

This document provides a comprehensive command reference for setting up, running, testing, and deploying the **Baani Electricals (BSSAC)** application.

---

## 🛠️ Environment & Package Management (`uv` & `pip`)

### Using `uv` (Recommended)

```bash
# Initialize virtual environment
uv venv

# Activate virtual environment
# macOS / Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# Install all locked dependencies
uv sync

# Add a new dependency to pyproject.toml
uv add <package_name>

# Export updated dependencies to requirements.txt for legacy systems
uv pip compile pyproject.toml -o requirements.txt
```

### Using Standard `pip`

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies from requirements.txt
pip install -r requirements.txt
```

---

## 🚀 Local Development Server

```bash
# Run server on default port configured in .env (8004)
python manage.py runserver 0.0.0.0:8004

# Run with explicit port override
python manage.py runserver 8000

# Open interactive Django Python shell
python manage.py shell
```

---

## 🗄️ Database Management & Migrations

```bash
# Check current migration status across all apps
python manage.py showmigrations

# Generate new migrations after altering models.py
python manage.py makemigrations

# Generate migrations for a specific app
python manage.py makemigrations home

# Apply all pending migrations
python manage.py migrate

# Inspect generated SQL before running migration (e.g. migration 0005 of home)
python manage.py sqlmigrate home 0005

# Rollback an app to a specific migration
python manage.py migrate home 0004
```

---

## 👤 User & Group Management

```bash
# Create a new superuser for the Django admin panel
python manage.py createsuperuser

# Change a user password via CLI
python manage.py changepassword <username>
```

---

## 📁 Static & Media Files

```bash
# Collect all static files into STATIC_ROOT (staticfiles/) for WhiteNoise
python manage.py collectstatic --noinput

# Clear collected static files
python manage.py collectstatic --clear --noinput
```

---

## 📨 Background Workers & Daemons

```bash
# Run the WhatsApp / SMS notification processor in foreground
python sms_worker.py

# Run in background with log redirection (Linux/macOS)
nohup python sms_worker.py > sms_worker.log 2>&1 &

# Inspect running worker process
ps aux | grep sms_worker.py
```

---

## 🧹 Code Quality, Linting & Formatting

```bash
# Check for linting issues and style violations using Ruff
uv run ruff check .

# Automatically apply safe linting fixes
uv run ruff check --fix .

# Format all Python files according to project standards
uv run ruff format .

# Check without modifying files
uv run ruff format --check .
```

---

## 🧪 Testing & Quality Assurance

```bash
# Run all Django integration & E2E tests (auto-uses in-memory SQLite & fast MD5 hasher)
uv run python manage.py test

# Run tests for a specific test module
uv run python manage.py test home.tests.test_auth_e2e
uv run python manage.py test home.tests.test_collections_e2e
uv run python manage.py test home.tests.test_sales_e2e
uv run python manage.py test home.tests.test_cash_counter_e2e
uv run python manage.py test home.tests.test_master_data_e2e
uv run python manage.py test home.tests.test_attendance_e2e
uv run python manage.py test home.tests.test_sms_worker_e2e
uv run python manage.py test home.tests.test_reports_and_system_e2e
uv run python manage.py test activation

# Verify branded error responses with DEBUG disabled in the tests
uv run python manage.py test home.tests.test_error_pages home.tests.test_media_delivery

# Run test coverage report
uv run --with coverage coverage run --source=home,activation manage.py test
uv run --with coverage coverage report --omit="*/migrations/*,*/tests/*"

# Run with verbose output
uv run python manage.py test -v 2
```

---

## 🚢 Production Execution (Gunicorn)

```bash
# Start Gunicorn production server with 4 worker processes
gunicorn baani.wsgi:application \
    --bind 0.0.0.0:8004 \
    --workers 4 \
    --threads 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
```

---

## ⚡ Redis & Caching Verification

```bash
# Test local Redis connection
redis-cli ping
# Expected output: PONG

# Inspect cache keys in database index 1 (default from .env)
redis-cli -n 1 keys "*"

# Flush Redis cache in index 1
redis-cli -n 1 flushdb
```

---

## 🔧 Troubleshooting & Common Scenarios

### 1. Port 8004 Already in Use
```bash
# Find process holding port 8004
lsof -i :8004

# Terminate process by PID
kill -9 <PID>
```

### 2. WeasyPrint Missing System Dependencies (macOS)
If PDF generation throws `OSError: dlopen()`:
```bash
brew install pango libffi cairo gdk-pixbuf
```

### 3. Database Locked (SQLite)
If `sqlite3.OperationalError: database is locked` occurs during concurrent operations:
- Ensure no lingering `sms_worker.py` or development shell instances are holding write locks.
- For multi-user concurrent testing, switch to MySQL in `.env`:
  ```ini
  DATABASE_URL=mysql://root:password@127.0.0.1:3306/baani
  ```

## Docker deployment

Configure a private `.env` with a unique secret, allowed hosts, and `DATABASE_URL`.
For MySQL, configure `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, and
`MYSQL_ROOT_PASSWORD`; the URL must match the non-root application credentials.
Use an absolute `VPS_STORAGE_ROOT` shared with Docker Desktop on macOS. The
launcher defaults to `~/docker-apps` on macOS and `/srv/apps` on Linux.

```bash
./start.sh --env .env --db mysql --docker-build
./start.sh --env .env --db mysql --docker-up
./start.sh --env .env --db mysql --docker-logs
./start.sh --env .env --db mysql --docker-down
```

The release builds a unique image, initializes storage, waits for MySQL and
Redis, checks Django and migration drift, stops web and any notification worker,
then applies migrations once and waits for a healthy web container. Back up and
verify the database before deploying; schema migrations can be irreversible. A
failed release after downtime leaves web stopped for inspection. The release lock
prevents concurrent releases for the same stack on this host. The exact image tag
is printed for management and rollback. The old database and media mounts remain
at `VPS_STORAGE_ROOT/PROJECT_NAME/DEPLOY_ENV/{mysql,media,data}` unless explicit
`APP_DATA_ROOT`, `MEDIA_DATA_DIR`, or `MYSQL_DATA_DIR` overrides are configured.
Changing these paths does not migrate existing data.

The optional notification worker runs once per invocation. Configure its `SMS_*`
URLs and token before scheduling it, and ensure invocations do not overlap.
Uploaded media is served by Django at `MEDIA_URL` for authenticated active session
users, including with `DEBUG=False`; only raster images render inline. Other files
download, and responses are private and not cached. WhiteNoise serves collected
static files. Gunicorn streams media, so monitor worker usage under heavy traffic. Compose interpolates unquoted and double-quoted values in
environment files; single-quote secrets containing literal `$` characters.

`PYTHON_IMAGE`, `UV_IMAGE`, `IMAGE_NAME`, `WEB_WORKERS`, `WEB_TIMEOUT`,
`WEB_MAX_REQUESTS`, `WEB_MAX_REQUESTS_JITTER`, `WEB_CPUS`, `WEB_MEMORY_LIMIT`,
`MYSQL_CPUS`, `MYSQL_MEMORY_LIMIT`, `MYSQL_BUFFER_POOL_SIZE`,
`MYSQL_MAX_CONNECTIONS`, and `MYSQL_BINLOG_EXPIRE_SECONDS` control the build and
resource limits. `PORT` changes the published host port; Gunicorn listens on 8004
inside the container. `./start.sh --help` lists the local launcher options.

- Set MEDIA_DATA_DIR to the host directory containing photo/img to use an alternate Docker upload archive. For local Django, set MEDIA_ROOT to that directory.
