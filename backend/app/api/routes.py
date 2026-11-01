from datetime import timedelta, date
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, update
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from app.core.config import settings
from app.core.database import get_db
from app.core.security import current_user, tenant, require, passwords, create_session, access_token, digest
from app.models import User, Company, Membership, Session, Customer, Product, Invoice, Payment, Audit, now
from app.schemas import Login, Register, CompanyInput, CustomerInput, ProductInput, DraftInput, PaymentInput, CancelInput, MemberInput
from app.services.billing import owned, audit, save_draft, issue, record_payment
from app.schemas import EmailActionInput, ActionTokenInput, ResetPasswordInput
from app.services.accounts import request_action, consume_action

router = APIRouter(prefix='/api/v1')


@router.post('/auth/forgot-password')
def forgot_password(data: EmailActionInput, db=Depends(get_db, scope='function')):
    return request_action(db,data.email)


@router.post('/auth/reset-password')
def reset_password(data: ResetPasswordInput, db=Depends(get_db, scope='function')):
    return consume_action(db,data.token,data.password)


@router.post('/auth/request-verification')
def request_verification(data: EmailActionInput, db=Depends(get_db, scope='function')):
    return request_action(db,data.email,verification=True)


@router.post('/auth/verify-email')
def verify_email(data: ActionTokenInput, db=Depends(get_db, scope='function')):
    return consume_action(db,data.token)


def serialize(obj):
    return jsonable_encoder({c.name: getattr(obj, c.name) for c in obj.__table__.columns}, custom_encoder={Decimal: str})


def credentials(response, user, session, token):
    response.set_cookie('refresh_token', token, httponly=True, secure=settings.secure_cookies,
                        samesite='strict', path='/api/v1/auth', max_age=604800)
    return {'access_token': access_token(user, session), 'token_type': 'bearer', 'user': {'id': user.id, 'name': user.name, 'email': user.email}}


def check_origin(request):
    if request.headers.get('origin') not in settings.cors_origins.split(','):
        raise HTTPException(403, 'Untrusted request origin')


@router.post('/auth/register', status_code=201)
def register(data: Register, response: Response, db=Depends(get_db, scope='function')):
    if not settings.registration_enabled:
        raise HTTPException(403, 'Registration is disabled by administrator')
    if db.scalar(select(User).where(User.email == str(data.email).lower())):
        raise HTTPException(409, 'Email already registered')
    user = User(email=str(data.email).lower(), name=data.name, password_hash=passwords.hash(data.password))
    company = Company(name=data.company_name, state_code=data.state_code)
    db.add_all([user, company]); db.flush()
    db.add(Membership(user_id=user.id, company_id=company.id, role='company_admin'))
    if settings.require_email_verification:
        return {'verification_required':True,'detail':'Account created. Request an email verification link before signing in.'}
    session, token = create_session(db, user)
    return credentials(response, user, session, token)


@router.post('/auth/login')
def login(data: Login, response: Response, db=Depends(get_db, scope='function')):
    user = db.scalar(select(User).where(User.email == str(data.email).lower()).with_for_update())
    if user and user.locked_until and user.locked_until > now():
        raise HTTPException(429, 'Account temporarily locked; retry in 15 minutes')
    if not user or not passwords.verify(data.password, user.password_hash):
        if user:
            user.failed_attempts += 1
            if user.failed_attempts >= 5:
                user.locked_until = now() + timedelta(minutes=15)
            db.commit()
        raise HTTPException(401, 'Invalid email or password')
    user.failed_attempts = 0; user.locked_until = None
    if settings.require_email_verification and not user.email_verified:
        raise HTTPException(403, 'Verify your email before signing in. Request a verification link below.')
    session, token = create_session(db, user)
    return credentials(response, user, session, token)


@router.post('/auth/refresh')
def refresh(request: Request, response: Response, db=Depends(get_db, scope='function')):
    check_origin(request)
    token = request.cookies.get('refresh_token', '')
    record = db.scalar(select(Session).where(Session.token_hash == digest(token)).with_for_update())
    if not record or record.expires_at < now():
        raise HTTPException(401, 'Session expired')
    if record.revoked:
        db.execute(update(Session).where(Session.family == record.family).values(revoked=True)); db.commit()
        raise HTTPException(401, 'Session reuse detected; sign in again')
    record.revoked = True
    user = db.get(User, record.user_id)
    session, token = create_session(db, user, record.family)
    return credentials(response, user, session, token)


