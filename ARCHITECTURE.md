# System Architecture (`ARCHITECTURE.md`)

This document details the architectural topology, data pipelines, application breakdown, and database relationships of the **Baani Electricals (BSSAC)** management platform.

---

## 🏛️ High-Level System Architecture

The following diagram illustrates how clients, web servers, database engines, cache stores, and asynchronous workers interconnect:

```mermaid
flowchart TD
    subgraph Clients["Clients & Presentation"]
        MobilePWA["📱 Mobile PWA (Field Staff / Collection)"]
        DesktopAdmin["💻 Desktop Web (Admin / Cash Counter)"]
        CustomerPortal["🌐 Customer Self-Service Portal"]
    end

    subgraph Ingress["Web Gateway & Security"]
        ReverseProxy["Nginx / Reverse Proxy (SSL / HTTPS)"]
        WhiteNoise["WhiteNoise Static Engine"]
    end

    subgraph AppServer["Application Layer (Django 6.1 / Gunicorn)"]
        CoreSettings["baani.settings (12-Factor Env)"]
        ErrorPages["Django error handlers and shared HTML templates"]
        PWAModule["PWA Controller (serviceworker.js / manifest.json)"]
        HomeApp["home App (Core Business Logic)"]
        ActivationApp["activation App (License / Expiry)"]
        DataTablesAPI["apiView.py (Server-side DataTables JSON)"]
        PDFEngine["WeasyPrint PDF Invoicing Engine"]
    end

    subgraph DataPersistence["Data & Cache Layer"]
        DB[(Database: SQLite Dev / MySQL 8.x Prod)]
        RedisCache[(Redis Cache Store)]
        MediaStorage[("Media Storage (Photos / ID Proofs)")]
    end

    subgraph AsyncWorker["Background Notification Worker"]
        SMSWorker["sms_worker.py (Daemon / Cron)"]
        WhatsAppAPI["External WhatsApp Gateway API"]
    end

    MobilePWA -->|HTTPS / REST| ReverseProxy
    DesktopAdmin -->|HTTPS / REST| ReverseProxy
    CustomerPortal -->|HTTPS / REST| ReverseProxy

    ReverseProxy --> WhiteNoise
    ReverseProxy --> AppServer

    AppServer -->|Handled request errors and CSRF rejection| ErrorPages
    HomeApp --> DB
    ActivationApp --> DB
    HomeApp --> RedisCache
    HomeApp --> MediaStorage
    HomeApp --> PDFEngine

    SMSWorker -->|Poll /api/get_all_unsent_messages/| HomeApp
    SMSWorker -->|Send Payload| WhatsAppAPI
    SMSWorker -->|POST /api/update_sent_msg_status/| HomeApp
```

---

## 🔄 Core Data & Business Flows

### 1. Field Collection Workflow (GPS-Tagged)

```mermaid
sequenceDiagram
    autonumber
    actor Staff as Field Staff (Mobile PWA)
    participant Django as Django App (home)
    participant DB as Database
    actor Admin as Admin / SalesAdmin
    participant Worker as sms_worker.py
    participant WA as WhatsApp Gateway
    actor Customer as Party / Customer

    Staff->>Django: Submit Collection Form (Party, Amount, Mode, GPS Lat/Lng)
    Django->>DB: Create Collection (isApproved=False, isTallied=False)
    Note over Django,DB: Record stored with soft-delete flag isDeleted=False

    Admin->>Django: Review Collection in /collection_list/
    Admin->>Django: Approve Collection (/api/approve_collection/)
    Django->>DB: Update Collection (isApproved=True, approvedBy=Admin, approvedOn=Now)
    Django->>DB: Create WhatsappMessageStatus record (Pending)

    Worker->>Django: Poll /api/get_all_unsent_messages/
    Django-->>Worker: Return Pending Message Payload
    Worker->>WA: POST message to customer phone (+91...)
    WA-->>Worker: HTTP 200 Success
    Worker->>Django: POST /api/update_sent_msg_status/ (id, status=Sent)
    Django->>DB: Update message status to "Sent"
    WA-->>Customer: Deliver WhatsApp receipt with collection details
```

### 2. Daily Cash Counter Operations

```mermaid
sequenceDiagram
    autonumber
    actor Counter as Cash Counter Operator
    participant Django as Django App
    participant DB as Database
    participant Weasy as WeasyPrint PDF

    Counter->>Django: Open Cash Counter Entry (/take_collection/)
    Counter->>Django: Log Payment (Cash, Card, Mixed, or Expense Voucher)
    Django->>DB: Insert CashCounter & CollectionCashCounter records
    Django->>Weasy: Render HTML invoice template to PDF
    Django-->>Counter: Stream PDF Invoice / Receipt for customer
```

---

## 📦 Application Component Breakdown

### 1. `baani` (Project Core)
- **Role**: Coordinates configuration, routing, and deployment settings.
- **Key Modules**:
  - `baani/settings.py`: 12-factor configuration parsed via `django-environ`.
  - `baani/urls.py`: Global URL dispatcher; serves PWA files directly at `/serviceworker.js` and `/manifest.json`.
  - `baani/wsgi.py` & `baani/asgi.py`: Entry points for WSGI and ASGI application servers.
  - `templates/errors/page.html` provides the shared browser layout for Django’s 400, 403, 404, and 500 templates and the CSRF rejection template. Django selects the production 400, 404, and 500 pages with `DEBUG=False`.

