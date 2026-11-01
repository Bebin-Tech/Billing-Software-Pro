# Database schema and module plan

All implemented tenant records carry company_id; catalog, invoices, payments, invoice lines/tax summaries and audit records also carry created_by and timestamps. IDs currently use INTEGER; migration to BIGINT is required before large-scale deployment. Financial columns are DECIMAL(18,2), rate columns DECIMAL(9,4), quantity columns DECIMAL(18,4), dates use DATE, timestamps are UTC-naive DATETIME. Application services enforce same-company references; composite foreign keys additionally enforce customer/invoice/product ownership on financial records.

## Implemented tables

| Table | Purpose / relationships / constraints |
|---|---|
| users | Global user identity; unique normalized email, bcrypt hash, failure counter, lockout deadline |
| companies | Independent tenant; business identity, state, address, invoice prefix |
| user_company_memberships | User/company authorization; unique user + company; role checked server-side |
| refresh_tokens | Hashed opaque session, user FK, family index, expiration and revocation; hashes unique |
| customers | Company-scoped billing contact and address |
| products | Goods/service catalog, explicit price and rate; unique company + SKU |
| sales_invoices | Customer FK, draft/issued/cancelled lifecycle, immutable issued totals and snapshots; unique company + issued number |
| invoice_sequences | Composite primary key company + financial year; company lock serializes increments |
| payments | Invoice FK, decimal amount/date/method; unique company + idempotency key; locked service validates balance |
| audit_logs | Append-only application event record with actor, tenant, entity and detail |
| password_reset_tokens, email_verification_tokens | User FK, unique hashed single-use action token, expiry and consumed flag; password reset revokes sessions |
| sales_invoice_items | Normalized line snapshots; quantity, original price/HSN/description/rate and reconciled components; tenant-safe invoice/product foreign keys |
| invoice_tax_summaries | One row per invoice/rate; taxable and component amounts; unique company/invoice/rate and tenant-safe invoice FK |

JSON calculation snapshots preserve the full original calculation and party details alongside normalized rows. Historical invoice snapshots survive catalog/customer changes. No unused tables were created for future modules.

## Remaining requested tables (create with their actual modules)

| Tables | Purpose and planned relationships / constraints |
|---|---|
| roles, permissions, role_permissions | Granular permission definitions and unique role/permission grants; replace current fixed role map |
| branches, warehouses | Company locations and warehouse/branch relationships; tenant-scoped codes |
| financial_years, company_settings | Company date ranges (nonoverlapping) and validated configuration |
| tax_rates, tax_categories | Qualified, effective-dated tax applicability and classifications; prohibit overlapping validity for a category/rule |
| units, payment_methods, expense_categories | Company-scoped configuration with unique codes and deactivation policy |
| customer_addresses, suppliers, supplier_addresses | Party and address relationships, tenant-safe FKs; supplier invoice validation uses supplier identity |
| product_categories, services | Catalog classifications and dedicated service records, tenant-safe unique codes |
| stock_balances, stock_movements | Locked warehouse/product balance and immutable signed quantity ledger; references posting source |
| stock_transfers, stock_adjustments | Authorized movement documents; atomic paired transfer movements and reasoned adjustment trails |
| inventory_batches | FIFO receipt cost layers; positive quantities, locked allocation and traceable cost consumption |
| quotations, quotation_items | Non-posting sales offers and normalized lines; tenant/document FK, version/status |
| credit_notes, credit_note_items, debit_notes, debit_note_items | Immutable correction documents and lines linked to original issued invoices; bounded adjustments and independent numbering |
| sales_returns | Returned goods authorization linked to invoice and stock reversal |
| purchase_orders, purchase_order_items | Non-posting supplier orders and normalized lines |
| purchase_invoices, purchase_invoice_items | Supplier bills and tax snapshots; unique company/supplier/invoice-number/date according to policy |
| purchase_returns, purchase_return_items | Posted purchase corrections, linked to purchase and stock reversal |
| payment_allocations | Many-to-many party/payment/document allocations; locked aggregate cannot exceed payment or document balance |
| refunds | Explicit payment reversals linked to original receipt and correction; idempotent posting |
| expenses, expense_attachments | Expense document, category, party and validated receipt references |
| bank_accounts, bank_transactions | Company bank identity and reconciled cash movements; unique imported external reference |
| customer_ledger, supplier_ledger | Immutable debit/credit postings with unique source keys and reconcilable balances |
| gst_return_periods, gst_return_summaries | Period selection and versioned preparation snapshot; never implies filing |
| gst_reconciliations, gst_reconciliation_items | Imported register comparison and item resolutions with evidence references |
| einvoice_records, eway_bill_records | Authorized integration request/result; real IRN/ack/QR/validity/status only, linked to invoice/company |
| external_api_logs | Redacted adapter evidence and request correlation; no credentials |
| notifications | Company/user event delivery and read state |
| file_attachments | Validated metadata, scoped storage key, MIME/size/hash and authorized retrieval |
| background_jobs | Idempotent job state, attempts, failure reason and scheduling |
| application_settings | Platform-level configuration; restricted platform administration |

Every future tenant-owned table requires company_id, tenant-safe foreign keys, actor/timestamps and appropriate lookup indexes. Soft deletion must not remove posted financial history. Financial corrections must use reversible ledger entries rather than mutation.