@router.post('/auth/logout', status_code=204)
def logout(request: Request, response: Response, db=Depends(get_db, scope='function')):
    check_origin(request)
    record = db.scalar(select(Session).where(Session.token_hash == digest(request.cookies.get('refresh_token', ''))))
    if record:
        db.execute(update(Session).where(Session.family == record.family).values(revoked=True))
    response.delete_cookie('refresh_token', path='/api/v1/auth')


@router.get('/auth/me')
def me(user=Depends(current_user)):
    return {'id': user.id, 'name': user.name, 'email': user.email}


@router.get('/auth/sessions')
def sessions(user=Depends(current_user),db=Depends(get_db,scope='function')):
    rows=db.scalars(select(Session).where(Session.user_id==user.id,Session.revoked==False,Session.expires_at>now()).order_by(Session.id.desc()))
    return [{'id':row.id,'created_at':row.created_at,'expires_at':row.expires_at} for row in rows]


@router.post('/auth/sessions/{ident}/revoke',status_code=204)
def revoke_session(ident:int,user=Depends(current_user),db=Depends(get_db,scope='function')):
    record=db.scalar(select(Session).where(Session.id==ident,Session.user_id==user.id).with_for_update())
    if not record: raise HTTPException(404,'Session not found')
    db.execute(update(Session).where(Session.family==record.family,Session.user_id==user.id).values(revoked=True))


@router.get('/companies')
def companies(user=Depends(current_user), db=Depends(get_db, scope='function')):
    rows = db.execute(select(Company, Membership.role).join(Membership, Membership.company_id == Company.id).where(Membership.user_id == user.id))
    return [{**serialize(company), 'role': role} for company, role in rows]


@router.post('/companies', status_code=201)
def add_company(data: CompanyInput, user=Depends(current_user), db=Depends(get_db, scope='function')):
    company = Company(**data.model_dump()); db.add(company); db.flush()
    db.add(Membership(user_id=user.id, company_id=company.id, role='company_admin'))
    return serialize(company)


@router.put('/companies/{ident}')
def edit_company(ident: int, data: CompanyInput, member=Depends(require('settings')), db=Depends(get_db, scope='function')):
    if ident != member.company_id:
        raise HTTPException(404, 'Company not found')
    company = db.get(Company, ident)
    for key, value in data.model_dump().items(): setattr(company, key, value)
    audit(db, member, 'settings_changed', company)
    return serialize(company)


@router.get('/users')
def members(member=Depends(require('users')), db=Depends(get_db, scope='function')):
    rows = db.execute(select(User, Membership.role).join(Membership, Membership.user_id == User.id).where(Membership.company_id == member.company_id))
    return [{'id': user.id, 'name': user.name, 'email': user.email, 'role': role} for user, role in rows]


@router.post('/users', status_code=201)
def add_member(data: MemberInput, member=Depends(require('users')), db=Depends(get_db, scope='function')):
    user = db.scalar(select(User).where(User.email == str(data.email).lower()))
    if not user: raise HTTPException(404, 'User must have an existing account')
    if db.scalar(select(Membership).where(Membership.user_id == user.id, Membership.company_id == member.company_id)):
        raise HTTPException(409, 'User is already a company member')
    record = Membership(company_id=member.company_id, user_id=user.id, role=data.role)
    db.add(record); db.flush(); audit(db, member, 'member_added', record)
    return {'id': record.id}


def listing(model, db, member, q='', page=1, page_size=25):
    query = select(model).where(model.company_id == member.company_id)
    if q:
        field = model.number if model == Invoice else model.name
        query = query.where(field.contains(q, autoescape=True))
    count = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(model.id.desc()).offset((page-1)*page_size).limit(page_size))
    return {'items': [serialize(row) for row in rows], 'total': count, 'page': page, 'page_size': page_size}


@router.get('/customers')
def customers(q: str = '', page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), member=Depends(tenant), db=Depends(get_db, scope='function')):
    return listing(Customer, db, member, q, page, page_size)


@router.post('/customers', status_code=201)
def add_customer(data: CustomerInput, member=Depends(tenant), db=Depends(get_db, scope='function')):
    if member.role not in ('company_admin', 'accountant', 'billing_staff'):
        raise HTTPException(403, 'Permission denied')
    obj = Customer(company_id=member.company_id, created_by=member.user_id, **data.model_dump())
    db.add(obj); db.flush(); audit(db, member, 'customer_created', obj)
    return serialize(obj)


