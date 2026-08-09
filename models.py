
from flask_sqlalchemy import SQLAlchemy

from datetime import (
    datetime,
    timedelta,
    date
)

import pytz
import uuid


# ==========================================================
# DATABASE
# ==========================================================

db = SQLAlchemy()


# ==========================================================
# KENYA TIMEZONE
# ==========================================================

kenya_tz = pytz.timezone("Africa/Nairobi")


# ==========================================================
# UUID HELPER
# ==========================================================

def generate_uuid():
    return str(uuid.uuid4())


# ==========================================================
# SCHOOL
# ==========================================================

class School(db.Model):

    __tablename__ = "schools"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=generate_uuid
    )

    school_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    name = db.Column(
        db.String(255),
        nullable=False
    )

    email = db.Column(
        db.String(255)
    )

    phone = db.Column(
        db.String(20)
    )

    active = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ==========================================================
# STUDENT
# ==========================================================

class Student(db.Model):

    __tablename__ = "students"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=generate_uuid
    )

    school_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "schools.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    admission_no = db.Column(
        db.String(50),
        nullable=False
    )

    fullname = db.Column(
        db.String(255),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        nullable=False
    )

    parent_name = db.Column(
        db.String(255)
    )

    parent_email = db.Column(
        db.String(150)
    )

    parent_phone = db.Column(
        db.String(30)
    )

    date_of_birth = db.Column(
        db.Date,
        nullable=False
    )

    grade = db.Column(
        db.String(30),
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    active = db.Column(
        db.Boolean,
        default=True
    )

    consent_completed = db.Column(
        db.Boolean,
        default=False
    )

    consent_completed_at = db.Column(
        db.DateTime
    )

    last_consent_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "consents.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(kenya_tz)
    )

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(kenya_tz),
        onupdate=lambda: datetime.now(kenya_tz)
    )

    school = db.relationship(
        "School",
        backref="students"
    )

    consent = db.relationship(
        "Consent",
        foreign_keys=[last_consent_id]
    )

    __table_args__ = (
        db.UniqueConstraint(
            "school_id",
            "admission_no",
            name="unique_student_school"
        ),
    )


# ==========================================================
# SYSTEM ADMIN
# ==========================================================

class SystemAdmin(db.Model):

    __tablename__ = "system_admins"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=generate_uuid
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    otp_code = db.Column(
        db.String(6)
    )

    otp_expiration = db.Column(
        db.DateTime
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ==========================================================
# SCHOOL ADMIN
# ==========================================================

class SchoolAdmin(db.Model):

    __tablename__ = "school_admins"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=generate_uuid
    )

    school_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "schools.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    fullname = db.Column(
        db.String(255),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    active = db.Column(
        db.Boolean,
        default=True
    )

    consent_completed = db.Column(
        db.Boolean,
        default=False
    )

    consent_completed_at = db.Column(
        db.DateTime
    )

    last_consent_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "consents.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(kenya_tz)
    )

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(kenya_tz),
        onupdate=lambda: datetime.now(kenya_tz)
    )

    school = db.relationship(
        "School",
        backref="school_admins"
    )

    consent = db.relationship(
        "Consent",
        foreign_keys=[last_consent_id]
    )


# ==========================================================
# MATERIAL
# ==========================================================

class Material(db.Model):

    __tablename__ = "materials"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=generate_uuid
    )

    title = db.Column(
        db.String(255),
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    subject = db.Column(
        db.String(100),
        nullable=False
    )

    grade = db.Column(
        db.String(30),
        nullable=False
    )

    file_name = db.Column(
        db.String(255),
        nullable=False
    )

    file_path = db.Column(
        db.String(500),
        nullable=False
    )

    active = db.Column(
        db.Boolean,
        default=True
    )

    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    assigned_schools = db.relationship(
        "MaterialSchool",
        back_populates="material",
        cascade="all, delete-orphan"
    )


# ==========================================================
# MATERIAL SCHOOL
# ==========================================================

class MaterialSchool(db.Model):

    __tablename__ = "material_schools"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=generate_uuid
    )

    material_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "materials.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    school_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "schools.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    material = db.relationship(
        "Material",
        back_populates="assigned_schools"
    )

    school = db.relationship(
        "School"
    )


# ==========================================================
# SURVEY
# ==========================================================

