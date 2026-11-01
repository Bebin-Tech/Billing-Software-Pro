# API

Interactive schemas are generated at `/docs`; machine-readable spec is `/openapi.json`. Versioned routes use `/api/v1`. Protected routes require `Authorization: Bearer <access-token>`. Tenant routes additionally require `X-Company-ID` corresponding to a current membership. Resource IDs outside the selected company return 404. Missing membership or permission returns 403.

Implemented: registration, login, refresh, logout, profile; company list/create/update; existing-account company membership list/add; customer list/create; catalog list/create; invoice list/detail/create draft/update draft/issue/cancel/PDF; payment list/create; dashboard summary; audit list. List endpoints use page/page_size where provided; catalog/customer/invoice lists support q. Amounts are returned as decimal strings. Errors use FastAPI's detail envelope, including 422 field errors.

Also implemented: customer/catalog detail and update; catalog deactivation; forgot/reset password; email verification request/consume; active session list/revoke; date-filtered `/reports/sales`, `/reports/sales.xlsx` and `/reports/gst-preparation`. The GST route is a limited outward-supply/HSN preparation summary and explicitly excludes complete return preparation and filing. Catalog/customer editing currently has API support but no editing UI.

`POST /payments` requires an idempotency_key (16–64 characters). The key must be reused for retries of the same payment; mismatched reuse is rejected. A payment cannot exceed the locked invoice's outstanding balance. Invoice creation never implies a payment. Cancellation currently supports unpaid issued invoices only and requires a reason of 10–500 characters.

Health endpoints: `/health` (liveness) and `/health/ready` (database connectivity). Readiness does not yet check migration version. Routes for unimplemented modules are intentionally absent; no successful dummy responses exist.
