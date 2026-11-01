from datetime import timedelta
from hashlib import sha256
import secrets
import jwt
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
from sqlalchemy import select
from app.core.config import settings
from app.core.database import get_db
from app.models import User, Membership, Session, now

class Passwords:
    @staticmethod
    def hash(value):
        if len(value.encode('utf-8')) > 72:
            raise HTTPException(422, 'Password must be at most 72 UTF-8 bytes')
        return bcrypt.hashpw(value.encode(), bcrypt.gensalt(rounds=12)).decode()

    @staticmethod
    def verify(value, hashed):
        return len(value.encode()) <= 72 and bcrypt.checkpw(value.encode(), hashed.encode())


passwords = Passwords()
bearer = HTTPBearer()
PERMISSIONS = {
    'company_admin': {'read', 'catalog', 'invoice', 'payment', 'settings', 'users'},
    'accountant': {'read', 'catalog', 'invoice', 'payment'},
    'billing_staff': {'read', 'invoice', 'payment', 'customer'},
    'inventory_manager': {'read', 'catalog'},
    'viewer': {'read'},
}


def digest(token):
    return sha256(token.encode()).hexdigest()


def create_session(db, user, family=None):
    token = secrets.token_urlsafe(48)
    record = Session(user_id=user.id, token_hash=digest(token), family=family or secrets.token_hex(24),
                     expires_at=now() + timedelta(days=7))
    db.add(record)
    db.flush()
    return record, token


def access_token(user, session):
    return jwt.encode({'sub': str(user.id), 'sid': session.id, 'exp': now() + timedelta(minutes=15),
                       'iss': 'gst-billing-pro', 'aud': 'gst-billing-api'}, settings.jwt_secret, algorithm='HS256')


def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db=Depends(get_db, scope='function')):
    try:
        claims = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=['HS256'],
                            issuer='gst-billing-pro', audience='gst-billing-api')
        session = db.get(Session, int(claims['sid']))
        user = db.get(User, int(claims['sub']))
        if not user or not session or session.user_id != user.id or session.revoked or session.expires_at < now():
            raise ValueError()
        if settings.require_email_verification and not user.email_verified:
            raise HTTPException(403, 'Verify your email before accessing the workspace')
        return user
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(401, 'Invalid or expired session')


def tenant(user=Depends(current_user), x_company_id: int = Header(), db=Depends(get_db, scope='function')):
    member = db.scalar(select(Membership).where(Membership.user_id == user.id, Membership.company_id == x_company_id))
    if not member:
        raise HTTPException(403, 'Company access denied')
    return member


def require(permission):
    def dependency(member=Depends(tenant)):
        if permission not in PERMISSIONS.get(member.role, set()):
            raise HTTPException(403, 'Permission denied')
        return member
    return dependency
