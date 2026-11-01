from datetime import timedelta
import secrets
from fastapi import HTTPException
from sqlalchemy import select, update
from app.core.config import settings
from app.core.security import digest, passwords
from app.integrations.mail import send_mail, MailUnavailable
from app.models import User, PasswordResetToken, EmailVerificationToken, Session, now


def request_action(db, email, verification=False):
    # Fail explicitly before identity lookup if deployment has no mail adapter.
    if not settings.smtp_host or not settings.smtp_from:
        raise HTTPException(503,'Email delivery is not configured; contact your administrator')
    user=db.scalar(select(User).where(User.email==str(email).lower()).with_for_update())
    if not user or (verification and user.email_verified):
        return {'detail':'If the account is eligible, an email has been sent'}
    model=EmailVerificationToken if verification else PasswordResetToken
    db.execute(update(model).where(model.user_id==user.id,model.used==False).values(used=True))
    token=secrets.token_urlsafe(48)
    db.add(model(user_id=user.id,token_hash=digest(token),expires_at=now()+timedelta(minutes=30)))
    fragment='verify' if verification else 'reset'
    link=f'{settings.frontend_url}/?action={fragment}#token={token}'
    try:
        send_mail(user.email,'Verify your GST Billing Pro email' if verification else 'Reset your GST Billing Pro password',
                  f'Use this single-use link within 30 minutes:\n\n{link}\n\nIf you did not request this, ignore this email.')
    except MailUnavailable as exc:
        raise HTTPException(503,str(exc))
    return {'detail':'If the account is eligible, an email has been sent'}


def consume_action(db, token, password=None):
    model=PasswordResetToken if password is not None else EmailVerificationToken
    record=db.scalar(select(model).where(model.token_hash==digest(token)).with_for_update())
    if not record or record.used or record.expires_at<now():
        raise HTTPException(400,'This link has expired or has already been used')
    user=db.scalar(select(User).where(User.id==record.user_id).with_for_update())
    record.used=True
    if password is not None:
        user.password_hash=passwords.hash(password)
        user.failed_attempts=0
        user.locked_until=None
        db.execute(update(Session).where(Session.user_id==user.id).values(revoked=True))
        db.execute(update(PasswordResetToken).where(PasswordResetToken.user_id==user.id).values(used=True))
    else:
        user.email_verified=True
    return {'detail':'Password reset. Sign in again.' if password is not None else 'Email verified. You may now sign in.'}