class Survey(db.Model):

    __tablename__ = "surveys"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=generate_uuid
    )

    title = db.Column(
        db.String(255),
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    subject = db.Column(
        db.String(100),
        nullable=False
    )

    grade = db.Column(
        db.String(30),
        nullable=False
    )

    duration_minutes = db.Column(
        db.Integer,
        default=30
    )

    active = db.Column(
        db.Boolean,
        default=True
    )

    instructions = db.Column(
        db.Text,
        default=""
    )

    passing_percentage = db.Column(
        db.Integer,
        default=40
    )

    attempts_allowed = db.Column(
        db.Integer,
        default=1
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    questions = db.relationship(
        "Question",
        back_populates="survey",
        cascade="all, delete-orphan"
    )

    assigned_schools = db.relationship(
        "SurveySchool",
        back_populates="survey",
        cascade="all, delete-orphan"
    )


# ==========================================================
# SURVEY SCHOOL
# ==========================================================

class SurveySchool(db.Model):

    __tablename__ = "survey_schools"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=generate_uuid
    )

    survey_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "surveys.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    school_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "schools.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    survey = db.relationship(
        "Survey",
        back_populates="assigned_schools"
    )

    school = db.relationship(
        "School"
    )


# ==========================================================
# QUESTION
# ==========================================================

class Question(db.Model):

    __tablename__ = "questions"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=generate_uuid
    )

    survey_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "surveys.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    question_no = db.Column(
        db.Integer
    )

    question = db.Column(
        db.Text,
        nullable=False
    )

    option_a = db.Column(
        db.String(255),
        nullable=False
    )

    option_b = db.Column(
        db.String(255),
        nullable=False
    )

    option_c = db.Column(
        db.String(255),
        nullable=False
    )

    option_d = db.Column(
        db.String(255),
        nullable=False
    )

    correct_answer = db.Column(
        db.String(1),
        nullable=False
    )

    marks = db.Column(
        db.Integer,
        default=1
    )

    survey = db.relationship(
        "Survey",
        back_populates="questions"
    )


# ==========================================================
# SURVEY ATTEMPT
# ==========================================================

class SurveyAttempt(db.Model):

    __tablename__ = "survey_attempts"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=generate_uuid
    )

    student_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "students.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    survey_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "surveys.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="Assigned"
    )

    started_at = db.Column(
        db.DateTime
    )

    submitted_at = db.Column(
        db.DateTime
    )

    time_taken = db.Column(
        db.Integer
    )

    attempt_number = db.Column(
        db.Integer,
        default=1
    )

    student = db.relationship(
        "Student"
    )

    survey = db.relationship(
        "Survey"
    )


# ==========================================================
# STUDENT ANSWER
# ==========================================================

class StudentAnswer(db.Model):

    __tablename__ = "student_answers"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=generate_uuid
    )

    student_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "students.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    survey_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "surveys.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    question_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "questions.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    selected_answer = db.Column(
        db.String(1)
    )

    correct_answer = db.Column(
        db.String(1)
    )

    is_correct = db.Column(
        db.Boolean
    )

    student = db.relationship(
        "Student"
    )

    survey = db.relationship(
        "Survey"
    )

    question = db.relationship(
        "Question"
    )


# ==========================================================
# RESULT
# ==========================================================

class Result(db.Model):

    __tablename__ = "results"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=generate_uuid
    )

    student_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "students.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    survey_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "surveys.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    total_questions = db.Column(
        db.Integer,
        default=0
    )

    score = db.Column(
        db.Integer,
        default=0
    )

    percentage = db.Column(
        db.Float,
        default=0
    )

    grade = db.Column(
        db.String(3)
    )

    completion = db.Column(
        db.Float,
        default=0
    )

    completed_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    student = db.relationship(
        "Student"
    )

    survey = db.relationship(
        "Survey"
    )


# ==========================================================
# SUBSCRIPTION
# ==========================================================

class Subscription(db.Model):

    __tablename__ = "subscriptions"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=generate_uuid
    )

    school_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "schools.id",
            ondelete="CASCADE"
        ),
        nullable=True
    )

    amount = db.Column(
        db.Float
    )

    start_date = db.Column(
        db.Date
    )

    expiry_date = db.Column(
        db.Date
    )

    status = db.Column(
        db.String(20)
    )


