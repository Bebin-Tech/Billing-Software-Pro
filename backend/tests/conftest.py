import os
os.environ['DATABASE_URL'] = 'sqlite://'
os.environ['JWT_SECRET'] = 'test-only-secret-must-never-be-used-in-production-12345'
os.environ['REGISTRATION_ENABLED'] = 'true'
os.environ['SECURE_COOKIES'] = 'false'
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.core.database import Base, get_db
from app.main import app, attempts


@pytest.fixture
def client():
    engine = create_engine('sqlite://', connect_args={'check_same_thread':False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    def override():
        with factory() as db:
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise
    app.dependency_overrides[get_db] = override
    attempts.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


def account(client, email='admin@example.com'):
    r=client.post('/api/v1/auth/register', json={'email':email,'password':'Secure-password-123','name':'Business Owner','company_name':'Test Company','state_code':'27'})
    assert r.status_code == 201, r.text
    token=r.json()['access_token']
    headers={'Authorization':f'Bearer {token}'}
    company=client.get('/api/v1/companies',headers=headers).json()[0]
    return {**headers,'X-Company-ID':str(company['id'])}
