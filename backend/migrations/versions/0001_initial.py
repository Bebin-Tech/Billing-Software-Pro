"""Initial tenant, catalog and service billing schema.

Revision ID: 0001
"""
from alembic import op
from sqlalchemy import Column, Integer, String, DateTime, Date, Numeric, Boolean, JSON, ForeignKey, UniqueConstraint

revision = '0001'
down_revision = None


def base():
    return [Column('id', Integer, primary_key=True), Column('created_at', DateTime, nullable=False), Column('updated_at', DateTime, nullable=False)]


def tenant():
    return base() + [Column('company_id', Integer, ForeignKey('companies.id'), nullable=False), Column('created_by', Integer, ForeignKey('users.id'), nullable=False)]


def upgrade():
    op.create_table('users', *base(), Column('email', String(254), nullable=False, unique=True), Column('name', String(120), nullable=False), Column('password_hash', String(255), nullable=False), Column('failed_attempts', Integer, nullable=False), Column('locked_until', DateTime))
    op.create_table('companies', *base(), Column('name', String(160), nullable=False), Column('state_code', String(2), nullable=False), Column('gstin', String(15)), Column('address', String(500), nullable=False), Column('invoice_prefix', String(12), nullable=False))
    op.create_table('user_company_memberships', *base(), Column('user_id', Integer, ForeignKey('users.id'), nullable=False), Column('company_id', Integer, ForeignKey('companies.id'), nullable=False), Column('role', String(30), nullable=False), UniqueConstraint('user_id','company_id'))
    op.create_table('refresh_tokens', *base(), Column('user_id', Integer, ForeignKey('users.id'), nullable=False), Column('token_hash', String(64), unique=True, nullable=False), Column('family', String(64), nullable=False), Column('expires_at', DateTime, nullable=False), Column('revoked', Boolean, nullable=False))
    op.create_table('customers', *tenant(), Column('name', String(160), nullable=False), Column('email', String(254)), Column('gstin', String(15)), Column('state_code', String(2), nullable=False), Column('address', String(500), nullable=False))
    op.create_table('products', *tenant(), Column('name', String(160), nullable=False), Column('sku', String(64), nullable=False), Column('hsn', String(8), nullable=False), Column('unit', String(20), nullable=False), Column('price', Numeric(18,2), nullable=False), Column('gst_rate', Numeric(9,4), nullable=False), Column('is_service', Boolean, nullable=False), Column('active', Boolean, nullable=False), UniqueConstraint('company_id','sku'))
    op.create_table('sales_invoices', *tenant(), Column('customer_id', Integer, ForeignKey('customers.id'), nullable=False), Column('number', String(40)), Column('status', String(20), nullable=False), Column('invoice_date', Date, nullable=False), Column('due_date', Date, nullable=False), Column('supply_state', String(2), nullable=False), Column('supply_rule', String(40), nullable=False), Column('reverse_charge', Boolean, nullable=False), Column('items', JSON, nullable=False), Column('snapshot', JSON, nullable=False), Column('taxable', Numeric(18,2), nullable=False), Column('tax', Numeric(18,2), nullable=False), Column('total', Numeric(18,2), nullable=False), Column('paid', Numeric(18,2), nullable=False), Column('cancellation_reason', String(500)), UniqueConstraint('company_id','number'))
    op.create_table('invoice_sequences', Column('company_id', Integer, ForeignKey('companies.id'), primary_key=True), Column('financial_year', String(9), primary_key=True), Column('value', Integer, nullable=False))
    op.create_table('payments', *tenant(), Column('invoice_id', Integer, ForeignKey('sales_invoices.id'), nullable=False), Column('amount', Numeric(18,2), nullable=False), Column('method', String(30), nullable=False), Column('payment_date', Date, nullable=False), Column('reference', String(100), nullable=False), Column('idempotency_key', String(64), nullable=False), UniqueConstraint('company_id','idempotency_key'))
    op.create_table('audit_logs', *tenant(), Column('action', String(60), nullable=False), Column('entity', String(60), nullable=False), Column('entity_id', Integer, nullable=False), Column('detail', JSON, nullable=False))
    for table in ['user_company_memberships','customers','products','sales_invoices','payments','audit_logs']:
        op.create_index(f'ix_{table}_company_id', table, ['company_id'])
    op.create_index('ix_refresh_tokens_user_id','refresh_tokens',['user_id'])
    op.create_index('ix_refresh_tokens_family','refresh_tokens',['family'])


def downgrade():
    for table in ['audit_logs','payments','invoice_sequences','sales_invoices','products','customers','refresh_tokens','user_company_memberships','companies','users']:
        op.drop_table(table)
