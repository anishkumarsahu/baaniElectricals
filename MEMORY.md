# Project Memory & Knowledge Base (`MEMORY.md`)

This document serves as persistent operational memory for the **Baani Electricals (BSSAC)** codebase. It captures architectural decisions, technical history, design trade-offs, critical quirks, and contextual rationale.

---

## 🏛️ Project Background & Overview

- **Organization**: Baani Electricals / BSSAC (Baani Switchgears & Automation Controls)
- **Primary Domain**: Electrical equipment wholesale, distribution, counter sales, and customer credit/collection tracking.
- **Core Problem Solved**: Field sales & collection executives collecting cash/cheques in the field needed a real-time, mobile-accessible ledger with GPS coordinates, manager approvals, counter point-of-sale logging, and automated WhatsApp payment receipts.
- **Development Team**: Ziva Infotech.

---

## 📅 Architectural Evolution & Milestones

### 1. Legacy Foundation (Django 4.1)
- Initial release built on standard Django 4.1 with monolithic settings, hardcoded credentials, and tight coupling to local server environments.
- Relied on direct SQLite storage for dev and MySQL for production.

### 2. Modernization & Django 6.1 Upgrade (Current `feature/docker-upgrade`)
- **Python Upgrade**: Upgraded to Python 3.14 target baseline (`requires-python = ">=3.14"`).
- **Django Upgrade**: Upgraded core framework to `django>=6.1.0,<6.2.0`.
- **Package Management**: Adopted modern `uv` workflow with `pyproject.toml` and `uv.lock`, keeping `requirements.txt` synced for backward compatibility.
- **12-Factor App Environment Configuration**:
  - Replaced hardcoded variables with `django-environ`.
  - Added `.env.example` defining all operational parameters (`DATABASE_URL`, `REDIS_URL`, `PORT`, `CSRF_TRUSTED_ORIGINS`, PWA metadata).
  - Centralized SMS/WhatsApp worker environment variables (`SMS_FETCH_URL`, `SMS_SEND_URL`, `SMS_AUTH_TOKEN`, `SMS_DELAY_SECONDS`).
- **PWA Route Normalization**:
  - Direct routing for `/serviceworker.js` and `/manifest.json` mapped to `pwa_views` to eliminate routing conflicts with Django 6.x URL patterns.
- **Permissions Hardening**:
  - Added granular permissions for `SalesAdmin` to edit sales records.
  - Introduced `createdBy` auditing field on the `Party` model to track customer account authorship.
  - Added 26-27 financial year fiscal numbering support on sales and counter invoices.

---

## 💡 Key Architectural Decisions & Patterns

### 1. Soft Deletion Paradigm (`isDeleted = models.BooleanField(default=False)`)
- **Decision**: Almost all primary business models (`StaffGroup`, `PartyGroup`, `StaffUser`, `Bank`, `Party`, `Collection`, `Sales`, `CashCounter`, `Attendance`, `WhatsappMessageStatus`) inherit or implement an `isDeleted` flag.
- **Rationale**: Financial and audit trails must never be permanently deleted from the database. Soft-deleted records are filtered out in standard queries (`filter(isDeleted__exact=False)`).
- **Rule**: Never run `.delete()` on these models in application code without strict operational justification.

### 2. Timezone Handling (`USE_TZ = False`)
- **Configuration**: `TIME_ZONE = 'Asia/Kolkata'`, `USE_TZ = False`.
- **Rationale**: The project stores naive datetimes matching Indian Standard Time (IST) directly in the database. Changing `USE_TZ` to `True` would break legacy date comparisons and timestamp filters across reports and DataTables.

### 3. MySQL Foreign Key Checks Disabling
- **Configuration in `baani/settings.py`**:
  ```python
  if 'mysql' in DATABASES['default']['ENGINE']:
      DATABASES['default']['OPTIONS'].setdefault("init_command", "SET foreign_key_checks = 0;")
      DATABASES['default']['OPTIONS'].setdefault('charset', 'utf8mb4')
  ```
