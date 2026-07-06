from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, date
from decimal import Decimal
db = SQLAlchemy()

class School(db.Model):
    __tablename__ = "schools"

    id = db.Column(db.Integer, primary_key=True)

    school_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    name = db.Column(
        db.String(255),
        nullable=False
    )

    email = db.Column(db.String(255))

    phone = db.Column(db.String(20))

    active = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

class SystemAdmin(db.Model):

    id = db.Column(db.Integer, primary_key=True)

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


    otp_code = db.Column(db.String(6))

    otp_expiration = db.Column(db.DateTime)


    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

class SchoolAdmin(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    school_id = db.Column(
        db.Integer,
        db.ForeignKey("schools.id")
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255)
    )
    active = db.Column(
        db.Boolean,
        default=True
    )
    school = db.relationship(
        "School",
        backref="school_admins"
    )

class Student(db.Model):

    __tablename__ = "students"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    school_id = db.Column(
        db.Integer,
        db.ForeignKey("schools.id"),
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

    school = db.relationship(
        "School",
        backref="students"
    )

    __table_args__ = (

        db.UniqueConstraint(
            "school_id",
            "admission_no",
            name="unique_student_school"
        ),

    )

class Material(db.Model):

    __tablename__ = "materials"

    id = db.Column(
        db.Integer,
        primary_key=True
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

class MaterialSchool(db.Model):

    __tablename__ = "material_schools"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    material_id = db.Column(
        db.Integer,
        db.ForeignKey("materials.id"),
        nullable=False
    )

    school_id = db.Column(
        db.Integer,
        db.ForeignKey("schools.id"),
        nullable=False
    )

    material = db.relationship(
        "Material",
        back_populates="assigned_schools"
    )

    school = db.relationship(
        "School"
    )
class Survey(db.Model):

    __tablename__ = "surveys"

    id = db.Column(
        db.Integer,
        primary_key=True
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

class SurveySchool(db.Model):

    __tablename__ = "survey_schools"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    survey_id = db.Column(
        db.Integer,
        db.ForeignKey("surveys.id"),
        nullable=False
    )

    school_id = db.Column(
        db.Integer,
        db.ForeignKey("schools.id"),
        nullable=False
    )

    survey = db.relationship(
        "Survey",
        back_populates="assigned_schools"
    )

    school = db.relationship(
        "School"
    )
class Question(db.Model):

    __tablename__ = "questions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    survey_id = db.Column(
        db.Integer,
        db.ForeignKey("surveys.id"),
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

    survey = db.relationship(
        "Survey",
        back_populates="questions"
    )
    marks = db.Column(
    db.Integer,
    default=1
    )
class SurveyAttempt(db.Model):

    __tablename__ = "survey_attempts"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False
    )

    survey_id = db.Column(
        db.Integer,
        db.ForeignKey("surveys.id"),
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

    student = db.relationship(
        "Student"
    )

    survey = db.relationship(
        "Survey"
    )
    attempt_number = db.Column(
    db.Integer,
    default=1
    )

class StudentAnswer(db.Model):

    __tablename__ = "student_answers"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False
    )

    survey_id = db.Column(
        db.Integer,
        db.ForeignKey("surveys.id"),
        nullable=False
    )

    question_id = db.Column(
        db.Integer,
        db.ForeignKey("questions.id"),
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

class Result(db.Model):

    __tablename__ = "results"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False
    )

    survey_id = db.Column(
        db.Integer,
        db.ForeignKey("surveys.id"),
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


class Subscription(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    school_id = db.Column(
        db.Integer,
        db.ForeignKey("schools.id")
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