# Architecture

React + TypeScript + Vite renders authenticated, company-aware business pages. TanStack Query handles reads and cache invalidation; Axios attaches a short-lived memory-only access token and company header. Refresh tokens are opaque HttpOnly cookies, hashed in the database, rotated on refresh, and grouped for reuse revocation. Origin validation protects refresh/logout; cookies use SameSite Strict and must be Secure in production. Login passwords use bcrypt with 12 rounds and a 72-byte maximum.

FastAPI validates Pydantic schemas and enforces role permissions. Tenant selection is never accepted without checking the authenticated user's membership. Tenant record retrieval always includes company_id, including cross-record references during draft creation and payments. SQLAlchemy transactions encompass draft creation, sequence assignment, payments and audit entries. Issuance locks the company row, then the invoice; this serializes first-use sequence creation and numbering per company on MySQL. Payments lock the invoice to prevent over-allocation. Financial totals and item/customer/seller snapshots are preserved on issuance. Issued financial content cannot be edited.

The Decimal-only GST calculator is the single source for financial totals; the browser displays returned totals. Dashboard cash comes from payment dates, turnover from issued invoice dates, and cancelled invoices are excluded. Receivables represent current balances for invoices selected by invoice date, not a historical as-of ledger. Profit, ITC and purchases are not fabricated from sales totals.

Normalized invoice lines and tax summaries accompany the immutable JSON calculation snapshot. Composite financial foreign keys prevent cross-company references at the database boundary. Database dependencies use function scope so transaction commits finish before HTTP responses are delivered; failed commits cannot leave the browser believing an uncommitted write succeeded.

Recovery/verification email uses SMTP with STARTTLS and certificate verification. Action tokens are hashed, single-use and expire in 30 minutes. Password reset invalidates all sessions. Deployment can require verified email before access. No mail was sent during testing; the adapter was mocked. Session listings never expose token hashes or secrets.

Current boundaries: stock, supplier accounting, statutory integrations, attachments, and jobs are not yet implemented. The current in-process auth limiter needs a shared-store replacement before multi-worker deployment. Refreshes in multiple browser tabs are not coordinated; concurrent use may trigger reuse protection. Access is read on each request so membership revocation takes effect immediately.

Technical references: [FastAPI JWT security](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) and [SQLAlchemy transaction isolation](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html).