- **Rationale**: Historically allowed bulk data imports, legacy table migrations, and uncascaded deletions without triggering foreign key constraint violations in MySQL. Maintain this setting when configuring production MySQL databases.

### 4. Image Resizing with `StdImageField`
- **Configuration**: Uses `django-stdimage` on `StaffUser.photo` and `StaffUser.idProof`.
- **Variations Generated**:
  - `thumbnail`: `(50, 50, True)` (crop for avatar display)
  - `medium`: `(300, 200)` (card preview)
  - `large`: `(600, 400)` (modal full view)
- `delete_orphans=True` ensures discarded media files are removed from disk on model updates.

### 5. Decoupled WhatsApp / SMS Worker (`sms_worker.py`)
- **Design**: Instead of running synchronously within Django HTTP request cycles (which would block web workers and increase user response times), SMS/WhatsApp messages are staged in the `WhatsappMessageStatus` table (`home/apiView.py`).
- **Worker Execution**: `sms_worker.py` runs as an external cron/daemon that:
  1. Polls `/api/get_all_unsent_messages/`
  2. Sends payloads to the WhatsApp gateway (`http://localhost:8082/...`)
  3. Posts completion status back to `/api/update_sent_msg_status/`
- **Resilience**: Configured with exponential delays and environment-driven URLs to prevent gateway rate-limiting.

### 6. Role-Based Access via Django User Groups
- Group memberships are cached on the `request` object (`_request_group_names(request)`) to avoid redundant database queries per view execution.
- Decorators in `home/views.py`:
  - `@check_group(*group_names)`: Checks if current user belongs to at least one of the specified groups.
  - `@check_two_group(group1, group2)`: Historical shortcut decorator for binary group validation.

### 7. Software Licensing App (`activation/`)
- The `Validity` model tracks license validity (`activationDate`, `expiryDate`, `activationType`).
- The `@is_activated()` decorator inspects the validity table before serving protected views. If expired, views redirect or display licensing warnings.

### 8. Integration & E2E Test Suite Architecture
- **In-Memory SQLite Test Database Auto-Fallback**:
  - `baani/settings.py` automatically detects when `'test' in sys.argv`. If `TEST_DATABASE_URL` is unset and the default database points to Docker container host `mysql`, it seamlessly switches to `sqlite:///:memory:`.
  - Configures `MD5PasswordHasher` exclusively during test execution, speeding up authentication tests by ~110x.
- **Hermetic Media Isolation**:
  - `BaseTestCase` establishes a unique temporary media root (`tempfile.mkdtemp()`) overriding `MEDIA_ROOT` per test run and destroys it on teardown, preventing uploaded test avatars or ID proofs from leaking into the repository.
- **Deterministic External Mocking**:
  - `BaseTestCase` auto-patches `home.apiView.send_message` and `home.apiView.get_location` so tests never spawn rogue daemon threads or call external WhatsApp/HERE geocoding gateways.
- **Coverage & Modules**:
  - 59 comprehensive integration and end-to-end tests across 8 key domain areas:
    1. `activation/tests.py`: Licensing boundaries, valid/expired/absent states, e-commerce validation.
    2. `home/tests/test_auth_e2e.py`: Authentication, group resolution, homepage redirects, logout, staff and 6-digit customer password changes.
    3. `home/tests/test_master_data_e2e.py`: StaffUser, PartyGroup, Bank, and Party CRUD with `createdBy` auditing and soft deletion.
    4. `home/tests/test_collections_e2e.py`: Cash/Cheque/Party collections with GPS coordinates, manager approval, receipt dispatch, soft delete.
    5. `home/tests/test_sales_e2e.py`: FY 26-27 invoice numbering, SalesAdmin update permissions, WhatsApp dispatch triggers.
    6. `home/tests/test_cash_counter_e2e.py`: POS modes (Cash, Card, Mix, Credit, Return, Advance, Expense), counter collection, and reports.
    7. `home/tests/test_attendance_e2e.py`: Daily check-in/out, GPS stamping, location deduction, DataTables.
    8. `home/tests/test_sms_worker_e2e.py`: Staging queue, 10-digit filtering, callback updating, daemon execution.
    9. `home/tests/test_reports_and_system_e2e.py`: Collection/Sales/POS reports, admin/staff dashboards, `/healthz`, and PWA service worker endpoints.

