# GST Billing Pro

A React / FastAPI / SQLAlchemy application targeting MySQL 8. This repository is an **in-progress implementation**, not a completed production accounting system. See [PROJECT_PROGRESS.md](PROJECT_PROGRESS.md) for exact scope and verification.

Implemented workflow: register an administrator and company (when enabled), sign in, create customers and services, save invoice drafts, review authoritative server totals, issue immutable invoices, download PDFs, record partial payments, inspect business metrics and audit events. No sample business transactions are seeded. Goods billing is deliberately blocked until inventory posting is implemented.

Recovery/verification forms, session revocation, draft editing, a limited sales/GST preparation workspace and sales Excel export are also implemented. SMTP must be configured for actual email delivery; no production emails were sent during testing.

## Windows setup

Install Python 3.13, Node.js 22+, and MySQL 8 or Docker Desktop. Open this directory in VS Code. All commands below use PowerShell.

```powershell
cd 'C:\Users\bbebi\OneDrive\Documents\Billing Software Pro\gst-billing-pro'
Copy-Item .env.example backend\.env
# Generate a secret, then put the output in backend/.env as JWT_SECRET:
py -3.13 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Choose strong database passwords. Set these in your current shell, without committing them:

```powershell
$env:MYSQL_PASSWORD = Read-Host 'MySQL application password'
$env:MYSQL_ROOT_PASSWORD = Read-Host 'MySQL root password'
docker compose up -d mysql
docker compose ps
```

Set `DATABASE_URL` in `backend/.env` to match your password (URL-encode special characters). Set `REGISTRATION_ENABLED=true` for initial onboarding. Disable it again after creating required accounts. This flag currently permits self-service company creation by any registering user; it is not a platform admin interface.

```powershell
cd backend
py -3.13 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Use **Terminal → New Terminal** in VS Code (or Ctrl+Shift+backtick) to open a second PowerShell terminal:

```powershell
cd 'C:\Users\bbebi\OneDrive\Documents\Billing Software Pro\gst-billing-pro\frontend'
npm ci
npm run dev
```

Open [the application](http://127.0.0.1:5173). Backend [OpenAPI documentation](http://127.0.0.1:8000/docs). The Vite development proxy keeps refresh cookies on the frontend origin. Use the same hostname consistently throughout a session. `SECURE_COOKIES=false` is for HTTP local development only.

## Verify

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m pytest -q
cd ..\frontend
npm run build
```

Fast tests use isolated SQLite databases. Opt-in MySQL tests cover actual concurrent numbering/payment locks and database tenant constraints; run `scripts/verify-mysql.ps1` against an explicitly disposable `gst_test_*` database. These tests and migration round-trip checks passed locally on MySQL 8.0.46. The complete production release gates remain open; see [deployment notes](docs/deployment.md).

The preinstalled Python available during implementation was 3.14; Python 3.13 remains the recommended target and still needs a compatibility run. An installed project environment is present at `backend/.venv`; activate it with `.\.venv\Scripts\Activate.ps1` instead of creating a second environment if using that verified runtime. Local development requires your own `.env` database configuration. Disposable browser QA used a separate schema and was never a production deployment.

## Tax scope

The calculator supports standard domestic service supplies, taxable interstate SEZ supply, inclusive/exclusive pricing, item percentage discounts, mixed rates, and reverse charge. Rates are explicit catalog configuration; no universal product classification or statutory applicability is inferred. The operator must confirm the legal place of supply. No GST portal filing, IRN, e-way bill, or official return status is claimed. See [GST scope](docs/gst-rules.md).
