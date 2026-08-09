from flask_mail import Message
from flask import current_app, render_template
from mail_config import mail
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, date
from decimal import Decimal
from datetime import datetime
import pytz
import uuid


kenya_tz = pytz.timezone("Africa/Nairobi")
db = SQLAlchemy()
def send_email(
    recipient,
    subject,
    html
):

    msg = Message(

        subject=subject,

        recipients=[recipient],

        html=html

    )

    mail.send(msg)

from consent_service import build_consent_link


def send_student_consent_email(

    student,

    token

):

    link = build_consent_link(token)

    html = render_template(

        "student_consent.html",

        student=student,

        consent_link=link,

        expires_at=token.expires_at

    )

    send_email(

        token.recipient_email,

        "Consent Required",

        html

    )

    token.status = "Sent"

    token.sent_at = datetime.now(kenya_tz)

    db.session.commit()

def send_school_admin_consent_email(

    admin,

    token

):

    link = build_consent_link(token)

    html = render_template(

        "admin_consent.html",

        admin=admin,

        consent_link=link,

        expires_at=token.expires_at

    )

    send_email(

        token.recipient_email,

        "Administrator Consent",

        html

    )

    token.status = "Sent"

    token.sent_at = datetime.now(kenya_tz)

    db.session.commit()

