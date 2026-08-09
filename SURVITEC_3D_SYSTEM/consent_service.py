import uuid

from datetime import datetime, timedelta, date

import pytz

from flask import url_for
from flask_mail import Message

from mail_config import mail

from models import (
    db,
    Consent,
    ConsentToken,
    ConsentLog,
    Student
)


# ============================================================
# TIMEZONE
# ============================================================

kenya_tz = pytz.timezone(
    "Africa/Nairobi"
)


# ============================================================
# AGE CALCULATOR
# ============================================================

def calculate_age(value):
    """
    Accepts:

    - Student object
    - datetime.date
    - datetime.datetime
    - 'YYYY-MM-DD' string

    Returns:
        Integer age in completed years.
    """

    # --------------------------------------------------------
    # STUDENT OBJECT
    # --------------------------------------------------------

    if hasattr(value, "date_of_birth"):

        value = value.date_of_birth


    # --------------------------------------------------------
    # STRING DATE
    # --------------------------------------------------------

    if isinstance(value, str):

        value = datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()


    # --------------------------------------------------------
    # DATETIME
    # --------------------------------------------------------

    elif isinstance(value, datetime):

        value = value.date()


    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    elif not isinstance(value, date):

        raise TypeError(
            f"Unsupported type: {type(value)}"
        )


    # --------------------------------------------------------
    # CURRENT KENYAN DATE
    # --------------------------------------------------------

    today = datetime.now(
        kenya_tz
    ).date()


    # --------------------------------------------------------
    # CALCULATE AGE
    # --------------------------------------------------------

    years = (
        today.year
        - value.year
    )


    if (
        today.month,
        today.day
    ) < (
        value.month,
        value.day
    ):

        years -= 1


    return years


# ============================================================
# STUDENT CONSENT TARGET
# ============================================================

def get_student_target(student):

    age = calculate_age(
        student.date_of_birth
    )


    if age >= 18:

        return "Student"


    return "Parent"


# ============================================================
# STUDENT CATEGORY
# ============================================================

def determine_student_category(student):

    age = calculate_age(
        student.date_of_birth
    )


    if age < 18:

        return "Minor"


    return "Adult"


# ============================================================
# PARENT CONSENT REQUIRED?
# ============================================================

def requires_parent(student):

    return (
        calculate_age(
            student.date_of_birth
        ) < 18
    )


# ============================================================
# GET ACTIVE CONSENT
# ============================================================

def get_active_consent(target):

    """
    target must be exactly one of:

        Student
        Parent
        SchoolAdmin
    """

    if not target:

        return None


    consent = (
        Consent.query
        .filter(
            Consent.target == target,
            Consent.active.is_(True)
        )
        .order_by(
            Consent.effective_from.desc(),
            Consent.id.desc()
        )
        .first()
    )


    return consent


# ============================================================
# CHECK STUDENT CONSENT
# ============================================================

def has_valid_student_consent(student):

    """
    Checks whether the student has agreed to the
    CURRENT active consent applicable to them.

    Returns:

        (True, consent)
        (False, consent)
        (False, None)
    """

    target = get_student_target(
        student
    )


    consent = get_active_consent(
        target
    )


    # --------------------------------------------------------
    # NO ACTIVE CONSENT
    # --------------------------------------------------------

    if consent is None:

        return False, None


    # --------------------------------------------------------
    # CHECK LOG
    # --------------------------------------------------------

    log = (
        ConsentLog.query
        .filter_by(
            consent_id=consent.id,
            user_type="Student",
            user_id=student.id,
            agreed=True,
            withdrawn=False
        )
        .first()
    )


    if log:

        return True, consent


    return False, consent


# ============================================================
# CHECK SCHOOL ADMIN CONSENT
# ============================================================

def has_valid_school_admin_consent(admin):

    """
    Checks whether the School Administrator has accepted
    the CURRENT active SchoolAdmin consent.
    """

    consent = get_active_consent(
        "SchoolAdmin"
    )


    # --------------------------------------------------------
    # NO ACTIVE SCHOOL ADMIN CONSENT
    # --------------------------------------------------------

    if consent is None:

        return False, None


    # --------------------------------------------------------
    # FIND AGREEMENT
    # --------------------------------------------------------

    log = (
        ConsentLog.query
        .filter_by(
            consent_id=consent.id,
            user_type="SchoolAdmin",
            user_id=admin.id,
            agreed=True,
            withdrawn=False
        )
        .first()
    )


    if log:

        return True, consent


    return False, consent


# ============================================================
# GENERATE TOKEN
# ============================================================

def generate_token():

    return str(
        uuid.uuid4()
    )


# ============================================================
# CREATE CONSENT TOKEN
# ============================================================

