from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import select, delete
from app.models import Company, Customer, Product, Invoice, InvoiceLine, TaxSummary, Sequence, Payment, Audit
from app.services.gst import calculate


def owned(db, model, ident, company_id, lock=False):
    query = select(model).where(model.id == ident, model.company_id == company_id)
    obj = db.scalar(query.with_for_update().execution_options(populate_existing=True) if lock else query)
    if not obj:
        raise HTTPException(404, 'Record not found')
    return obj


def audit(db, member, action, obj, detail=None):
    db.add(Audit(company_id=member.company_id, created_by=member.user_id, action=action,
                 entity=obj.__tablename__, entity_id=obj.id, detail=detail or {}))


def save_draft(db, member, data, invoice=None):
    customer = owned(db, Customer, data.customer_id, member.company_id)
    company = db.get(Company, member.company_id)
    rows = []
    for line in data.items:
        product = owned(db, Product, line.product_id, member.company_id)
        if not product.active:
            raise HTTPException(422, 'Inactive product')
        if not product.is_service:
            raise HTTPException(422, 'Goods invoicing is unavailable until stock posting is implemented; service invoices are supported')
        rows.append({**line.model_dump(mode='json'), 'name': product.name, 'hsn': product.hsn,
                     'unit': product.unit, 'price': str(product.price), 'gst_rate': str(product.gst_rate)})
    try:
        result = calculate(rows, company.state_code, data.supply_state, data.supply_rule, data.reverse_charge)
    except ValueError as exc:
        raise HTTPException(422,str(exc))
    values = data.model_dump(exclude={'items'})
    values.update(items=rows, snapshot={**result, 'seller': {'name': company.name, 'gstin': company.gstin, 'address': company.address},
                                       'customer': {'name': customer.name, 'gstin': customer.gstin, 'address': customer.address}},
                  taxable=Decimal(result['taxable']), tax=Decimal(result['tax']), total=Decimal(result['total']))
    if invoice:
        if invoice.status != 'draft':
            raise HTTPException(409, 'Issued financial content is immutable')
        for key, value in values.items():
            setattr(invoice, key, value)
    else:
        invoice = Invoice(company_id=member.company_id, created_by=member.user_id, **values)
        db.add(invoice)
    db.flush()
    db.execute(delete(InvoiceLine).where(InvoiceLine.company_id==member.company_id,InvoiceLine.invoice_id==invoice.id))
    db.execute(delete(TaxSummary).where(TaxSummary.company_id==member.company_id,TaxSummary.invoice_id==invoice.id))
    buckets={}
    for row in result['items']:
        amounts={key:Decimal(row[key]) for key in ('taxable','cgst','sgst','igst','total')}
        db.add(InvoiceLine(company_id=member.company_id,created_by=member.user_id,invoice_id=invoice.id,
            product_id=row['product_id'],description=row['name'],hsn=row['hsn'],quantity=Decimal(row['quantity']),
            unit_price=Decimal(row['price']),gst_rate=Decimal(row['gst_rate']),**amounts))
        rate=row['gst_rate']
        bucket=buckets.setdefault(rate,{key:Decimal(0) for key in ('taxable','cgst','sgst','igst')})
        for key in bucket: bucket[key]+=amounts[key]
    for rate,amounts in buckets.items():
        db.add(TaxSummary(company_id=member.company_id,created_by=member.user_id,invoice_id=invoice.id,gst_rate=Decimal(rate),**amounts))
    db.flush()
    audit(db, member, 'draft_saved', invoice)
    return invoice


def issue(db, member, ident):
    # Company lock serializes sequence initialization as well as increments.
    company = db.scalar(select(Company).where(Company.id == member.company_id).with_for_update())
    invoice = owned(db, Invoice, ident, member.company_id, lock=True)
    if invoice.status != 'draft':
        raise HTTPException(409, 'Only drafts can be issued')
    year = invoice.invoice_date.year - (invoice.invoice_date.month < 4)
    fy = f'{year}-{str(year+1)[-2:]}'
    # A locking current read is essential under MySQL REPEATABLE READ: the
    # authentication/membership SELECT may have established an older snapshot.
    sequence = db.scalar(select(Sequence).where(Sequence.company_id == member.company_id,
                         Sequence.financial_year == fy).with_for_update().execution_options(populate_existing=True))
    if not sequence:
        sequence = Sequence(company_id=member.company_id, financial_year=fy, value=0)
        db.add(sequence)
    sequence.value += 1
    invoice.number = f'{company.invoice_prefix}/{fy}/{sequence.value:05d}'
    invoice.status = 'issued'
    audit(db, member, 'invoice_issued', invoice, {'number': invoice.number})
    db.flush()
    return invoice


def record_payment(db, member, data):
    invoice = owned(db, Invoice, data.invoice_id, member.company_id, lock=True)
    existing = db.scalar(select(Payment).where(Payment.company_id == member.company_id,
                                              Payment.idempotency_key == data.idempotency_key).with_for_update())
    if existing:
        if (existing.invoice_id, existing.amount, existing.method, existing.payment_date, existing.reference) != (data.invoice_id, data.amount, data.method, data.payment_date, data.reference):
            raise HTTPException(409, 'Idempotency key was already used for another payment')
        return existing
    if invoice.status != 'issued':
        raise HTTPException(409, 'Payments require an issued invoice')
    if data.amount > invoice.total - invoice.paid:
        raise HTTPException(422, 'Payment exceeds outstanding balance')
    payment = Payment(company_id=member.company_id, created_by=member.user_id, **data.model_dump())
    db.add(payment)
    invoice.paid += data.amount
    db.flush()
    audit(db, member, 'payment_recorded', payment)
    return payment
