# GST rule scope and review

This is a limited calculation engine, not a certified GST compliance engine. A qualified practitioner must approve classification, rates, place-of-supply determination, invoice requirements, and effective-date rules before real use. Current configured rule identifier: domestic-v1.

- Operator supplies a confirmed GST place-of-supply code and selects standard domestic or taxable SEZ rule. Standard supplies split tax only after this rule selection. SEZ forces interstate treatment. Zero-rated SEZ and export/LUT supplies are not supported.
- Tax rates are supplied by the catalog administrator. Automatic classification, effective-dated tax-rate master, nil/exempt/non-GST distinctions, and tax eligibility are pending.
- Gross = unit price × quantity. Item percentage discount reduces gross. Inclusive pricing divides discounted gross by (1 + rate/100). Taxable amount and tax round HALF_UP to 2 decimals per line. Intrastate CGST rounds half tax and SGST receives the residual so components reconcile exactly. Invoice totals sum rounded lines. Practitioner approval of this policy is required, especially odd-paise splits.
- RCM tax is displayed in the snapshot but is not added to customer payable amount or dashboard output tax collectible.
- No cess, invoice-level discounts, freight/other charges, credit/debit notes, refunds, export validation, e-invoice eligibility, IRN API, or e-way bill API is implemented.
- GSTIN validation currently checks syntax only; checksum, state correspondence and portal status validation are pending.

No report is represented as filed. Authorized GST integrations must preserve real request/response evidence and keep encrypted credentials server-side. Until a verified adapter is configured, those operations must fail explicitly.
