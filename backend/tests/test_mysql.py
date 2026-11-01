"""Opt-in tests. TEST_MYSQL_URL must point to a disposable gst_test_* database."""
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.core.database import Base
from app.models import User, Company, Membership, Customer, Invoice, Payment
from app.schemas import PaymentInput
from app.services.billing import issue, record_payment


@pytest.fixture
def mysql():
    url=os.environ.get('TEST_MYSQL_URL')
    if not url: pytest.skip('TEST_MYSQL_URL not configured')
    parsed=make_url(url)
    if not parsed.database.startswith('gst_test_'):
        pytest.fail('Refusing to modify a database without the gst_test_ prefix')
    engine=create_engine(url,pool_size=10,max_overflow=10)
    Base.metadata.create_all(engine)
    factory=sessionmaker(engine,expire_on_commit=False)
    with factory.begin() as db:
        u=User(email='concurrent@example.com',name='Concurrent test',password_hash='not-a-login-hash')
        c=Company(name='Concurrency test',state_code='27');db.add_all([u,c]);db.flush()
        member=Membership(user_id=u.id,company_id=c.id,role='company_admin');db.add(member)
        customer=Customer(company_id=c.id,created_by=u.id,name='Test client',state_code='27');db.add(customer);db.flush()
        ids=[]
        for i in range(12):
            obj=Invoice(company_id=c.id,created_by=u.id,customer_id=customer.id,invoice_date=date(2026,11,1),due_date=date(2026,11,30),supply_state='27',items=[],snapshot={},taxable=Decimal('1000'),tax=Decimal('180'),total=Decimal('1180'))
            db.add(obj);db.flush();ids.append(obj.id)
        db.flush();member_id=member.id
    yield factory,member_id,ids
    # Only the explicitly disposable test schema is cleared.
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_concurrent_numbering(mysql):
    factory,member_id,ids=mysql
    def post(ident):
        with factory.begin() as db:
            member=db.get(Membership,member_id)
            return issue(db,member,ident).number
    with ThreadPoolExecutor(max_workers=8) as pool:
        numbers=list(pool.map(post,ids))
    assert len(set(numbers))==12
    assert sorted(int(n.rsplit('/',1)[1]) for n in numbers)==list(range(1,13))


def test_concurrent_payments_do_not_overallocate(mysql):
    factory,member_id,ids=mysql
    with factory.begin() as db: issue(db,db.get(Membership,member_id),ids[0])
    def pay(i):
        try:
            with factory.begin() as db:
                record_payment(db,db.get(Membership,member_id),PaymentInput(invoice_id=ids[0],amount='800',method='Cash',payment_date=date(2026,11,1),idempotency_key=f'parallel-payment-{i:016d}'))
            return True
        except Exception as exc:
            assert getattr(exc,'status_code',None)==422
            return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(pay,range(2)))
    assert sum(outcomes)==1
    with factory() as db:
        invoice=db.get(Invoice,ids[0]);assert invoice.paid==Decimal('800')
        assert len(list(db.scalars(select(Payment))))==1


def test_database_rejects_cross_company_invoice_customer(mysql):
    factory,member_id,ids=mysql
    with pytest.raises(IntegrityError):
        with factory.begin() as db:
            original=db.get(Invoice,ids[0])
            other=Company(name='Other tenant',state_code='29');db.add(other);db.flush()
            db.add(Invoice(company_id=other.id,created_by=original.created_by,customer_id=original.customer_id,
                invoice_date=date(2026,11,1),due_date=date(2026,11,30),supply_state='29',items=[],snapshot={},
                taxable=Decimal('100'),tax=Decimal('18'),total=Decimal('118')))