def create_consent_token(
    consent,
    user,
    user_type,
    email
):

    # --------------------------------------------------------
    # VALIDATE CONSENT
    # --------------------------------------------------------

    if consent is None:

        print(
            "ERROR: Cannot create consent token."
        )

        print(
            f"User Type: {user_type}"
        )

        print(
            "Consent: None"
        )

        return None


    # --------------------------------------------------------
    # VALIDATE USER
    # --------------------------------------------------------

    if user is None:

        print(
            "ERROR: Cannot create consent token."
        )

        print(
            f"User Type: {user_type}"
        )

        print(
            "User: None"
        )

        return None


    # --------------------------------------------------------
    # VALIDATE EMAIL
    # --------------------------------------------------------

    if not email:

        print(
            f"ERROR: No email available for {user_type}."
        )

        return None


    # --------------------------------------------------------
    # CREATE TOKEN
    # --------------------------------------------------------

    token = ConsentToken(

        token=generate_token(),

        consent_id=consent.id,

        user_type=user_type,

        user_id=str(
            user.id
        ),

        recipient_email=email,

        status="Created",

        expires_at=(
            datetime.now(
                kenya_tz
            )
            + timedelta(hours=48)
        )
    )


    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    db.session.add(
        token
    )

    db.session.commit()


    print(
        "CONSENT TOKEN CREATED"
    )

    print(
        f"User Type : {user_type}"
    )

    print(
        f"User ID   : {user.id}"
    )

    print(
        f"Consent   : {consent.id}"
    )

    print(
        f"Token     : {token.token}"
    )


    return token


# ============================================================
# BUILD CONSENT LINK
# ============================================================

def build_consent_link(token):

    if token is None:

        print(
            "ERROR: build_consent_link() received None."
        )

        return None


    if not getattr(token, "token", None):

        print(
            "ERROR: ConsentToken has no token value."
        )

        return None


    return url_for(

        "view_consent",

        token=token.token,

        _external=True

    )


# ============================================================
# GENERATE STUDENT CONSENT
# ============================================================

def generate_student_consent(student):

    target = get_student_target(
        student
    )


    print(
        f"Student Category : {target}"
    )


    consent = get_active_consent(
        target
    )


    print(
        f"Consent Found : {consent}"
    )


    # --------------------------------------------------------
    # NO CONSENT
    # --------------------------------------------------------

    if consent is None:

        print(
            f"No ACTIVE consent found for target '{target}'"
        )

        return None


    # --------------------------------------------------------
    # EMAIL
    # --------------------------------------------------------

    if target == "Parent":

        email = student.parent_email

    else:

        email = student.email


    print(
        f"Email : {email}"
    )


    # --------------------------------------------------------
    # CREATE TOKEN
    # --------------------------------------------------------

    token = create_consent_token(

        consent=consent,

        user=student,

        user_type="Student",

        email=email

    )


    print(
        f"Token : {token}"
    )


    return token


# ============================================================
# GENERATE SCHOOL ADMIN CONSENT
# ============================================================

def generate_school_admin_consent(admin):

    """
    Generate a consent token for a School Administrator.

    Returns:
        ConsentToken
        None if the token cannot be created.
    """

    if admin is None:

        print("ERROR: School Admin is None.")

        return None


    print(
        f"Generating consent for School Admin: {admin.id}"
    )


    # ========================================================
    # FIND ACTIVE SCHOOL ADMIN CONSENT
    # ========================================================

    consent = (
        Consent.query
        .filter(
            Consent.target == "SchoolAdmin",
            Consent.active.is_(True)
        )
        .order_by(
            Consent.effective_from.desc(),
            Consent.id.desc()
        )
        .first()
    )


    print(
        f"SchoolAdmin consent found: {consent}"
    )


    # ========================================================
    # NO CONSENT
    # ========================================================

    if consent is None:

        print(
            "ERROR: No active SchoolAdmin consent exists."
        )

        print(
            "Check your Consent table."
        )

        print(
            "Required target: SchoolAdmin"
        )

        print(
            "Required active: True"
        )

        return None


    # ========================================================
    # ADMIN EMAIL
    # ========================================================

    email = getattr(
        admin,
        "email",
        None
    )


    if not email:

        print(
            "ERROR: School Admin has no email."
        )

        return None


    # ========================================================
    # CREATE TOKEN
    # ========================================================

    token = create_consent_token(

        consent=consent,

        user=admin,

        user_type="SchoolAdmin",

        email=email

    )


    # ========================================================
    # VERIFY TOKEN
    # ========================================================

    if token is None:

        print(
            "ERROR: create_consent_token() returned None."
        )

        return None


    print(
        "School Admin consent token created:"
    )

    print(
        f"Token: {token.token}"
    )


    return token

# ============================================================
# SEND PARENT CONSENT EMAIL
# ============================================================

