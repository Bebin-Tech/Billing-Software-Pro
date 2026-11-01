from urllib.parse import urlparse, parse_qs
from conftest import account
from app.core.config import settings


def test_password_reset_is_single_use_and_revokes_sessions(client,monkeypatch):
    headers=account(client)
    messages=[]
    monkeypatch.setattr(settings,'smtp_host','smtp.example.com')
    monkeypatch.setattr(settings,'smtp_from','billing@example.com')
    monkeypatch.setattr('app.services.accounts.send_mail',lambda *args:messages.append(args))
    result=client.post('/api/v1/auth/forgot-password',json={'email':'admin@example.com'})
    assert result.status_code==200 and len(messages)==1
    link=messages[0][2].split('\n')[2]
    token=parse_qs(urlparse(link).fragment)['token'][0]
    payload={'token':token,'password':'New-secure-password-123'}
    assert client.post('/api/v1/auth/reset-password',json=payload).status_code==200
    assert client.post('/api/v1/auth/reset-password',json=payload).status_code==400
    assert client.get('/api/v1/companies',headers=headers).status_code==401
    assert client.post('/api/v1/auth/login',json={'email':'admin@example.com','password':'Secure-password-123'}).status_code==401
    assert client.post('/api/v1/auth/login',json={'email':'admin@example.com','password':payload['password']}).status_code==200


def test_email_verification_and_unconfigured_mail(client,monkeypatch):
    headers=account(client)
    assert client.post('/api/v1/auth/request-verification',json={'email':'admin@example.com'}).status_code==503
    messages=[]
    monkeypatch.setattr(settings,'smtp_host','smtp.example.com')
    monkeypatch.setattr(settings,'smtp_from','billing@example.com')
    monkeypatch.setattr(settings,'require_email_verification',True)
    monkeypatch.setattr('app.services.accounts.send_mail',lambda *args:messages.append(args))
    assert client.get('/api/v1/companies',headers=headers).status_code==403
    assert client.post('/api/v1/auth/request-verification',json={'email':'admin@example.com'}).status_code==200
    token=parse_qs(urlparse(messages[0][2].split('\n')[2]).fragment)['token'][0]
    assert client.post('/api/v1/auth/verify-email',json={'token':token}).status_code==200
    assert client.post('/api/v1/auth/verify-email',json={'token':token}).status_code==400
    assert client.get('/api/v1/companies',headers=headers).status_code==200
