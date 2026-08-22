from threading import Thread
from flask import current_app
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


def send_school_admin_consent_email(admin, token):
    from consent_service import build_consent_link

    if admin is None or token is None:
        return False

    link = build_consent_link(token)

    html = f"""
    <html>
    <body style="margin:0;padding:40px 20px;background:#f4f7fb;font-family:Arial,Helvetica,sans-serif;">
    <div style="max-width:700px;margin:auto;background:#ffffff;border-radius:14px;overflow:hidden;box-shadow:0 8px 30px rgba(0,0,0,.08);">
        <div style="background:#2563eb;padding:30px;color:white;">
            <h1 style="margin:0;font-size:24px;">School Administrator Consent</h1>
            <p style="margin:8px 0 0;opacity:.9;">Survitec 3D School Platform</p>
        </div>
        <div style="padding:35px;">
            <p>Dear <strong>{admin.username}</strong>,</p>
            <p>You have been registered as a School Administrator on the Survitec 3D School Platform.</p>
            <p>Before accessing the administration system, you are required to review and accept the current School Administrator Consent.</p>
            <div style="background:#eff6ff;border-left:4px solid #2563eb;padding:18px;margin:25px 0;border-radius:6px;">
                <strong>Action required</strong>
                <p style="margin:8px 0 0;color:#444;">Please review the consent document and indicate whether you agree.</p>
            </div>
            <div style="text-align:center;margin:35px 0;">
                <a href="{link}" style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;padding:15px 30px;border-radius:8px;font-weight:bold;">Review & Give Consent</a>
            </div>
            <p style="color:#666;font-size:14px;">This secure consent link expires after <strong>48 hours</strong>.</p>
            <hr style="border:none;border-top:1px solid #eee;margin:30px 0;">
            <p style="color:#777;font-size:13px;">If you did not expect this invitation, please contact your system administrator.</p>
            <p>Regards,<br><strong>Survitec 3D Team</strong></p>
        </div>
    </div>
    </body>
    </html>
    """

    send_email_safe(admin.email, "Administrator Consent Required", html=html)
    token.status = "Sent"
    token.sent_at = datetime.now(kenya_tz)
    from models import db
    db.session.commit()
    return True


def send_student_consent_email(student, token):
    from consent_service import build_consent_link

    if student is None or token is None:
        return False

    link = build_consent_link(token)

    html = f"""
    <html>
    <body style="margin:0;padding:40px 20px;background:#f4f7fb;font-family:Arial,Helvetica,sans-serif;">
    <div style="max-width:700px;margin:auto;background:#ffffff;border-radius:14px;overflow:hidden;box-shadow:0 8px 30px rgba(0,0,0,.08);">
        <div style="background:#7c3aed;padding:30px;color:white;">
            <h1 style="margin:0;font-size:24px;">Student Consent Required</h1>
            <p style="margin:8px 0 0;opacity:.9;">Survitec 3D School Platform</p>
        </div>
        <div style="padding:35px;">
            <p>Dear <strong>{student.fullname}</strong>,</p>
            <p>You have been registered as a student on the Survitec 3D School Platform.</p>
            <p>Before accessing the platform, you are required to review and accept the current Student Consent.</p>
            <div style="background:#f5f3ff;border-left:4px solid #7c3aed;padding:18px;margin:25px 0;border-radius:6px;">
                <strong>Action required</strong>
                <p style="margin:8px 0 0;color:#444;">Please review the consent document and indicate whether you agree.</p>
            </div>
            <div style="text-align:center;margin:35px 0;">
                <a href="{link}" style="display:inline-block;background:#7c3aed;color:#ffffff;text-decoration:none;padding:15px 30px;border-radius:8px;font-weight:bold;">Review & Give Consent</a>
            </div>
            <p style="color:#666;font-size:14px;">This secure consent link expires after <strong>48 hours</strong>.</p>
            <hr style="border:none;border-top:1px solid #eee;margin:30px 0;">
            <p style="color:#777;font-size:13px;">If you did not expect this invitation, please contact your school administrator.</p>
            <p>Regards,<br><strong>Survitec 3D Team</strong></p>
        </div>
    </div>
    </body>
    </html>
    """

    send_email_safe(token.recipient_email, "Consent Required", html=html)
    token.status = "Sent"
    token.sent_at = datetime.now(kenya_tz)
    from models import db
    db.session.commit()
    return True
