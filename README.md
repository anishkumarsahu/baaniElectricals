# Baani Electricals (BSSAC) — ERP & Field Operations Management

[![Python Version](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/django-6.1.0-green.svg)](https://www.djangoproject.com/)
[![Package Manager](https://img.shields.io/badge/managed%20by-uv-purple.svg)](https://github.com/astral-sh/uv)
[![PWA Ready](https://img.shields.io/badge/PWA-enabled-orange.svg)](https://web.dev/progressive-web-apps/)

An enterprise resource planning (ERP), field collection tracking, sales counter, and customer ledger management platform developed for **Baani Electricals** (operating under the **BSSAC** brand).

---

## 📑 Documentation Index

This repository maintains an active documentation suite to keep track of system architecture, design decisions, memory, operational rules, commands, and tasks:

| Document | Purpose |
| :--- | :--- |
| [ARCHITECTURE.md](file:///Users/anishkumarsahu/ZivaInfotech/BaaniElectricals/baaniElectricals/ARCHITECTURE.md) | High-level system design, data flows, components, and Mermaid topology |
| [MEMORY.md](file:///Users/anishkumarsahu/ZivaInfotech/BaaniElectricals/baaniElectricals/MEMORY.md) | Long-term project memory, technical evolution, design decisions, and quirks |
| [TASKS.md](file:///Users/anishkumarsahu/ZivaInfotech/BaaniElectricals/baaniElectricals/TASKS.md) | Active sprint status, completed roadmap, backlog, and technical debt |
| [DESIGN.md](file:///Users/anishkumarsahu/ZivaInfotech/BaaniElectricals/baaniElectricals/DESIGN.md) | UI/UX patterns, role-based workflows, PWA design, and API conventions |
| [RULES.md](file:///Users/anishkumarsahu/ZivaInfotech/BaaniElectricals/baaniElectricals/RULES.md) | Code quality standards, soft-deletion rules, security, and contribution guidelines |
| [COMMANDS.md](file:///Users/anishkumarsahu/ZivaInfotech/BaaniElectricals/baaniElectricals/COMMANDS.md) | Command cheat sheet for `uv`, Django, migrations, background workers, and deployment |
| [AGENTS.md](file:///Users/anishkumarsahu/ZivaInfotech/BaaniElectricals/baaniElectricals/AGENTS.md) | Operational guidelines and protocol for AI coding assistants working in this repository |

---

## ⚡ Key Capabilities

- **Field Collection & Geolocation Tracking**: Mobile-friendly PWA interface for field staff to record collections, capture live GPS coordinates, and log check-in/check-out locations.
- **Cash Counter & Invoicing**: Counter management for cash, card, and mixed payments with daily reconciliation, receipt generation, and PDF invoice generation via WeasyPrint.
- **Sales & Approvals Workflow**: Multi-tier approval system for sales entries, collections, and cheque clearance across Admin, Moderator, and SalesAdmin roles.
- **Customer Self-Service Portal**: Customers can log in with their assigned credentials to inspect transaction history, payment statuses, and profile information.
- **Progressive Web App (PWA)**: Offline-first service worker, installable on mobile devices (Android/iOS) with desktop-class performance.
- **SMS & WhatsApp Messaging Automation**: Out-of-process worker (`sms_worker.py`) dispatching automated notifications, payment receipts, and balance alerts via WhatsApp gateway.
- **License & Validity Management**: Built-in activation gating (`activation` app) regulating installation expiry and module access.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | Python 3.14+, Django 6.1.0 |
| **Package Management** | `uv` (Astral), `pyproject.toml`, `requirements.txt` |
| **Database** | SQLite3 (Local development) / MySQL 8.x (Production via `mysqlclient`) |
| **Caching & Sessions** | Redis (`django-redis` backend) |
| **Static & Media** | WhiteNoise 6.11, Django-StdImage (thumbnailing), Pillow |
| **Document Generation** | WeasyPrint 70.0 (HTML-to-PDF conversion) |
| **Frontend & UI** | Django Templates, Bootstrap, jQuery DataTables, HTML5 Geolocation, PWA Service Worker |
| **Background Services**| Standalone Python WhatsApp/SMS poller (`sms_worker.py`) |
| **Production Server** | Gunicorn 23.0.0, Reverse Proxy (Nginx/Traefik) |

---

## 📁 Repository Structure

```text
baaniElectricals/
├── activation/                # Software licensing & expiry verification app
│   ├── models.py              # Validity & EcomValidity models
│   ├── views.py               # is_activated decorator & validation checks
│   └── urls.py
├── baani/                     # Project configuration & settings
│   ├── settings.py            # 12-factor environment-driven Django settings
│   ├── urls.py                # Root routing, PWA endpoints, Admin URLs
│   ├── wsgi.py / asgi.py
├── home/                      # Core business logic app
│   ├── models.py              # StaffUser, Party, Collection, Sales, CashCounter, Attendance
│   ├── views.py               # Template view controllers & authorization wrappers
│   ├── apiView.py             # Server-side DataTables & JSON endpoints
│   ├── templates/             # HTML templates (Admin, Collection, Counter, Customer)
│   ├── templatetags/          # Custom Django filters and template utilities
│   └── urls.py
├── static/                    # CSS, JS libraries, vendor plugins, PWA service worker
├── staticfiles/               # Collected static files (WhiteNoise target)
├── media/                     # Uploaded user photos and verification documents
├── sms_worker.py              # Background worker for WhatsApp/SMS notification polling
├── pyproject.toml             # uv package declaration and dependencies
├── requirements.txt           # Pip-compatible dependency export
├── uv.lock                    # Locked dependency graph
├── manage.py                  # Django CLI runner
├── .env.example               # Template environment configuration
└── db.sqlite3                 # Local SQLite database (development)
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.14+ (or compatible Python 3.12/3.13)
- `uv` installed ([docs.astral.sh/uv](https://docs.astral.sh/uv/)) or standard `pip`
- SQLite (default) or MySQL 8.0+
- Optional: Redis running on `localhost:6379`

### 2. Environment Setup

Clone repository and initialize virtual environment using `uv`:

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate
uv sync

# Or using standard pip
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example configuration:

```bash
cp .env.example .env
```

Review `.env` to customize secrets, ports, or switch between SQLite and MySQL:

```ini
DEBUG=True
PORT=8004
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://127.0.0.1:6379/1
```

### 4. Database Setup & Migrations

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Launch the Development Server

```bash
python manage.py runserver 0.0.0.0:8004
```

Visit the application at:
- Web App: [http://localhost:8004/home/](http://localhost:8004/home/)
- Admin Panel: [http://localhost:8004/admin/](http://localhost:8004/admin/)

### 6. Run the SMS / WhatsApp Worker (Optional)

In a separate terminal session:

```bash
python sms_worker.py
```

---

## 🛡️ User Roles & Access Control

Access control is governed by Django User Groups via custom view decorators (`@check_group`, `@check_two_group`):

- **Admin / Moderator**: Full access to dashboard, user management, approval lists, bank configs, and system settings.
- **SalesAdmin**: Elevated access to sales invoicing, approvals, and transaction auditing.
- **Collection / NormalStaff**: Field agents who log customer collections, record payment modes, capture GPS data, and check attendance.
- **CashCounter**: Counter operators managing on-premise billing, cash/card splits, and counter expense vouchers.
- **Customer**: External clients reviewing ledger balances, invoices, and payment receipts.

---

## 🤝 Contributing

1. Always read [RULES.md](file:///Users/anishkumarsahu/ZivaInfotech/BaaniElectricals/baaniElectricals/RULES.md) before writing code.
2. Follow the branch naming convention: `feature/<name>`, `bugfix/<name>`, or `refactor/<name>`.
3. Format and lint changes using `ruff`:
   ```bash
   uv run ruff check .
   uv run ruff format .
   ```
4. Consult [COMMANDS.md](file:///Users/anishkumarsahu/ZivaInfotech/BaaniElectricals/baaniElectricals/COMMANDS.md) for testing and migration instructions.
5. Keep [MEMORY.md](file:///Users/anishkumarsahu/ZivaInfotech/BaaniElectricals/baaniElectricals/MEMORY.md) and [TASKS.md](file:///Users/anishkumarsahu/ZivaInfotech/BaaniElectricals/baaniElectricals/TASKS.md) updated upon major milestones.
