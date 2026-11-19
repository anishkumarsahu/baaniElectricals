# Task & Roadmap Tracker (`TASKS.md`)

This document tracks all active, in-progress, completed, and backlog tasks for the **Baani Electricals (BSSAC)** repository.

---

## 🎯 Current Milestone: Modernization & Containerization (`feature/docker-upgrade`)

- **Active Branch**: `feature/docker-upgrade`
- **Objective**: Modernize runtime to Python 3.14 + Django 6.1, decouple environmental configuration, normalize PWA routes, and establish reproducible containerized deployments.

---

## 📋 Task Board

### ✅ Completed Tasks

- [x] **Authenticated media delivery**: Serve existing and new uploads in production with session authentication and path protections.

- [x] **Hansika-style Docker release**: Added image-pinned guarded deployments, health checks, resource limits, and migration preflight.

- [x] **Docker web image build**: Aligned dependency, asset, and runtime stages with the Hansika pattern while preserving Baani’s PWA worker.

- [x] **Local Docker environment**: Configured private MySQL settings and preserved the prior environment file.

- [x] **macOS Docker mounts**: Default the launcher storage root to a Docker Desktop shared home directory when no root is configured.

- [x] **Docker startup diagnostics**: Documented literal secret quoting and added a daemon availability check.

- [x] **Docker storage configuration**: Added Hansika-style environment-specific bind mounts and storage initialization.

- [x] **Server launcher**: Added `start.sh` for local and Docker operations with explicit migrations.

- [x] **Django 6.1 & Python 3.14 Upgrade**: Updated dependencies in `pyproject.toml` and pinned Django to `>=6.1.0,<6.2.0`.
- [x] **Package Manager Modernization (`uv`)**: Initialized `uv` project structure, generated `uv.lock`, and exported synced `requirements.txt`.
- [x] **12-Factor App Environment Configuration**:
  - Implemented `django-environ` in `baani/settings.py`.
  - Created `.env.example` defining database URLs, ports, Redis connection strings, and security toggles.
- [x] **Decoupled SMS Worker Configuration**:
  - Refactored `sms_worker.py` to source `SMS_FETCH_URL`, `SMS_SEND_URL`, `SMS_AUTH_TOKEN`, and `SMS_DELAY_SECONDS` from environment variables.
- [x] **Fiscal Year 26–27 Support**: Added 2026–2027 fiscal year invoice numbering logic for sales and counter invoices.
- [x] **Sales Admin Permissions**: Configured granular edit permissions for the `SalesAdmin` group and added `createdBy` tracking on the `Party` model.
- [x] **PWA Route Normalization**:
  - Explicitly mapped `/serviceworker.js` and `/manifest.json` in `baani/urls.py` to prevent route collision with wildcard handlers.
- [x] **Automated Integration & E2E Test Suite**:
  - Authored comprehensive test suite covering 59 integration/E2E test scenarios across 7 modules:
    - `activation/tests.py`: License validity and `@is_activated()` / `@is_ecom_activated()` decorators.
    - `home/tests/test_auth_e2e.py`: RBAC permissions, role session routing, password change.
    - `home/tests/test_master_data_e2e.py`: Staff, Party, Bank, and PartyGroup CRUD with `createdBy` auditing.
    - `home/tests/test_collections_e2e.py`: Field collection (cash/cheque), admin approvals, GPS coordinates, cheque reminders.
    - `home/tests/test_sales_e2e.py`: Sales invoicing with FY 26-27 series, SalesAdmin update permissions, WhatsApp dispatch triggers.
    - `home/tests/test_cash_counter_e2e.py`: POS multi-mode (Cash, Card, Mix, Credit, Expense), counter collection, and reports.
    - `home/tests/test_attendance_e2e.py`: Staff attendance check-in/out with location and DataTables.
    - `home/tests/test_sms_worker_e2e.py`: WhatsApp daemon queuing, filtering, and callback updating.
    - `home/tests/test_reports_and_system_e2e.py`: Financial aggregation reports, admin/staff dashboards, `/healthz`, and PWA service worker endpoints.
- [x] **Repository Documentation Suite**:
  - Authored `README.md`, `MEMORY.md`, `ARCHITECTURE.md`, `TASKS.md`, `DESIGN.md`, `RULES.md`, `COMMANDS.md`, and `AGENTS.md`.

---

### ⏳ In Progress

- [x] **Dockerization & Multi-Stage Dockerfile**: Added a locked Python/uv image and Compose services for web, migrations, Redis, optional MySQL, and the opt-in one-shot notification worker.
- [ ] **Static Assets Pipeline Validation**:
  - Validate WhiteNoise serving with `DEBUG=False` under Docker container conditions.
  - Verify PWA offline assets caching.
- [ ] **Ruff Linter & Formatter Baseline**:
  - Run `ruff check --fix` and `ruff format` across the codebase to ensure consistent styling.

---

### 📌 Backlog & Future Enhancements

#### High Priority
- [ ] **Deconstruct `home/apiView.py`**:
  - Break down the ~147 KB file into organized domain modules:
    - `home/api/collections.py`
    - `home/api/sales.py`
    - `home/api/cash_counter.py`
    - `home/api/users.py`
    - `home/api/reports.py`
- [ ] **Healthcheck Endpoint (`/healthz` or `/api/health/`)**:
  - Add lightweight probe validating database connection and Redis availability for container orchestrators.

#### Medium Priority
- [ ] **Celery / Redis Task Queue Integration**:
  - Migrate polling logic from standalone `sms_worker.py` to Celery or Django-Q background tasks.
- [ ] **REST API Token Authentication**:
  - Add Token/JWT-based authentication for external API consumers instead of relying on legacy session cookies.
- [ ] **Audit Trail Expansion**:
  - Implement full change history logging (e.g., `django-simple-history`) for `Collection` and `Sales` models.

#### Low Priority
- [ ] **Dark Mode / UI Refresh**:
  - Update legacy Bootstrap theme to modern accessible UI components.
- [ ] **Automated Database Backups**:
  - Script scheduled MySQL/SQLite dumps with rotation and cloud backup upload.

---

## 📝 Task Tracking Rules for Agents & Developers

1. **Keep in Sync**: Whenever you finish a task, check the box `[x]` and add relevant context in `MEMORY.md`.
2. **Prioritization**: Never jump into low-priority tasks when high-priority tasks (e.g. security, container stability, tests) remain pending.
3. **Branch Hygiene**: Never commit unverified tasks directly to `master`. Work on feature branches.

- [x] Align local and container media roots with Hansika.
