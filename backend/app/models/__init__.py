from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy import String, ForeignKey, ForeignKeyConstraint, UniqueConstraint, Numeric, DateTime, Date, JSON, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Record:
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class User(Record, Base):
    __tablename__ = 'users'
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    failed_attempts: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)


class Company(Record, Base):
    __tablename__ = 'companies'
    name: Mapped[str] = mapped_column(String(160))
    state_code: Mapped[str] = mapped_column(String(2))
    gstin: Mapped[str | None] = mapped_column(String(15))
    address: Mapped[str] = mapped_column(String(500), default='')
    invoice_prefix: Mapped[str] = mapped_column(String(12), default='INV')


class ActionToken(Record):
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used: Mapped[bool] = mapped_column(Boolean, default=False)


class PasswordResetToken(ActionToken, Base):
    __tablename__ = 'password_reset_tokens'


class EmailVerificationToken(ActionToken, Base):
    __tablename__ = 'email_verification_tokens'


class Membership(Record, Base):
    __tablename__ = 'user_company_memberships'
    __table_args__ = (UniqueConstraint('user_id', 'company_id'),)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    company_id: Mapped[int] = mapped_column(ForeignKey('companies.id'), index=True)
    role: Mapped[str] = mapped_column(String(30), default='company_admin')


class Session(Record, Base):
    __tablename__ = 'refresh_tokens'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    family: Mapped[str] = mapped_column(String(64), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class TenantRecord(Record):
    company_id: Mapped[int] = mapped_column(ForeignKey('companies.id'), index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))


class Customer(TenantRecord, Base):
    __tablename__ = 'customers'
    __table_args__ = (UniqueConstraint('company_id', 'id', name='uq_customers_company_id'),)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str | None] = mapped_column(String(254))
    gstin: Mapped[str | None] = mapped_column(String(15))
    state_code: Mapped[str] = mapped_column(String(2))
    address: Mapped[str] = mapped_column(String(500), default='')


class Product(TenantRecord, Base):
    __tablename__ = 'products'
    __table_args__ = (UniqueConstraint('company_id', 'sku'), UniqueConstraint('company_id', 'id', name='uq_products_company_id'))
    name: Mapped[str] = mapped_column(String(160))
    sku: Mapped[str] = mapped_column(String(64))
    hsn: Mapped[str] = mapped_column(String(8))
    unit: Mapped[str] = mapped_column(String(20), default='NOS')
    price: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(9, 4))
    is_service: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Invoice(TenantRecord, Base):
    __tablename__ = 'sales_invoices'
    __table_args__ = (UniqueConstraint('company_id', 'number'),
                     UniqueConstraint('company_id', 'id', name='uq_invoices_company_id'),
                     ForeignKeyConstraint(['company_id','customer_id'], ['customers.company_id','customers.id'], name='fk_invoice_tenant_customer'))
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id'))
    number: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default='draft')
    invoice_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    supply_state: Mapped[str] = mapped_column(String(2))
    supply_rule: Mapped[str] = mapped_column(String(40), default='domestic_standard')
    reverse_charge: Mapped[bool] = mapped_column(Boolean, default=False)
    items: Mapped[list] = mapped_column(JSON)
    snapshot: Mapped[dict] = mapped_column(JSON)
    taxable: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    paid: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    cancellation_reason: Mapped[str | None] = mapped_column(String(500))


class Sequence(Base):
    __tablename__ = 'invoice_sequences'
    company_id: Mapped[int] = mapped_column(ForeignKey('companies.id'), primary_key=True)
    financial_year: Mapped[str] = mapped_column(String(9), primary_key=True)
    value: Mapped[int] = mapped_column(Integer, default=0)


class Payment(TenantRecord, Base):
    __tablename__ = 'payments'
    invoice_id: Mapped[int] = mapped_column(ForeignKey('sales_invoices.id'))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    method: Mapped[str] = mapped_column(String(30))
    payment_date: Mapped[date] = mapped_column(Date)
    reference: Mapped[str] = mapped_column(String(100), default='')
    idempotency_key: Mapped[str] = mapped_column(String(64))
    __table_args__ = (UniqueConstraint('company_id', 'idempotency_key'),
                     ForeignKeyConstraint(['company_id','invoice_id'], ['sales_invoices.company_id','sales_invoices.id'], name='fk_payment_tenant_invoice'))


class InvoiceLine(TenantRecord, Base):
    __tablename__ = 'sales_invoice_items'
    __table_args__ = (
        ForeignKeyConstraint(['company_id','invoice_id'],['sales_invoices.company_id','sales_invoices.id'],name='fk_line_tenant_invoice'),
        ForeignKeyConstraint(['company_id','product_id'],['products.company_id','products.id'],name='fk_line_tenant_product'),
    )
    invoice_id: Mapped[int] = mapped_column(Integer, index=True)
    product_id: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String(160))
    hsn: Mapped[str] = mapped_column(String(8))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18,4))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18,2))
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(9,4))
    taxable: Mapped[Decimal] = mapped_column(Numeric(18,2))
    cgst: Mapped[Decimal] = mapped_column(Numeric(18,2))
    sgst: Mapped[Decimal] = mapped_column(Numeric(18,2))
    igst: Mapped[Decimal] = mapped_column(Numeric(18,2))
    total: Mapped[Decimal] = mapped_column(Numeric(18,2))


class TaxSummary(TenantRecord, Base):
    __tablename__ = 'invoice_tax_summaries'
    __table_args__ = (UniqueConstraint('company_id','invoice_id','gst_rate'),
        ForeignKeyConstraint(['company_id','invoice_id'],['sales_invoices.company_id','sales_invoices.id'],name='fk_tax_summary_tenant_invoice'))
    invoice_id: Mapped[int] = mapped_column(Integer, index=True)
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(9,4))
    taxable: Mapped[Decimal] = mapped_column(Numeric(18,2))
    cgst: Mapped[Decimal] = mapped_column(Numeric(18,2))
    sgst: Mapped[Decimal] = mapped_column(Numeric(18,2))
    igst: Mapped[Decimal] = mapped_column(Numeric(18,2))


class Audit(TenantRecord, Base):
    __tablename__ = 'audit_logs'
    action: Mapped[str] = mapped_column(String(60))
    entity: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[int] = mapped_column(Integer)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
