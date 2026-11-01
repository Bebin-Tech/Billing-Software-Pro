# Project progress

Updated: 1 November 2026. **In progress; not production-ready.**

## Implemented and initially verified

- React/TypeScript/Vite application with responsive light accounting workspace, sidebar, company selector, server-backed tables, empty/error/loading states and invoice charts.
- FastAPI versioned routes, Pydantic input validation, SQLAlchemy models, Alembic initial migration, MySQL configuration and Docker development setup.
- Administrator registration controlled by environment flag; bcrypt login, lockout, in-process auth rate limit, short-lived JWT access, hashed refresh cookies, rotation/reuse revocation, logout, active-session inspection/revocation.
- SMTP adapter, hashed expiring single-use recovery/verification tokens, password reset with session revocation, optional verification requirement and connected recovery/verification forms. Actual delivery requires SMTP configuration; tests use a mocked sender and no real email was sent.
- Multiple companies per user, current membership validation and fixed server-side role permissions; existing-account member assignment.
- Customer and goods/service catalog creation and searchable pagination; update/detail APIs and product deactivation API.
- Decimal calculator for the documented limited supply scope; server-calculated service invoice drafts, draft editing/review, locked numbering/issuance, immutable issued financial content, A4 PDF, unpaid cancellation with reason and audit. Normalized line/tax summary records and composite tenant-safe financial foreign keys accompany immutable JSON snapshots.
- Partial invoice payments with locked over-allocation checks and idempotency keys; payment history, actual dashboard turnover/cash/receivables/GST and monthly chart.
- Audit events, health checks, explicit unconfigured GST provider interface, Windows setup and architecture/schema/API/deployment/GST documentation.
- Sales register, limited outward-supply/HSN preparation summary, financial-year/date selection, print styling and sales Excel export with formula-injection protection. These are not complete GSTR-1/GSTR-3B reports and never imply filing.

## Verification evidence

- Backend: **22 tests passed in the installed project .venv on Python 3.14** (19 SQLite/unit/API tests + 3 real MySQL tests). Covers GST rates/rounding/inclusive/discount/mixed rules and storage overflow, service invoice/PDF/payment workflow, immutability, payment retry/overpayment, tenant isolation, permissions, cancellation, refresh reuse, reset/verification single use, session revocation, and report/Excel totals. One non-failing installed-library deprecation warning concerns Starlette's future test transport.
- Real MySQL 8.0.46: migrations 0001–0003 upgrade and schema comparison passed. Twelve concurrent invoices received unique sequential numbers; competing payments could not overallocate; a direct cross-company customer reference was rejected by the database. Migration downgrade/upgrade round trip also passed.
- Frontend: **five component/workflow tests passed**; final TypeScript and production bundle build passed. Patched dependency audit reports **zero vulnerabilities**. Rollup emits harmless annotation warnings from the installed Zod package.
- Real HTTP + browser: sign-in, live dashboard, invoice register/detail and partial payment verified against a separate disposable MySQL schema. A real HTTP race was fixed by committing dependencies before sending responses. Numbering snapshot isolation was fixed using a locking current read. Browser payment showed INR 500 paid and INR 680 outstanding against INR 1,180; screenshot: docs/qa-payment.png. No QA records were seeded into a production database.
- Complete responsive/accessibility sweep, full browser E2E suite and PDF visual QA remain pending.

## Remaining phases / incomplete requirements

1. Foundation: platform super-admin/subscriptions, configurable granular permission tables, complete company fields and BIGINT IDs. Email delivery must be verified with real SMTP credentials. Session device/IP metadata and cross-tab refresh coordination remain incomplete.
2. Workspace: full user lifecycle/role editing, global search, financial-year selector, notification center, help/profile, company creation UI and comprehensive settings.
3. Masters: update/deactivate UI, supplier CRUD, qualified effective-dated tax masters, category/unit masters, complete party/catalog fields and dedicated normalized services.
4. Billing: invoice-level discount, cess/charges/roundoff, exempt/nil/non-GST and special supply rules, quotations, credit/debit notes, duplicate draft, email, A5/thermal templates and mandatory invoice particulars including amount in words/banking. Customer/product pickers currently load at most 100 records and need server-side search before large catalogs.
5. Purchases/inventory: supplier bills/orders, receiving, auditable stock ledger/warehouse transfers/adjustments, negative-stock policy, FIFO batches and returns. Goods invoicing is blocked until this is complete.
6. Finance: multi-document allocation, advances/refunds, expenses/attachments, banking, customer/supplier ledgers, full payables and aging.
7. GST: complete GSTR-1/GSTR-3B preparation, imported-register reconciliation, qualified ITC eligibility, authorized e-invoice/e-way-bill adapters and credentials. No GST portal filing is implemented or claimed.
8. Advanced reports: P&L/cashflow/stock reports, remaining PDF/Excel exports, notification delivery, background jobs and richer charts based on actual data.
9. Production: distributed rate limiting, cross-tab refresh coordination, broader security/dependency review, complete MySQL API suite and browser E2E tests, performance/accessibility/PDF review, backup restore validation, monitoring and actual Vercel/Render/managed-MySQL deployment.

## External dependencies

Production hosting/database/domain access, SMTP provider, authorized GST provider and practitioner-approved GST rules remain unconfigured. No fabricated records, portal responses, filing status or deployment claims are used.

Temporary local browser/backend/MySQL QA servers were stopped after verification. Configure a development database and follow README.md to run your own workspace. The saved screenshot is explicitly from disposable QA records and is not a production account or deployment.
