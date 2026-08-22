from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from mail_config import mail
from datetime import datetime
import pytz
import traceback

kenya_tz = pytz.timezone("Africa/Nairobi")


def send_email_safe(recipient, subject, body=None, html=None):
    """
    Sends email in a background thread with full error handling.
    Never crashes the request — logs errors instead.
    """
    app = current_app._get_current_object()

    def _worker():
        with app.app_context():
            try:
                msg = Message(subject=subject, recipients=[recipient])
                if html:
                    msg.html = html
                elif body:
                    msg.body = body
                else:
                    msg.body = ""
                mail.send(msg)
                app.logger.info(f"Email sent to {recipient}: {subject}")
            except Exception as e:
                app.logger.error(f"FAILED to send email to {recipient}: {e}")
                app.logger.error(traceback.format_exc())

    Thread(target=_worker, daemon=True).start()


def send_student_consent_email(student, token):
    from consent_service import build_consent_link
    link = build_consent_link(token)
    html = render_template(
        "student_consent.html",
        student=student,
        consent_link=link,
        expires_at=token.expires_at
    )
    send_email_safe(token.recipient_email, "Consent Required", html=html)
    token.status = "Sent"
    token.sent_at = datetime.now(kenya_tz)
    from models import db
    db.session.commit()


def send_school_admin_consent_email(admin, token):
    from consent_service import build_consent_link
    link = build_consent_link(token)
    html = render_template(
        "admin_consent.html",
        admin=admin,
        consent_link=link,
        expires_at=token.expires_at
    )
    send_email_safe(token.recipient_email, "Administrator Consent", html=html)
    token.status = "Sent"
    token.sent_at = datetime.now(kenya_tz)
    from models import db
    db.session.commit()