# ==========================================================
# CONSENT
# ==========================================================

class Consent(db.Model):

    __tablename__ = "consents"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=generate_uuid
    )

    title = db.Column(
        db.String(255),
        nullable=False
    )

    target = db.Column(
        db.String(50),
        nullable=False
    )

    version = db.Column(
        db.String(20),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    active = db.Column(
        db.Boolean,
        default=True
    )

    effective_from = db.Column(
        db.DateTime
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(kenya_tz)
    )

    logs = db.relationship(
        "ConsentLog",
        back_populates="consent",
        cascade="all, delete-orphan"
    )


# ==========================================================
# CONSENT LOG
# ==========================================================

class ConsentLog(db.Model):

    __tablename__ = "consent_logs"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=generate_uuid
    )

    consent_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "consents.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    student_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "students.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    school_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "schools.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # Generic/polymorphic user reference.
    # No FK because user_type determines the entity.
    user_id = db.Column(
        db.String(36),
        nullable=True
    )

    user_type = db.Column(
        db.String(30)
    )

    agreed = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    consented_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(kenya_tz)
    )

    ip_address = db.Column(
        db.String(100)
    )

    country = db.Column(
        db.String(100)
    )

    region = db.Column(
        db.String(100)
    )

    county = db.Column(
        db.String(100)
    )

    city = db.Column(
        db.String(100)
    )

    latitude = db.Column(
        db.Float
    )

    longitude = db.Column(
        db.Float
    )

    timezone = db.Column(
        db.String(100)
    )

    device = db.Column(
        db.String(255)
    )

    browser = db.Column(
        db.String(255)
    )

    operating_system = db.Column(
        db.String(255)
    )

    user_agent = db.Column(
        db.Text
    )

    accepted_language = db.Column(
        db.String(255)
    )

    screen_resolution = db.Column(
        db.String(50)
    )

    gps_latitude = db.Column(
        db.Float
    )

    gps_longitude = db.Column(
        db.Float
    )

    gps_accuracy = db.Column(
        db.Float
    )

    withdrawn = db.Column(
        db.Boolean,
        default=False
    )

    withdrawn_at = db.Column(
        db.DateTime
    )

    withdrawal_reason = db.Column(
        db.Text
    )

    consent = db.relationship(
        "Consent",
        back_populates="logs"
    )

    student = db.relationship(
        "Student"
    )

    school = db.relationship(
        "School"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "student_id",
            "consent_id",
            name="unique_student_consent"
        ),
    )


# ==========================================================
# CONSENT TOKEN
# ==========================================================

class ConsentToken(db.Model):

    __tablename__ = "consent_tokens"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=generate_uuid
    )

    token = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        default=generate_uuid
    )

    consent_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "consents.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    user_type = db.Column(
        db.String(30),
        nullable=False
    )

    # Generic/polymorphic user reference.
    user_id = db.Column(
        db.String(36),
        nullable=False
    )

    recipient_email = db.Column(
        db.String(255),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="Created"
    )

    sent_at = db.Column(
        db.DateTime
    )

    opened_at = db.Column(
        db.DateTime
    )

    accepted_at = db.Column(
        db.DateTime
    )

    declined_at = db.Column(
        db.DateTime
    )

    expires_at = db.Column(
        db.DateTime,
        default=lambda: (
            datetime.now(kenya_tz)
            + timedelta(hours=48)
        )
    )

    ip_address = db.Column(
        db.String(100)
    )

    country = db.Column(
        db.String(100)
    )

    region = db.Column(
        db.String(100)
    )

    county = db.Column(
        db.String(100)
    )

    city = db.Column(
        db.String(100)
    )

    latitude = db.Column(
        db.Float
    )

    longitude = db.Column(
        db.Float
    )

    gps_latitude = db.Column(
        db.Float
    )

    gps_longitude = db.Column(
        db.Float
    )

    gps_accuracy = db.Column(
        db.Float
    )

    browser = db.Column(
        db.String(255)
    )

    operating_system = db.Column(
        db.String(255)
    )

    device = db.Column(
        db.String(255)
    )

    user_agent = db.Column(
        db.Text
    )

    accepted_language = db.Column(
        db.String(255)
    )

    screen_resolution = db.Column(
        db.String(50)
    )

    consent = db.relationship(
        "Consent"
    )