@router.get('/products')
def products(q: str = '', page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), member=Depends(tenant), db=Depends(get_db, scope='function')):
    return listing(Product, db, member, q, page, page_size)


@router.post('/products', status_code=201)
def add_product(data: ProductInput, member=Depends(require('catalog')), db=Depends(get_db, scope='function')):
    obj = Product(company_id=member.company_id, created_by=member.user_id, **data.model_dump())
    db.add(obj); db.flush(); audit(db, member, 'product_created', obj)
    return serialize(obj)


@router.get('/products/{ident}')
def get_product(ident:int,member=Depends(tenant),db=Depends(get_db,scope='function')):
    return serialize(owned(db,Product,ident,member.company_id))


@router.put('/products/{ident}')
def edit_product(ident:int,data:ProductInput,member=Depends(require('catalog')),db=Depends(get_db,scope='function')):
    obj=owned(db,Product,ident,member.company_id,lock=True)
    for key,value in data.model_dump().items(): setattr(obj,key,value)
    audit(db,member,'product_updated',obj)
    return serialize(obj)


@router.delete('/products/{ident}',status_code=204)
def deactivate_product(ident:int,member=Depends(require('catalog')),db=Depends(get_db,scope='function')):
    obj=owned(db,Product,ident,member.company_id,lock=True)
    obj.active=False
    audit(db,member,'product_deactivated',obj)


@router.get('/customers/{ident}')
def get_customer(ident:int,member=Depends(tenant),db=Depends(get_db,scope='function')):
    return serialize(owned(db,Customer,ident,member.company_id))


@router.put('/customers/{ident}')
def edit_customer(ident:int,data:CustomerInput,member=Depends(tenant),db=Depends(get_db,scope='function')):
    if member.role not in ('company_admin','accountant','billing_staff'):
        raise HTTPException(403,'Permission denied')
    obj=owned(db,Customer,ident,member.company_id,lock=True)
    for key,value in data.model_dump().items(): setattr(obj,key,value)
    audit(db,member,'customer_updated',obj)
    return serialize(obj)


@router.get('/invoices')
def invoices(q: str = '', page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), member=Depends(tenant), db=Depends(get_db, scope='function')):
    return listing(Invoice, db, member, q, page, page_size)


@router.post('/invoices/drafts', status_code=201)
def draft(data: DraftInput, member=Depends(require('invoice')), db=Depends(get_db, scope='function')):
    return serialize(save_draft(db, member, data))


@router.get('/invoices/{ident}')
def invoice(ident: int, member=Depends(tenant), db=Depends(get_db, scope='function')):
    return serialize(owned(db, Invoice, ident, member.company_id))


@router.put('/invoices/{ident}/draft')
def edit_draft(ident: int, data: DraftInput, member=Depends(require('invoice')), db=Depends(get_db, scope='function')):
    return serialize(save_draft(db, member, data, owned(db, Invoice, ident, member.company_id, lock=True)))


@router.post('/invoices/{ident}/issue')
def issue_invoice(ident: int, member=Depends(require('invoice')), db=Depends(get_db, scope='function')):
    return serialize(issue(db, member, ident))


@router.post('/invoices/{ident}/cancel')
def cancel(ident: int, data: CancelInput, member=Depends(require('invoice')), db=Depends(get_db, scope='function')):
    obj = owned(db, Invoice, ident, member.company_id, lock=True)
    if obj.status != 'issued' or obj.paid:
        raise HTTPException(409, 'Only unpaid issued invoices can be cancelled; paid corrections require credit/refund workflows')
    obj.status = 'cancelled'; obj.cancellation_reason = data.reason
    audit(db, member, 'invoice_cancelled', obj, {'reason': data.reason})
    return serialize(obj)


@router.get('/payments')
def payments(page: int = Query(1, ge=1), member=Depends(tenant), db=Depends(get_db, scope='function')):
    return listing(Payment, db, member, page=page)


@router.post('/payments', status_code=201)
def pay(data: PaymentInput, member=Depends(require('payment')), db=Depends(get_db, scope='function')):
    return serialize(record_payment(db, member, data))