---

## ⚠️ Important Caveats & Known Technical Debt

1. **Massive `home/apiView.py` File**:
   - The file is ~146 KB and handles over 40 DataTables JSON views, reporting endpoints, and AJAX mutations.
   - *Future Plan*: Refactor into a modular package (`home/api/collections.py`, `home/api/sales.py`, `home/api/users.py`, etc.).
2. **Double User Schema (`StaffUser` vs Django `User`)**:
   - `User` handles authentication credentials and groups.
   - `StaffUser` stores business attributes (phone, photo, idProof, address, partyGroup).
   - *Caution*: When creating or modifying staff credentials, both `User` and `StaffUser` records must be kept in sync.
3. **Database Dual Support**:
   - Code must remain compatible with both SQLite3 (local testing) and MySQL (production). Avoid engine-specific SQL constructs in raw queries.
4. **Hardcoded URLs in Legacy Templates**:
   - Some templates or scripts reference `https://bssac.in/`. When developing locally or on staging, ensure `.env` overrides these endpoints.

### Docker deployment
- The image builds locked dependencies and collects static assets at build time; the non-root web, migration, and opt-in one-shot notification jobs share persistent data and media volumes. Redis is private to Compose and MySQL is an optional profile. The release launcher applies migrations as a separate job; web startup does not apply them. SQLite deployments must use `/data/db.sqlite3`; a repository database is excluded from the build context. Django serves authenticated uploads; worker endpoints must be configured deliberately.
- `start.sh` offers local uv/Gunicorn and Compose actions. It uses the selected Docker environment file for both interpolation and container settings; migrations remain explicit and Docker shutdown preserves volumes.

- Docker uses Hansika-style host bind mounts under `VPS_STORAGE_ROOT/PROJECT_NAME/DEPLOY_ENV`, with `APP_DATA_ROOT`, `MEDIA_DATA_DIR`, and `MYSQL_DATA_DIR` overrides. A root-only initialization job prepares app directories; old named volumes are not migrated automatically.

- Compose interpolates dollar signs in unquoted environment values; single-quote literal secrets in deployment files. The launcher reports an unavailable Docker daemon before starting services.

- On macOS `start.sh` defaults `VPS_STORAGE_ROOT` to `$HOME/docker-apps` when unset, avoiding Docker Desktop’s unshared `/srv` path; explicit environment values win. Direct Compose commands still require a shared storage path.
- The local private `.env` was configured for the Compose MySQL service; its previous contents were backed up locally before replacement. Docker MySQL storage starts separately from the existing SQLite database.
- The Docker image follows Hansika's dependency, asset, and non-root runtime stages. Collected static assets are kept once in the runtime image; Baani's service worker remains at its required source path. The runtime uses the MariaDB client library needed by mysqlclient without compiler headers.

- Docker releases now follow Hansika’s unique-image, host-lock, preflight, stop-writers, migrate-once, and health-gated restart pattern. Deleted migration history is rejected outright for Baani. Existing Baani storage and DATABASE_URL conventions are retained.

- Uploaded media is served directly by Django in production and development to authenticated active session users, with path containment and private response headers. Baani does not provide Hansika’s JWT authentication. Existing media paths and bind mounts are unchanged.

- Local uploads default to the sibling media_cdn directory. Compose mounts the existing host media directory at /media_cdn.
