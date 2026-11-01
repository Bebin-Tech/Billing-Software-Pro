"""Normalized invoice lines and tenant-safe financial references.

Revision ID: 0003
"""
from alembic import op
import sqlalchemy as sa

revision='0003'
down_revision='0002'


def columns():
    return [sa.Column('id',sa.Integer(),primary_key=True),sa.Column('created_at',sa.DateTime(),nullable=False),
        sa.Column('updated_at',sa.DateTime(),nullable=False),sa.Column('company_id',sa.Integer(),sa.ForeignKey('companies.id'),nullable=False),
        sa.Column('created_by',sa.Integer(),sa.ForeignKey('users.id'),nullable=False),
        sa.Column('invoice_id',sa.Integer(),nullable=False),sa.Column('gst_rate',sa.Numeric(9,4),nullable=False)]


def amounts():
    return [sa.Column(key,sa.Numeric(18,2),nullable=False) for key in ('taxable','cgst','sgst','igst')]


def upgrade():
    for table,name in [('customers','uq_customers_company_id'),('products','uq_products_company_id'),('sales_invoices','uq_invoices_company_id')]:
        op.create_unique_constraint(name,table,['company_id','id'])
    op.create_foreign_key('fk_invoice_tenant_customer','sales_invoices','customers',['company_id','customer_id'],['company_id','id'])
    op.create_foreign_key('fk_payment_tenant_invoice','payments','sales_invoices',['company_id','invoice_id'],['company_id','id'])
    op.create_table('sales_invoice_items',*columns(),*amounts(),
        sa.Column('product_id',sa.Integer(),nullable=False),sa.Column('description',sa.String(160),nullable=False),
        sa.Column('hsn',sa.String(8),nullable=False),sa.Column('quantity',sa.Numeric(18,4),nullable=False),
        sa.Column('unit_price',sa.Numeric(18,2),nullable=False),sa.Column('total',sa.Numeric(18,2),nullable=False),
        sa.ForeignKeyConstraint(['company_id','invoice_id'],['sales_invoices.company_id','sales_invoices.id'],name='fk_line_tenant_invoice'),
        sa.ForeignKeyConstraint(['company_id','product_id'],['products.company_id','products.id'],name='fk_line_tenant_product'))
    op.create_table('invoice_tax_summaries',*columns(),*amounts(),
        sa.UniqueConstraint('company_id','invoice_id','gst_rate'),
        sa.ForeignKeyConstraint(['company_id','invoice_id'],['sales_invoices.company_id','sales_invoices.id'],name='fk_tax_summary_tenant_invoice'))
    for table in ['sales_invoice_items','invoice_tax_summaries']:
        op.create_index(f'ix_{table}_company_id',table,['company_id'])
        op.create_index(f'ix_{table}_invoice_id',table,['invoice_id'])
    # Backfill historical snapshot rows without consulting mutable catalog prices.
    bind=op.get_bind()
    import json
    from decimal import Decimal
    for invoice in bind.execute(sa.text('SELECT id, company_id, created_by, created_at, updated_at, snapshot FROM sales_invoices')).mappings():
        snapshot=invoice['snapshot']
        if isinstance(snapshot,str): snapshot=json.loads(snapshot)
        buckets={}
        for row in snapshot.get('items',[]):
            base={k:invoice[k] for k in ('company_id','created_by','created_at','updated_at')}
            base.update(invoice_id=invoice['id'],gst_rate=row['gst_rate'])
            values={k:row[k] for k in ('taxable','cgst','sgst','igst','total')}
            table=sa.table('sales_invoice_items',*[sa.column(k) for k in [*base,*values,'product_id','description','hsn','quantity','unit_price']])
            bind.execute(table.insert().values(**base,**values,product_id=row['product_id'],description=row['name'],hsn=row['hsn'],quantity=row['quantity'],unit_price=row['price']))
            bucket=buckets.setdefault(row['gst_rate'],{k:Decimal(0) for k in ('taxable','cgst','sgst','igst')})
            for k in bucket: bucket[k]+=Decimal(row[k])
        for rate,values in buckets.items():
            base={k:invoice[k] for k in ('company_id','created_by','created_at','updated_at')}
            base.update(invoice_id=invoice['id'],gst_rate=rate)
            table=sa.table('invoice_tax_summaries',*[sa.column(k) for k in [*base,*values]])
            bind.execute(table.insert().values(**base,**values))


def downgrade():
    op.drop_table('invoice_tax_summaries');op.drop_table('sales_invoice_items')
    op.drop_constraint('fk_payment_tenant_invoice','payments',type_='foreignkey')
    op.drop_constraint('fk_invoice_tenant_customer','sales_invoices',type_='foreignkey')
    for table,name in [('customers','uq_customers_company_id'),('products','uq_products_company_id'),('sales_invoices','uq_invoices_company_id')]:
        op.drop_constraint(name,table,type_='unique')
