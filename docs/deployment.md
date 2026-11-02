# Vercel deployment — 2 November 2026

React and FastAPI deploy together in **one Vercel project** using Vercel Services (currently beta). Render is no longer used. The repository root vercel.json defines frontend/ (Vite) and backend/ (FastAPI, app.main:app).

Application: https://gst-billing-pro.vercel.app

Project: gst-billing-pro, team bebin-dotms-projects. Set the Vercel project root to the repository root, not frontend/. Service-specific build settings are in vercel.json. /api/*, /health*, /docs and /openapi.json go directly to FastAPI; other paths resolve through the frontend SPA. No BACKEND_URL or separate backend hostname is required. Cookies stay on the same HTTPS origin. Existing deployment protection is preserved.

## MySQL is required

The user explicitly chose to **keep MySQL**. No MySQL integration is currently connected. Vercel's persistent databases are supplied through integrations; its function filesystem cannot store the business database. PostgreSQL, SQLite and temporary files have not been substituted.

Open [Vercel Storage](https://vercel.com/bebin-dotms-projects/gst-billing-pro/stores) and connect managed MySQL. [Railway's Vercel integration](https://vercel.com/marketplace/railway) can connect MySQL databases. The owner must complete provider account setup and any plan purchase. No paid database was purchased. TiDB is MySQL-compatible but is a different database; it was not substituted for MySQL 8.

Set the provider's SQLAlchemy connection URL directly as the **server-only production secret** DATABASE_URL in Vercel, using mysql+pymysql:// and certificate-verified TLS parameters. Do not put credentials in chat, GitHub, VITE_* variables or screenshots. Use a dedicated application database/user and automated backups.

Until connected, /health returns liveness, while /health/ready and business API calls return explicit 503 errors. Backend liveness is not proof of database readiness; login and billing remain unavailable.

## Environment and migrations

JWT_SECRET was generated securely and stored as a production secret without writing it into source or logs. CORS_ORIGINS and FRONTEND_URL are https://gst-billing-pro.vercel.app; SECURE_COOKIES=true; REGISTRATION_ENABLED=false. Configure a separate signing secret before using preview environments.

After connecting the database, apply migrations from backend/ in a trusted terminal with DATABASE_URL and JWT_SECRET configured as protected environment variables:

```powershell
python -m alembic upgrade head
python -m alembic check
```

Do not migrate on every request or cold start. Redeploy after changing Vercel environment variables. Confirm /health/ready returns 200, then temporarily enable registration for administrator onboarding and disable it afterward. SMTP requires its own connection and delivery checks.

## Verification and remaining gates

Twenty backend tests passed locally; three opt-in MySQL tests were skipped because the disposable MySQL instance is stopped. Those three concurrency/reference tests passed in the earlier local run. Missing-database behavior has an explicit API test. The frontend tests and build previously passed.

Before business use, finish the remaining modules and test deployed registration, tenant isolation, refresh/logout, invoices/PDFs/payments and reports against the real database. The in-process limiter must become distributed for serverless scaling. Check connection limits, migrations, backup restore, qualified GST rules and mandatory invoice particulars. This remains an incomplete accounting application.

References: [Services](https://vercel.com/docs/services), [FastAPI](https://vercel.com/docs/frameworks/backend/fastapi), [Storage integrations](https://vercel.com/marketplace).
