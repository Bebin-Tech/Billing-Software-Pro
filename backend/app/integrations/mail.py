import ssl
import smtplib
from email.message import EmailMessage
from app.core.config import settings


class MailUnavailable(Exception):
    pass


def send_mail(recipient: str, subject: str, body: str):
    if not settings.smtp_host or not settings.smtp_from:
        raise MailUnavailable('Email delivery is not configured')
    message=EmailMessage()
    message['From']=settings.smtp_from
    message['To']=recipient
    message['Subject']=subject
    message.set_content(body)
    try:
        with smtplib.SMTP(settings.smtp_host,settings.smtp_port,timeout=15) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            if settings.smtp_user:
                server.login(settings.smtp_user,settings.smtp_password)
            server.send_message(message)
    except (smtplib.SMTPException,OSError) as exc:
        raise MailUnavailable('Email provider is unavailable') from exc