def send_parent_consent_email(
    student,
    token
):

    if token is None:

        print(
            "Cannot send parent consent email: token is None."
        )

        return False


    consent_link = build_consent_link(
        token
    )


    subject = (
        "Parental Consent Required"
    )


    html = f"""
    <html>

    <body
        style="
            font-family:Arial,sans-serif;
            background:#f5f7fa;
            padding:30px;
        "
    >

        <div
            style="
                max-width:700px;
                margin:auto;
                background:white;
                padding:40px;
                border-radius:10px;
                box-shadow:0 0 15px rgba(0,0,0,.08);
            "
        >

            <h2 style="color:#2563eb;">
                Parent/Guardian Consent Required
            </h2>

            <p>
                Dear Parent/Guardian,
            </p>

            <p>

                Your child

                <strong>
                    {student.fullname}
                </strong>

                has been registered on the

                <strong>
                    Survitec 3D School Platform
                </strong>.

            </p>

            <p>

                Before your child can access the platform,
                we require your consent to collect and process
                their personal information.

            </p>

            <p
                style="
                    margin:35px 0;
                    text-align:center;
                "
            >

                <a
                    href="{consent_link}"
                    style="
                        background:#2563eb;
                        color:white;
                        text-decoration:none;
                        padding:15px 35px;
                        border-radius:8px;
                        font-weight:bold;
                    "
                >

                    Review & Give Consent

                </a>

            </p>

            <p>

                This consent link expires after

                <strong>
                    48 hours
                </strong>.

            </p>

            <hr>

            <p
                style="
                    font-size:13px;
                    color:#666;
                "
            >

                If you did not expect this email,
                you may safely ignore it.

            </p>

            <p>

                Regards,<br>

                <strong>
                    Survitec 3D Team
                </strong>

            </p>

        </div>

    </body>

    </html>
    """


    msg = Message(

        subject=subject,

        recipients=[
            student.parent_email
        ]

    )


    msg.html = html


    mail.send(
        msg
    )


    return True


# ============================================================
# SEND SCHOOL ADMIN CONSENT EMAIL
# ============================================================

def send_school_admin_consent_email(admin, token):

    if admin is None:

        print(
            "ERROR: School Admin is None."
        )

        return False


    if token is None:

        print(
            "ERROR: School Admin consent token is None."
        )

        return False


    consent_link = build_consent_link(
        token
    )


    if consent_link is None:

        print(
            "ERROR: Could not build School Admin consent link."
        )

        return False


    subject = (
        "School Administrator Consent Required"
    )


    html = f"""
    <html>

    <body
        style="
            margin:0;
            padding:40px 20px;
            background:#f4f7fb;
            font-family:Arial,Helvetica,sans-serif;
        "
    >

        <div
            style="
                max-width:700px;
                margin:auto;
                background:#ffffff;
                border-radius:14px;
                overflow:hidden;
                box-shadow:0 8px 30px rgba(0,0,0,.08);
            "
        >

            <div
                style="
                    background:#2563eb;
                    padding:30px;
                    color:white;
                "
            >

                <h1
                    style="
                        margin:0;
                        font-size:24px;
                    "
                >
                    School Administrator Consent
                </h1>

                <p
                    style="
                        margin:8px 0 0;
                        opacity:.9;
                    "
                >
                    Survitec 3D School Platform
                </p>

            </div>


            <div
                style="
                    padding:35px;
                "
            >

                <p>
                    Dear
                    <strong>
                        {admin.username}
                    </strong>,
                </p>


                <p>

                    You have been registered as a
                    School Administrator on the
                    Survitec 3D School Platform.

                </p>


                <p>

                    Before accessing the administration
                    system, you are required to review
                    and accept the current School
                    Administrator Consent.

                </p>


                <div
                    style="
                        background:#eff6ff;
                        border-left:4px solid #2563eb;
                        padding:18px;
                        margin:25px 0;
                        border-radius:6px;
                    "
                >

                    <strong>
                        Action required
                    </strong>

                    <p
                        style="
                            margin:8px 0 0;
                            color:#444;
                        "
                    >

                        Please review the consent document
                        and indicate whether you agree.

                    </p>

                </div>


                <div
                    style="
                        text-align:center;
                        margin:35px 0;
                    "
                >

                    <a
                        href="{consent_link}"
                        style="
                            display:inline-block;
                            background:#2563eb;
                            color:#ffffff;
                            text-decoration:none;
                            padding:15px 30px;
                            border-radius:8px;
                            font-weight:bold;
                        "
                    >

                        Review & Give Consent

                    </a>

                </div>


                <p
                    style="
                        color:#666;
                        font-size:14px;
                    "
                >

                    This secure consent link expires
                    after <strong>48 hours</strong>.

                </p>


                <hr
                    style="
                        border:none;
                        border-top:1px solid #eee;
                        margin:30px 0;
                    "
                >


                <p
                    style="
                        color:#777;
                        font-size:13px;
                    "
                >

                    If you did not expect this invitation,
                    please contact your system administrator.

                </p>


                <p>

                    Regards,<br>

                    <strong>
                        Survitec 3D Team
                    </strong>

                </p>

            </div>

        </div>

    </body>

    </html>
    """


    msg = Message(

        subject=subject,

        recipients=[
            admin.email
        ]

    )


    msg.html = html


    mail.send(
        msg
    )


    print(
        "School Admin consent email sent successfully."
    )


    return True