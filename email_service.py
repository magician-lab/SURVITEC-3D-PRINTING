from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from mail_config import mail
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, date
from decimal import Decimal
import pytz
import uuid

from consent_service import build_consent_link

kenya_tz = pytz.timezone("Africa/Nairobi")

def _send_async_email(app, db, token_id, recipient, subject, html):
    """
    Background worker function to handle synchronous SMTP operations
    safely inside an application context.
    """
    with app.app_context():
        try:
            # Attempt to send the email via SMTP
            msg = Message(subject=subject, recipients=[recipient], html=html)
            mail.send(msg)
            
            # Update token status inside the background thread's context
            # We re-query or update based on the passed token ID if necessary,
            # or handle database state carefully.
            if token_id:
                # Import your model locally to avoid circular imports if needed
                # from models import ConsentToken 
                # token = db.session.get(ConsentToken, token_id)
                # if token:
                #     token.status = "Sent"
                #     token.sent_at = datetime.now(kenya_tz)
                #     db.session.commit()
                pass
        except Exception as e:
            app.logger.error(f"Background SMTP email failed to {recipient}: {e}")

def send_email(recipient, subject, html):
    """
    Spawns a background thread for sending mail to prevent Gunicorn 
    worker blocking / timeouts on cloud hosting like Render.
    """
    app = current_app._get_current_object()
    db_instance = current_app.extensions.get('sqlalchemy') # or pass your db instance
    
    # We trigger the thread so the HTTP request completes immediately
    Thread(
        target=_send_async_email,
        args=(app, db_instance, None, recipient, subject, html)
    ).start()

def send_student_consent_email(student, token):
    link = build_consent_link(token)
    html = render_template(
        "student_consent.html",
        student=student,
        consent_link=link,
        expires_at=token.expires_at
    )
    
    # Fire off the async email dispatch
    send_email(
        token.recipient_email,
        "Consent Required",
        html
    )

    # Update state immediately for the HTTP transaction
    token.status = "Sent"
    token.sent_at = datetime.now(kenya_tz)
    db.session.commit()

def send_school_admin_consent_email(admin, token):
    link = build_consent_link(token)
    html = render_template(
        "admin_consent.html",
        admin=admin,
        consent_link=link,
        expires_at=token.expires_at
    )
    
    # Fire off the async email dispatch
    send_email(
        token.recipient_email,
        "Administrator Consent",
        html
    )

    # Update state immediately for the HTTP transaction
    token.status = "Sent"
    token.sent_at = datetime.now(kenya_tz)
    db.session.commit()