### 2. `home` (Business Domain Logic)
- **Role**: Houses the domain models, templates, controllers, and APIs.
- **Key Sub-modules**:
  - `home/models.py`: Primary domain schema (Users, Parties, Collections, Sales, Attendance, Cash Counter).
  - `home/views.py`: Route handlers for admin dashboard, staff collection forms, counter operations, and authentication.
  - `home/apiView.py`: High-density REST-like and DataTables server-side endpoints for asynchronous UI interactions.
  - `home/templatetags/`: Custom filters for currency formatting, date transformations, and role assertions.

### 3. `activation` (Licensing & Validity)
- **Role**: Software licensing guard and subscription expiry enforcement.
- **Key Sub-modules**:
  - `activation/models.py`: `Validity` and `EcomValidity` models storing activation and expiration dates.
  - `activation/views.py`: `is_activated` decorator that wraps protected views and enforces license checks.

### 4. `sms_worker.py` (Background Notification Daemon)
- **Role**: Decoupled message dispatcher running outside the HTTP request/response cycle.
- **Workflow**:
  - Polls unsent notifications via `SMS_FETCH_URL`.
  - Dispatches messages to `SMS_SEND_URL` with bearer token authentication.
  - Acknowledges delivery via `SMS_UPDATE_STATUS_URL`.

---

## 🗄️ Database Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    User ||--o| StaffUser : "authenticates"
    User ||--o| Party : "customer_account"
    StaffGroup ||--o{ StaffUser : "categorizes"
    PartyGroup ||--o{ Party : "groups"
    StaffUser ||--o{ Party : "assigned_to"
    StaffUser ||--o{ Party : "created_by"

    Party ||--o{ Collection : "pays"
    Bank ||--o{ Collection : "deposited_in"
    StaffUser ||--o{ Collection : "collected_by"
    StaffUser ||--o{ Collection : "approved_by"

    Party ||--o{ Sales : "purchases"
    StaffUser ||--o{ Sales : "created_by"
    StaffUser ||--o{ Sales : "approved_by"

    Party ||--o{ CashCounter : "counter_transaction"
    Bank ||--o{ CashCounter : "bank_link"
    StaffUser ||--o{ CashCounter : "created_by"

    StaffUser ||--o{ Attendance : "logs_attendance"

    StaffUser {
        int id PK
        string name
        string phone
        string email
        string username
        string group
        boolean isDeleted
        datetime datetime
    }

    Party {
        int id PK
        string name
        string phone
        string username
        string address
        int partyGroupID FK
        int assignTo FK
        int createdBy FK
        boolean isDeleted
    }

    Collection {
        int id PK
        int partyID FK
        float paidAmount
        string modeOfPayment
        string paymentID
        string latitude
        string longitude
        boolean isApproved
        boolean isTallied
        int collectedBy FK
        int approvedBy FK
        boolean isDeleted
    }

    Sales {
        int id PK
        int partyID FK
        string invoiceNumber
        float amount
        boolean isApproved
        int createdBy FK
        int approvedBy FK
        date buildDate
        boolean isDeleted
    }

    CashCounter {
        int id PK
        int partyID FK
        string invoiceNumber
        string mode
        float amount
        float mixCashAmount
        float mixCardAmount
        int bankID FK
        int createdBy FK
        boolean isDeleted
    }

    Attendance {
        int id PK
        int staffID FK
        string registerType
        boolean isLogIn
        boolean isLogOut
        string login_latitude
        string login_longitude
        datetime loginDateTime
        datetime logoutDateTime
        boolean isDeleted
    }
```

---

## 🔒 Security Architecture

1. **Authentication & Session Management**:
   - Uses Django standard session cookies with configurable flags: `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, and `SECURE_SSL_REDIRECT`.
2. **Access Control**:
   - Custom decorators (`@check_group`, `@check_two_group`) ensure users only reach views mapped to their Django `auth.Group`.
3. **CSRF Protection**:
   - CSRF middleware active across all state-mutating HTTP POST requests, with configurable `CSRF_TRUSTED_ORIGINS`.
4. **Data Isolation**:
   - Customers (`Customer` group) can only view records referencing their own `Party` identity.
5. **Auditability**:
   - Audit timestamps (`datetime`, `lastUpdatedOn`) and actor foreign keys (`createdBy`, `collectedBy`, `approvedBy`) are logged on financial transactions.

## Container deployment

```mermaid
flowchart LR
    Proxy["TLS proxy"] --> Web["Gunicorn + WhiteNoise"]
    Web --> DB["SQLite bind mount or optional MySQL"]
    Web --> Redis["Redis"]
    Migration["Explicit migration job"] --> DB
    Worker["Scheduled opt-in notification job"] --> API["Configured notification endpoints"]
    Web --> Media["Persistent media bind mount"]
```

The application serves uploaded media to authenticated users. The worker runs once per invocation.

Compose places data, media, and MySQL in environment-specific host directories; a one-shot storage initialization service prepares application directory ownership.

Docker releases build a uniquely tagged image, validate migration drift, stop application writers, apply migrations once, then wait for the health probe before declaring success. A host lock serializes releases per stack.

Uploaded media is streamed by Django to authenticated active session users from the existing media bind mount, including when DEBUG is disabled. WhiteNoise handles static files.

- Authenticated media requests read from the sibling media_cdn directory locally or the persistent host bind mount at /media_cdn in Docker.