@router.get('/dashboard/summary')
def summary(start: date | None = None, end: date | None = None, member=Depends(tenant), db=Depends(get_db, scope='function')):
    query = select(Invoice).where(Invoice.company_id == member.company_id, Invoice.status == 'issued')
    if start: query = query.where(Invoice.invoice_date >= start)
    if end: query = query.where(Invoice.invoice_date <= end)
    rows = list(db.scalars(query))
    zero = Decimal(0)
    cash_query = select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.company_id == member.company_id)
    if start: cash_query = cash_query.where(Payment.payment_date >= start)
    if end: cash_query = cash_query.where(Payment.payment_date <= end)
    monthly = {}
    for row in rows:
        key = row.invoice_date.strftime('%Y-%m')
        monthly[key] = monthly.get(key, zero) + row.taxable
    return {'taxable_turnover': str(sum((r.taxable for r in rows), zero)),
            'output_gst': str(sum((r.tax for r in rows if not r.reverse_charge), zero)),
            'invoice_value': str(sum((r.total for r in rows), zero)),
            'cash_received': str(db.scalar(cash_query)),
            'receivables': str(sum((r.total-r.paid for r in rows), zero)), 'invoice_count': len(rows),
            'overdue_count': sum(r.due_date < date.today() and r.paid < r.total for r in rows),
            'customers': db.scalar(select(func.count()).select_from(Customer).where(Customer.company_id == member.company_id)),
            'monthly_sales': [{'month': k, 'taxable': str(v)} for k, v in sorted(monthly.items())]}


@router.get('/audit-logs')
def audits(page: int = Query(1, ge=1), member=Depends(require('settings')), db=Depends(get_db, scope='function')):
    return listing(Audit, db, member, page=page)


@router.get('/invoices/{ident}/pdf')
def pdf(ident: int, member=Depends(tenant), db=Depends(get_db, scope='function')):
    obj = owned(db, Invoice, ident, member.company_id)
    output = BytesIO(); styles = getSampleStyleSheet(); snapshot = obj.snapshot
    story = [Paragraph(escape(snapshot['seller']['name']), styles['Title']),
             Paragraph(escape(snapshot['seller'].get('address') or ''), styles['Normal']),
             Paragraph('GSTIN: ' + escape(snapshot['seller'].get('gstin') or 'Unregistered'), styles['Normal']),
             Spacer(1, 18), Paragraph(f'{obj.status.upper()} — {escape(obj.number or "DRAFT")}', styles['Heading2']),
             Paragraph(f'Invoice date: {obj.invoice_date} | Due: {obj.due_date}', styles['Normal']),
             Paragraph('Bill to: ' + escape(snapshot['customer']['name']), styles['Normal']),
             Paragraph(escape(snapshot['customer'].get('address') or ''), styles['Normal']), Spacer(1, 18)]
    rows = [['Description / HSN', 'Qty', 'Taxable INR', 'CGST', 'SGST', 'IGST', 'Total INR']]
    for row in snapshot['items']:
        rows.append([Paragraph(escape(row['name'] + ' / ' + row['hsn']), styles['Normal']), row['quantity'], row['taxable'], row['cgst'], row['sgst'], row['igst'], row['total']])
    table = Table(rows, repeatRows=1, colWidths=[160, 35, 68, 48, 48, 48, 70])
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8eef6')), ('FONTSIZE',(0,0),(-1,-1),8), ('BOTTOMPADDING',(0,0),(-1,-1),10), ('LINEBELOW',(0,0),(-1,0),1,colors.lightgrey)]))
    story += [table, Spacer(1, 20), Paragraph(f'Taxable: INR {obj.taxable} | Tax: INR {obj.tax} | Total: INR {obj.total}', styles['Heading3']),
              Paragraph(f'Paid: INR {obj.paid} | Outstanding: INR {obj.total-obj.paid}', styles['Normal']),
              Paragraph('Reverse charge: ' + ('Yes; GST payable by recipient' if obj.reverse_charge else 'No'), styles['Normal']),
              Spacer(1, 40), Paragraph('Authorized signature __________________', styles['Normal'])]
    SimpleDocTemplate(output, rightMargin=25, leftMargin=25).build(story)
    output.seek(0)
    return StreamingResponse(output, media_type='application/pdf', headers={'Content-Disposition': f'attachment; filename="invoice-{obj.id}.pdf"'})
