# Engineering Rules & Development Guidelines (`RULES.md`)

This document defines the strict engineering standards, architectural invariants, security protocols, and coding rules that apply to all developers and AI agents working on the **Baani Electricals (BSSAC)** codebase.

---

## 🚨 Non-Negotiable Invariants

### 1. Zero Hard Deletions on Financial & Auditing Records
- **Rule**: Never call `.delete()` on instances of `Collection`, `Sales`, `CashCounter`, `CollectionCashCounter`, `Party`, `StaffUser`, `Bank`, or `Attendance`.
- **Enforcement**: Set `instance.isDeleted = True` and call `instance.save()`. All retrieval querysets must include `.filter(isDeleted__exact=False)`.

### 2. Mandatory Authorization Checks on All Views
- **Rule**: Every view function or class in `home/views.py` and `home/apiView.py` must enforce access control.
- **Enforcement**:
  - Decorate views with `@check_group(...)` specifying permitted roles (e.g. `'Admin'`, `'Moderator'`, `'Collection'`, `'SalesAdmin'`, `'CashCounter'`, `'Customer'`).
  - Gated views must also be checked with `@is_activated()` to honor software license validity.
  - Never introduce unauthenticated public endpoints unless explicitly intended (such as login or PWA service worker endpoints).

### 3. Absolute Secret Protection & Environment Hygiene
- **Rule**: Never commit `.env` files, database passwords, JWT secrets, WhatsApp API tokens, or production credentials to git.
- **Enforcement**:
  - `.gitignore` must strictly ignore `.env`, `*.sqlite3`, `media/`, and IDE folders.
  - When introducing a new configurable property, add it to `.env.example` with a sanitized dummy value and configure a fallback in `baani/settings.py` using `env(...)`.

### 4. Database Engine Neutrality
- **Rule**: Application code must run seamlessly on both SQLite3 (local testing) and MySQL 8.x (production).
- **Enforcement**:
  - Do not use database-specific raw SQL queries or engine-exclusive column extensions.
  - Foreign key relations must use `on_delete=models.SET_NULL, null=True, blank=True` to prevent cascade failure when entities are modified.

---

## 🐍 Python & Django Coding Conventions

### 1. Code Formatting & Linting
- **Standard**: Follow PEP 8 guidelines.
- **Tooling**: We use [Ruff](https://github.com/astral-sh/ruff) as the primary linter and formatter.
- **Rules**:
  - Line length: 120 characters maximum.
  - Target runtime: Python 3.14+ syntax.
  - Run `ruff check .` and `ruff format .` before pushing code.

### 2. Migration Discipline
- **Rule**: Every model change requires an explicit, clean migration.
- **Guidelines**:
  - Name migrations descriptively if authored manually.
  - Never edit or delete an existing migration file that has already been applied in production or staging environments.
  - Always run `python manage.py makemigrations --check` in CI to ensure no schema drift exists.

### 3. Timezone Consistency
- **Rule**: Maintain `USE_TZ = False` in `baani/settings.py`.
- **Reason**: The codebase relies on naive datetimes representing Indian Standard Time (`Asia/Kolkata`). Do not introduce `django.utils.timezone.now()` where timezone-aware objects conflict with existing database records; use standard `datetime.now()` or consistent date objects matching existing patterns.

### 4. Asynchronous & Heavy Operations
- **Rule**: Never run synchronous outbound network requests (e.g. WhatsApp API, external webhook calls) inside standard Django view requests.
- **Pattern**: Write messages to the `WhatsappMessageStatus` table and let `sms_worker.py` dispatch them asynchronously.

---

## 🌿 Git & Collaboration Rules

### 1. Branch Strategy
- `master`: Production-ready, deployable code only. Protected branch.
- `feature/<name>`: New capabilities or functional improvements.
- `bugfix/<name>`: Targeted bug fixes.
- `refactor/<name>`: Code restructuring or modernization without behavioral changes.

### 2. Commit Message Standards
Use clear, imperative commit messages:
```text
feat(sales): add fiscal year 26-27 invoice numbering
fix(auth): correct redirect path on unauthorized group check
docs(arch): add architecture diagram and ERD
refactor(settings): decouple redis url into environment config
```

### 3. Review Checklist Before Merging
- [ ] Code passes `ruff check .` with zero errors.
- [ ] Database migrations created and tested forwards and backwards.
- [ ] Soft-delete logic maintained on all affected queries.
- [ ] No secret or credentials exposed in diff.
- [ ] Updated `MEMORY.md` and `TASKS.md` reflecting new capabilities.
