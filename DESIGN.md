# System & UI/UX Design Specifications (`DESIGN.md`)

This document defines the design patterns, UI/UX philosophy, role personas, API paradigms, and data modeling standards governing the **Baani Electricals (BSSAC)** application.

---

## 🎨 UI/UX Philosophy

The application balances two distinct interface modalities:
1. **Field Mobile Operations (PWA)**: Optimized for on-the-go collection staff on smartphones. Emphasizes low-latency input, touch-friendly tap targets (minimum 48px), automated geolocation tagging, and resilient performance under varying network connectivity.
2. **Back-Office & Admin Portal**: Optimized for desktop monitors. Features rich data tables, real-time filtering, bulk approval controls, accounting summaries, and PDF export dialogs.

---

## 👥 User Personas & Workflows

### 1. Field Collection Staff (`Collection` / `NormalStaff` Group)
- **Primary Goal**: Quickly log payments collected from retailers and electrical contractors on-site.
- **Key Interface**: `/collection_home/`, `/add_collection/`, `/my_collection/`.
- **Workflow**:
  - Staff logs in via mobile PWA.
  - Daily attendance clock-in with automated GPS coordinate logging (`login_latitude`, `login_longitude`).
  - Selects Party (retailer) from search dropdown.
  - Enters payment details: amount, payment mode (Cash, Cheque, NEFT/UPI), transaction/cheque ID, cheque clearance date.
  - GPS coordinates are silently captured by HTML5 Geolocation API and submitted with the payload.
  - Success alert notifies staff; collection status displays as "Pending Approval".

### 2. Cash Counter Operator (`CashCounter` Group)
- **Primary Goal**: High-speed, error-free retail counter billing and daily cash drawer reconciliation.
- **Key Interface**: `/take_collection/`, Counter Collection Views.
- **Workflow**:
  - Selects walk-in or registered party.
  - Selects payment composition: pure Cash, pure Card, or Split (`mixCashAmount` + `mixCardAmount`).
  - Enters counter expense vouchers if cash was disbursed for petty operational needs.
  - Automatically generates WeasyPrint thermal or A4 PDF invoices for immediate printing.

### 3. Sales Admin & Approver (`Admin`, `Moderator`, `SalesAdmin` Group)
- **Primary Goal**: Audit collections, verify bank deposits, approve or reject collections, and ensure ledger integrity before tallying.
- **Key Interface**: `/admin_home/`, `/collection_list/`, `/cheque_reminder_list/`.
- **Workflow**:
  - Admin reviews pending collections list populated via server-side DataTables.
  - Validates bank deposit details or cheque physical deposit.
  - Clicks "Approve"; backend tags `isApproved=True`, stamps `approvedBy` and `approvedOn`, and enqueues a WhatsApp receipt to the client.

### 4. Retail Customer / Party (`Customer` Group)
- **Primary Goal**: Verify statements of accounts, outstanding credit balance, and transaction history.
- **Key Interface**: `/customer_home/`, `/customer/change-password/`.
- **Workflow**:
  - Restricted self-service view showing only invoices and payments mapped to their `Party` entity.
  - Secure credential management for password resets.

---

## 📱 Progressive Web App (PWA) Architecture

- **Manifest Configuration**:
  - Name: `BSSAC`
  - Theme Color: `#272E38` (Deep Slate Charcoal)
  - Display Mode: `standalone` (Chromeless native app container)
  - Start URL: `/home/`
  - Icons: Multi-resolution icons (`192x192`, `512x512`, plus maskable formats for modern Android launchers).
- **Service Worker Lifecycle**:
  - Statically hosted via `static/sw/serviceworker.js` and exposed at the root `/serviceworker.js`.
  - Precaches essential navigation shell assets, stylesheets, and vendor scripts.
  - Intercepts offline requests with caching strategies to prevent disruption during intermittent cell reception.

---

## 🔌 API & Client-Server Contracts

### 1. DataTables Server-Side Processing
All high-volume lists (Collections, Parties, Users, Sales, Counter transactions) utilize jQuery DataTables with server-side processing via `django-datatables-view` in `home/apiView.py`.

**Standard DataTables Query Parameters**:
- `draw`: Sequence counter echoed back in the response.
- `start`: Pagination offset.
- `length`: Page size (e.g. 10, 25, 50, 100).
- `search[value]`: Search string applied across multiple columns (`name__icontains`, `phone__icontains`, etc.).
- `order[0][column]` & `order[0][dir]`: Dynamic sorting parameters.

**Standard Response Schema**:
```json
{
  "draw": 1,
  "recordsTotal": 1420,
  "recordsFiltered": 45,
  "data": [
    ["101", "Shree Balaji Electricals", "₹15,000.00", "Cash", "Approved", "2026-11-16 14:30", "...actions..."]
  ]
}
```

### 2. Mutation & Action APIs (JSON)
All form actions and status toggles submit via AJAX and expect consistent JSON responses:

**Success Response**:
```json
{
  "status": "success",
  "message": "Collection approved successfully."
}
```

**Error Response**:
```json
{
  "status": "error",
  "message": "Invalid collection ID or unauthorized operation."
}
```

---

## 🗄️ Data Modeling Standards

1. **Naming Conventions**:
   - Class names: `CamelCase` (e.g. `StaffUser`, `PartyGroup`, `CashCounter`).
   - Fields: `camelCase` for domain models (e.g. `paidAmount`, `modeOfPayment`, `isApproved`, `lastUpdatedOn`).
2. **Audit Timestamp Standard**:
   - Every operational model must feature:
     ```python
     datetime = models.DateTimeField(auto_now_add=True, auto_now=False)
     lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)
     ```
3. **Soft-Delete Invariant**:
   - Every business model must include:
     ```python
     isDeleted = models.BooleanField(default=False)
     ```
4. **Relational Integrity**:
   - Foreign keys to users, parties, or banks must use `on_delete=models.SET_NULL` with `blank=True, null=True` to prevent accidental cascading deletion of financial history.
