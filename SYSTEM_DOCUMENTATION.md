# SURVITEC 3D SCHOOL PLATFORM
## System Architecture and Documentation

---

### Table of Contents

1. System Overview
2. Technology Stack
3. Directory Structure
4. Database Schema and ERD
5. Application Entry Point and Configuration
6. Authentication and Authorization
7. API Endpoints (Routes)
8. Service Layer
9. Data Flow Diagrams
10. Consent Management System
11. File Upload and Material Management
12. Survey and Assessment System
13. Email System
14. Frontend Templates
15. Security Considerations
16. Deployment Architecture

---

## 1. System Overview

**Survitec 3D School Platform** is a Flask-based monolithic web application designed for Kenyan schools.

### Core Capabilities

- **School Management**: Multi-tenant school administration with hierarchical roles
- **Student Management**: Student enrollment, profiles, and school assignment
- **Educational Materials**: Upload, assign, and distribute learning materials (PDF, DOCX, PPTX, XLSX, images, video)
- **Surveys and Assessments**: Online quizzes with timed attempts, auto-grading, and results
- **Consent Management**: GDPR-style consent with age-based routing (student vs parent consent), email-based token links, full audit trail

### User Roles

| Role | Description |
|------|-------------|
| **System Admin** | Full platform control - manages schools, admins, students, materials, surveys, consents |
| **School Admin** | School-scoped admin - manages students within their assigned school |
| **Student** | Learner - takes surveys, views materials, manages consent |

---

## 2. Technology Stack

### Backend

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.14 |
| Web Framework | Flask | 3.1.2 |
| ORM | Flask-SQLAlchemy | 3.1.1 |
| ORM Core | SQLAlchemy | 2.0.46 |
| Database (Production) | PostgreSQL | via psycopg2-binary 2.9.12 |
| Database (Development) | SQLite | instance/database.db |
| Template Engine | Jinja2 | 3.1.6 |
| Authentication | werkzeug.security | password hashing |
| Session Management | Flask Sessions | signed cookies |
| Email | Flask-Mail | 0.10.0 |
| WSGI Server | Gunicorn | 26.0.0 |
| Environment Config | python-dotenv | 1.2.2 |
| Timezone | pytz | Africa/Nairobi |

### Key Dependencies

| Package | Purpose |
|---------|---------|
| APScheduler 3.11.2 | Scheduled tasks (available but unused) |
| Flask-JWT-Extended 4.7.1 | JWT support (available but unused) |
| reportlab, weasyprint, pdfminer, pdfplumber | PDF generation/parsing |
| openpyxl, pandas | Excel/data processing |
| beautifulsoup4, lxml | HTML parsing |
| flask-cors 6.0.2 | CORS support (available but unused) |
| Flask-Bcrypt 1.0.1 | Bcrypt (available but unused) |

---

## 3. Directory Structure

```
SURVITEC-3D-PRINTING/
|
+-- main.py              (5835 lines)  Entry point, routes, config, decorators
+-- models.py            (1184 lines)  15 database model classes
+-- consent_service.py   (1146 lines)  Consent business logic
+-- email_service.py     (95 lines)    Async email dispatch
+-- mail_config.py       (3 lines)     Flask-Mail initialization
+-- requirements.txt     (88 packages) Python dependencies
|
+-- instance/
|   +-- database.db                   SQLite development database
|
+-- uploads/
|   +-- materials/                    Uploaded educational files
|
+-- templates/                        36 Jinja2 HTML templates
    +-- login.html                    System admin login
    +-- landing.html                  Consent review page
    +-- forgot.html                   Password reset request
    +-- verify_otp.html               OTP verification
    +-- reset.html                    Password reset form
    +-- schools.html                  School CRUD management
    +-- school_admins.html            School admin CRUD
    +-- school_students.html          Student CRUD per school
    +-- users.html                    System admin CRUD
    +-- materials.html                Material upload/management
    +-- consents.html                 Consent list
    +-- consent_details.html          Consent detail view
    +-- consent_logs.html             Consent audit logs
    +-- create_consent.html           Create new consent
    +-- edit_consent.html             Edit consent
    +-- student_consent.html          Student consent email template
    +-- admin_consent.html            Admin consent email template
    +-- accepted.html                 Consent accepted page
    +-- declined.html                 Consent declined page
    +-- expired.html                  Consent expired page
    +-- pending.html                  Consent pending page
    +-- parent_consent_sent.html      Parent consent sent page
    +-- parent_required.html          Parent consent required page
    +-- access_denied.html            Access denied page
    +-- admin/surveys.html            Survey management
    +-- admin/survey_questions.html   Question management
    +-- school/login.html             School admin login
    +-- school/dashboard.html         School admin dashboard
    +-- students/login.html           Student login
    +-- students/dashboard.html       Student dashboard
    +-- students/materials.html       Student materials list
    +-- students/viewer.html          Material viewer
    +-- students/surveys.html         Student surveys list
    +-- students/take_survey.html     Quiz-taking interface
    +-- students/result.html          Individual result
    +-- students/results.html         All results list
```

---

## 4. Database Schema and ERD

All models use **UUID primary keys** (String(36)) generated via uuid.uuid4().

### 4.1 Models Overview

| # | Model | Table | Purpose | Location |
|---|-------|-------|---------|----------|
| 1 | School | schools | School records | models.py:40 |
| 2 | Student | students | Student profiles | models.py:84 |
| 3 | SystemAdmin | system_admins | Platform admins | models.py:202 |
| 4 | SchoolAdmin | school_admins | School-scoped admins | models.py:247 |
| 5 | Material | materials | Educational files | models.py:337 |
| 6 | MaterialSchool | material_schools | Material-school junction | models.py:397 |
| 7 | Survey | surveys | Quiz/survey definitions | models.py:439 |
| 8 | SurveySchool | survey_schools | Survey-school junction | models.py:515 |
| 9 | Question | questions | Survey questions | models.py:557 |
| 10 | SurveyAttempt | survey_attempts | Student attempt tracking | models.py:625 |
| 11 | StudentAnswer | student_answers | Individual answers | models.py:688 |
| 12 | Result | results | Graded results | models.py:754 |
| 13 | Consent | consents | Consent documents | models.py:825 |
| 14 | ConsentLog | consent_logs | Consent audit trail | models.py:880 |
| 15 | ConsentToken | consent_tokens | Email-based consent links | models.py:1046 |

### 4.2 Model Fields Detail

#### School (models.py:40)
- **id**: String(36) PK, default=uuid4
- **school_code**: String(20), unique, not null
- **name**: String(255), not null
- **email**: String(255)
- **phone**: String(20)
- **active**: Boolean, default=True
- **created_at**: DateTime, default=utcnow
- **Relationships**: students, school_admins

#### Student (models.py:84)
- **id**: String(36) PK, default=uuid4
- **school_id**: String(36) FK -> schools.id (CASCADE)
- **admission_no**: String(50), not null
- **fullname**: String(255), not null
- **email**: String(255)
- **parent_name**: String(255)
- **parent_email**: String(255)
- **parent_phone**: String(20)
- **date_of_birth**: Date
- **grade**: String(50)
- **password_hash**: String(255), not null
- **active**: Boolean, default=True
- **consent_completed**: Boolean, default=False
- **consent_completed_at**: DateTime
- **last_consent_id**: String(36) FK -> consents.id (SET NULL)
- **created_at**: DateTime, default=utcnow
- **updated_at**: DateTime, default=utcnow
- **Constraints**: UniqueConstraint(school_id, admission_no)
- **Relationships**: school, consent

#### SystemAdmin (models.py:202)
- **id**: String(36) PK, default=uuid4
- **username**: String(50), unique, not null
- **email**: String(255), unique, not null
- **password**: String(255), not null
- **otp_code**: String(10)
- **otp_expiration**: DateTime
- **created_at**: DateTime, default=utcnow

#### SchoolAdmin (models.py:247)
- **id**: String(36) PK, default=uuid4
- **school_id**: String(36) FK -> schools.id (CASCADE)
- **fullname**: String(255), not null
- **email**: String(255), unique, not null
- **username**: String(50), unique, not null
- **password_hash**: String(255), not null
- **active**: Boolean, default=True
- **consent_completed**: Boolean, default=False
- **consent_completed_at**: DateTime
- **last_consent_id**: String(36) FK -> consents.id (SET NULL)
- **created_at**: DateTime, default=utcnow
- **updated_at**: DateTime, default=utcnow
- **Relationships**: school, consent

#### Material (models.py:337)
- **id**: String(36) PK, default=uuid4
- **title**: String(255), not null
- **description**: Text
- **subject**: String(100)
- **grade**: String(50)
- **file_name**: String(255)
- **file_path**: String(500)
- **active**: Boolean, default=True
- **uploaded_at**: DateTime, default=utcnow
- **Relationships**: assigned_schools (MaterialSchool, cascade delete)

#### MaterialSchool (models.py:397) - Junction Table
- **id**: String(36) PK, default=uuid4
- **material_id**: String(36) FK -> materials.id (CASCADE)
- **school_id**: String(36) FK -> schools.id (CASCADE)

#### Survey (models.py:439)
- **id**: String(36) PK, default=uuid4
- **title**: String(255), not null
- **description**: Text
- **subject**: String(100)
- **grade**: String(50)
- **duration_minutes**: Integer, default=30
- **active**: Boolean, default=True
- **instructions**: Text
- **passing_percentage**: Float, default=50.0
- **attempts_allowed**: Integer, default=1
- **created_at**: DateTime, default=utcnow
- **Relationships**: questions (cascade delete), assigned_schools (SurveySchool, cascade delete)

#### SurveySchool (models.py:515) - Junction Table
- **id**: String(36) PK, default=uuid4
- **survey_id**: String(36) FK -> surveys.id (CASCADE)
- **school_id**: String(36) FK -> schools.id (CASCADE)

#### Question (models.py:557)
- **id**: String(36) PK, default=uuid4
- **survey_id**: String(36) FK -> surveys.id (CASCADE)
- **question_no**: Integer, not null
- **question**: Text, not null
- **option_a**: String(255)
- **option_b**: String(255)
- **option_c**: String(255)
- **option_d**: String(255)
- **correct_answer**: String(1) (A/B/C/D), not null
- **marks**: Integer, default=1

#### SurveyAttempt (models.py:625)
- **id**: String(36) PK, default=uuid4
- **student_id**: String(36) FK -> students.id (CASCADE)
- **survey_id**: String(36) FK -> surveys.id (CASCADE)
- **status**: String(20), default="Assigned"
- **started_at**: DateTime
- **submitted_at**: DateTime
- **time_taken**: Float
- **attempt_number**: Integer, default=1

#### StudentAnswer (models.py:688)
- **id**: String(36) PK, default=uuid4
- **student_id**: String(36) FK -> students.id (CASCADE)
- **survey_id**: String(36) FK -> surveys.id (CASCADE)
- **question_id**: String(36) FK -> questions.id (CASCADE)
- **selected_answer**: String(1)
- **correct_answer**: String(1)
- **is_correct**: Boolean

#### Result (models.py:754)
- **id**: String(36) PK, default=uuid4
- **student_id**: String(36) FK -> students.id (CASCADE)
- **survey_id**: String(36) FK -> surveys.id (CASCADE)
- **total_questions**: Integer
- **score**: Integer
- **percentage**: Float
- **grade**: String(2) (A-E)
- **completion**: Float
- **completed_at**: DateTime

#### Consent (models.py:825)
- **id**: String(36) PK, default=uuid4
- **title**: String(255), not null
- **target**: String(50) (Student/Parent/SchoolAdmin)
- **version**: String(20), default="1.0"
- **content**: Text, not null
- **active**: Boolean, default=True
- **effective_from**: DateTime
- **created_at**: DateTime, default=utcnow
- **Relationships**: logs (ConsentLog, cascade delete)

#### ConsentLog (models.py:880)
- **id**: String(36) PK, default=uuid4
- **consent_id**: String(36) FK -> consents.id (CASCADE)
- **student_id**: String(36) FK -> students.id (SET NULL)
- **school_id**: String(36) FK -> schools.id (CASCADE)
- **user_id**: String(36)
- **user_type**: String(50)
- **agreed**: Boolean
- **consented_at**: DateTime
- **ip_address**: String(45)
- **country, region, county, city**: String fields
- **latitude, longitude**: Float
- **timezone**: String(100)
- **device, browser, operating_system**: String fields
- **user_agent, accepted_language**: Text
- **screen_resolution**: String(20)
- **gps_latitude, gps_longitude**: Float
- **gps_accuracy**: Float
- **withdrawn**: Boolean, default=False
- **withdrawn_at**: DateTime
- **withdrawal_reason**: Text
- **Constraints**: UniqueConstraint(student_id, consent_id)

#### ConsentToken (models.py:1046)
- **id**: String(36) PK, default=uuid4
- **token**: String(36), unique (UUID)
- **consent_id**: String(36) FK -> consents.id (CASCADE)
- **user_type**: String(50)
- **user_id**: String(36)
- **recipient_email**: String(255)
- **status**: String(20), default="sent"
- **sent_at, opened_at, accepted_at, declined_at**: DateTime
- **expires_at**: DateTime, default=now + 48 hours
- **Full geolocation and device tracking fields**

### 4.3 Entity Relationship Diagram

```
+----------------+      +------------------+
|    Schools     |<---->|  SchoolAdmins    |
|----------------|      |------------------|
| id (PK)        |      | id (PK)          |
| school_code(UQ)|      | school_id (FK)   |
| name           |      | fullname         |
| email          |      | email (UQ)       |
| phone          |      | username (UQ)    |
| active         |      | password_hash    |
| created_at     |      | consent_completed|
+-------+--------+      +------------------+
        |
        +------+------+------------------+
        |      |      |                  |
   +----+--+ +--+--------+ +-----+--------+
   |Students| |Materials | |   Surveys    |
   |---------| |----------| |--------------|
   |id (PK)  | |id (PK)   | |id (PK)      |
   |school_id| |title     | |title        |
   |admission| |subject   | |subject      |
   |fullname | |grade     | |grade        |
   |email    | |file_path | |duration     |
   |grade    | |active    | |passing_pct  |
   |password | +----+-----+ |attempts     |
   |consent  |      |       +------+-------+
   +----+----+      |              |
        |      +-----+------+      |
        |      |MaterialSchool|     |
        |      |(Junction)    |     |
        |      |material_id   |     |
        |      |school_id     |     |
        |      +--------------+     |
        |                           |
   +----+-------+           +------+------
   |SurveyAttempt|           |  Questions  |
   |--------------|          |-------------|
   |student_id FK|          |survey_id FK |
   |survey_id FK |          |question_no  |
   |status       |          |question     |
   |started_at   |          |options A-D  |
   |submitted_at |          |correct_ans  |
   |time_taken   |          |marks        |
   |attempt_num  |          +-------------+
   +------+------+               |
          |               +------+--------+
   +------+------+       |SurveySchool   |
   |StudentAnswer|       |(Junction)     |
   |--------------|      |survey_id (FK) |
   |student_id FK|       |school_id (FK) |
   |survey_id FK |       +---------------+
   |question_id  |
   |selected_ans |
   |correct_ans  |
   |is_correct   |
   +--------------+
          |
   +------+-------+
   |   Results    |
   |---------------|
   |student_id FK |
   |survey_id FK  |
   |score         |
   |percentage    |
   |grade (A-E)   |
   |completion    |
   |completed_at  |
   +---------------+

+---------------+     +---------------+
|   Consents    |<--->|  ConsentLog   |
|---------------|     |---------------|
| id (PK)       |     | consent_id FK |
| title         |     | student_id FK |
| target        |     | school_id FK  |
| version       |     | agreed        |
| content       |     | ip_address    |
| active        |     | geo fields    |
| effective_from|     | device fields |
+-------+-------+     | withdrawn     |
        |              +---------------+
   +----+---------+
   | ConsentToken |
   |---------------|
   | token (UQ)   |
   | consent_id   |
   | user_type    |
   | user_id      |
   | recipient    |
   | status       |
   | expires_at   |
   +---------------+
```

---

## 5. Application Entry Point and Configuration

**File**: main.py (5835 lines)

### 5.1 App Initialization (lines 18-82)

- Flask app created at line 18: `app = Flask(__name__)`
- Database URI loaded from `DATABASE_URL` env var via python-dotenv (line 30)
- Secret key hardcoded: `supersecretkey123` (line 41)
- Upload folder: `uploads/materials` (line 44)
- Allowed extensions: pdf, doc, docx, ppt, pptx, xls, xlsx, zip, mp4, png, jpg, jpeg (lines 46-72)

### 5.2 Database Seeding (lines 98-132)

On startup, auto-creates default admin:
- Username: admin
- Password: admin123
- Email: kephakimathikanyola@gmail.com

### 5.3 Mail Configuration (lines 135-141)

- SMTP: smtp.gmail.com:587 (TLS)
- Username: survitec3d@gmail.com
- Password: (app password, hardcoded)
- Sender: survitec3d@gmail.com

### 5.4 Dev Server (lines 5829-5835)

- Host: 0.0.0.0
- Port: 5050
- Debug: True

---

## 6. Authentication and Authorization

### 6.1 Three-Tier Role System

| Role | Model | Session Keys | Login Route |
|------|-------|-------------|-------------|
| System Admin | SystemAdmin | system_admin_id | /system/login |
| School Admin | SchoolAdmin | school_admin_id, school_id | /school/login |
| Student | Student | student_id, school_id | /student/login |

### 6.2 Authorization Decorators (main.py)

| Decorator | Line | Purpose |
|-----------|------|---------|
| @system_admin_required | 312-429 | Validates session system_admin_id, checks SystemAdmin exists in DB |
| @school_login_required | 457-476 | Validates session school, checks SchoolAdmin exists |
| @student_login_required | 2439-2539 | Validates student_id, checks student exists, is active, school is active |
| @shared_access | 433-449 | Allows System Admin OR School Admin |

### 6.3 Password Handling

All roles use werkzeug.security:
- `generate_password_hash()` for creation
- `check_password_hash()` for verification

### 6.4 OTP / Password Reset Flow

1. User visits /forgot -> enters email
2. System generates 6-digit OTP, stores in SystemAdmin.otp_code
3. OTP expires in 10 minutes
4. User enters OTP at /verify_otp
5. On success, redirected to /reset_password
6. New password saved with generate_password_hash()

---

## 7. API Endpoints (Routes)

### 7.1 Authentication Routes

| Route | Method | Function | Auth | Line |
|-------|--------|----------|------|------|
| /system/login | GET/POST | system_login | Public | 158 |
| /admin/logout | GET | admin_logout | System Admin | 874 |
| /school/login | GET/POST | school_login | Public | 4619 |
| /school/logout | GET | school_logout | Public | 480 |
| /student/login | GET/POST | student_login | Public | 2545 |
| /student/logout | GET | student_logout | Student | 3093 |
| /forgot | GET/POST | forgot | Public | 694 |
| /verify_otp | GET/POST | verify_otp | Public | 756 |
| /reset_password | GET/POST | reset_password | OTP Verified | 814 |

### 7.2 System Admin - User Management

| Route | Method | Function | Line |
|-------|--------|----------|------|
| /users | GET/POST | manage_users | 493 |
| /edit_user/<id> | POST | edit_user | 587 |
| /delete_user/<id> | POST | delete_user | 665 |

### 7.3 System Admin - School Management

| Route | Method | Function | Line |
|-------|--------|----------|------|
| /schools | GET/POST | manage_schools | 890 |
| /edit_school/<school_id> | POST | edit_school | 1056 |
| /delete_school/<id> | POST | delete_school | 1200 |
| /toggle_school/<id> | POST | toggle_school | 1224 |

### 7.4 System Admin - School Admin Management

| Route | Method | Function | Line |
|-------|--------|----------|------|
| /school_admins | GET/POST | manage_school_admins | 1248 |
| /edit_school_admin/<id> | POST | edit_school_admin | 1364 |
| /delete_school_admin/<id> | POST | delete_school_admin | 1406 |
| /toggle_school_admin/<id> | POST | toggle_school_admin | 1429 |

### 7.5 Student Management (Shared Access)

| Route | Method | Function | Auth | Line |
|-------|--------|----------|------|------|
| /students/<school_id> | GET | school_students | Shared | 1452 |
| /students/add/<school_id> | POST | add_student | Shared | 1493 |
| /students/edit/<id> | POST | edit_student | Shared | 1638 |
| /students/toggle/<id> | POST | toggle_student | Shared | 1715 |
| /students/delete/<id> | POST | delete_student | Shared | 1751 |

### 7.6 Material Management (System Admin)

| Route | Method | Function | Line |
|-------|--------|----------|------|
| /materials | GET/POST | manage_materials | 1784 |
| /material_schools/<material_id> | GET | material_schools | 2084 |
| /toggle_material/<id> | POST | toggle_material | 2100 |
| /download_material/<id> | GET | download_material | 2137 |
| /get_material/<id> | GET | get_material | 2157 |
| /edit_material/<id> | POST | edit_material | 2193 |
| /delete_material/<id> | POST | delete_material | 2378 |

### 7.7 Student - Materials and Content

| Route | Method | Function | Line |
|-------|--------|----------|------|
| /student/materials | GET | student_materials | 3112 |
| /student/material/<id> | GET | view_material | 3182 |
| /student/material/content/<id> | GET | material_content | 3221 |
| /student/material/download/<id> | GET | student_download_material | 3266 |

### 7.8 Survey Management (System Admin)

| Route | Method | Function | Line |
|-------|--------|----------|------|
| /surveys | GET/POST | surveys | 3311 |
| /survey/<id>/questions | GET | survey_questions | 3439 |
| /survey/<id>/get | GET | get_survey | 3461 |
| /survey/<id>/edit | POST | edit_survey | 3501 |
| /survey/<id>/toggle | POST | toggle_survey | 3597 |
| /survey/<id>/delete | POST | delete_survey | 3621 |
| /survey/<survey_id>/question/add | POST | add_question | 3649 |
| /question/<id>/get | GET | get_question | 3727 |
| /question/<id>/edit | POST | edit_question | 3751 |
| /question/<id>/delete | POST | delete_question | 3815 |

### 7.9 Student - Survey Taking

| Route | Method | Function | Line |
|-------|--------|----------|------|
| /student/surveys | GET | student_surveys | 4548 |
| /student/survey/<id>/start | GET | start_survey | 3875 |
| /student/survey/attempt/<attempt_id> | GET | take_survey | 4031 |
| /student/survey/<attempt_id>/submit | POST | submit_survey | 4067 |
| /student/result/<survey_id> | GET | student_result | 4305 |
| /student/survey/<survey_id>/retake | GET | retake_survey | 4430 |
| /student/results | GET | student_results | 4591 |

### 7.10 Consent Management

| Route | Method | Function | Auth | Line |
|-------|--------|----------|------|------|
| /consent/<token> | GET/POST | view_consent | Public | 4863 |
| /consent/accepted/<token> | GET | consent_accepted | Public | 5111 |
| /consent/declined/<token> | GET | consent_declined | Public | 5123 |
| /consent/expired | GET | consent_expired | Public | 5138 |
| /consent/access-denied/<token> | GET | consent_access_denied | Public | 5147 |
| /consent/parent/<token> | GET | parent_required | Public | 5202 |
| /consent/send-parent/<token> | GET | send_parent_consent | Public | 5217 |
| /consent/pending/<token> | GET | consent_pending | Public | 5256 |
| /school-admin/consent/<token> | GET | school_admin_consent | Public | 5626 |
| /consent/request/<user_type>/user_id | GET | request_new_consent | Public | 5638 |
| /system/consents | GET | manage_consents | System Admin | 5273 |
| /system/consent/create | GET/POST | create_consent | System Admin | 5323 |
| /system/consent/<id>/edit | GET/POST | edit_consent | System Admin | 5392 |
| /system/consent/<id>/activate | GET | activate_consent | System Admin | 5437 |
| /system/consent/<id>/deactivate | GET | deactivate_consent | System Admin | 5477 |
| /system/consent/<id>/delete | GET | delete_consent | System Admin | 5501 |
| /system/consent/<id>/duplicate | GET | duplicate_consent | System Admin | 5547 |
| /system/consent/<consent_id> | GET | admin_consent_details | System Admin | 5587 |
| /system/consent/logs | GET | consent_logs | System Admin | 5760 |
| /parent/consent/sent | GET | parent_consent_sent | Public | 5778 |

---

## 8. Service Layer

### 8.1 Consent Service (consent_service.py)

| Function | Line | Purpose |
|----------|------|---------|
| calculate_age() | 34 | Calculates student age from DOB (supports Student, date, datetime, string) |
| get_student_target() | 125 | Returns "Student" if age >= 18, else "Parent" |
| determine_student_category() | 144 | Returns "Minor" or "Adult" |
| requires_parent() | 163 | Boolean check if student is under 18 |
| get_active_consent() | 176 | Finds active Consent record for a target type |
| has_valid_student_consent() | 212 | Checks if student has agreed to current active consent |
| has_valid_school_admin_consent() | 273 | Checks if school admin has agreed to current active consent |
| create_consent_token() | 334 | Creates ConsentToken with 48-hour expiry |
| build_consent_link() | 464 | Generates external URL for consent view |
| generate_student_consent() | 499 | End-to-end: determine target, find consent, create token |
| generate_school_admin_consent() | 581 | Same for school admins |
| send_parent_consent_email() | 716 | Sends inline HTML email to parent |
| send_school_admin_consent_email() | 887 | Sends inline HTML email to school admin |

### 8.2 Email Service (email_service.py)

| Function | Line | Purpose |
|----------|------|---------|
| _send_async_email() | 15 | Background thread worker for SMTP |
| send_email() | 41 | Spawns Python Thread for async email (non-blocking) |
| send_student_consent_email() | 55 | Renders HTML template, fires async send |
| send_school_admin_consent_email() | 76 | Same for school admin consent |

### 8.3 Mail Config (mail_config.py)

- Line 3: `mail = Mail()` - bare Flask-Mail instance
- Initialized with app at main.py:21 via `mail.init_app(app)`

---

## 9. Data Flow Diagrams

### 9.1 Student Login Flow

```
[Student Browser]
       |
       v
POST /student/login (school_code, admission_no, password)
       |
       v
[Find School by school_code]
       |
       v
[Find Student by admission_no + school_id]
       |
       v
[Verify password via check_password_hash()]
       |
       v
[Calculate age via consent_service.calculate_age()]
       |
       +--- Under 18 ---> consent target = "Parent"
       |
       +--- 18+ --------> consent target = "Student"
       |
       v
[Find active Consent for target type]
       |
       v
[Check ConsentLog for existing agreement]
       |
       +--- Already agreed ---> Create session -> /student/dashboard
       |
       +--- Not agreed -------> Create ConsentToken
                                 Send email with consent link
                                 Redirect to /pending.html
```

### 9.2 Survey Taking and Grading Flow

```
[Student -> GET /student/survey/<id>/start]
       |
       v
[Validate: survey active, correct grade, assigned to school, attempts remaining]
       |
       v
[Create/Update SurveyAttempt (status="Started", started_at=now)]
       |
       v
[Redirect to /student/survey/attempt/<attempt_id>]
       |
       v
[Render take_survey.html with questions and timer]
       |
       v
[Student answers questions, clicks Submit]
       |
       v
POST /student/survey/<attempt_id>/submit
       |
       v
[For each question:]
  |-- Compare selected_answer vs correct_answer
  |-- Create StudentAnswer record (is_correct = True/False)
       |
       v
[Calculate: score, percentage, grade (A-E), completion %]
       |
       v
[Create Result record]
       |
       v
[Update SurveyAttempt: status="Completed", submitted_at, time_taken]
       |
       v
[Redirect to /student/result/<survey_id>]
```

### 9.3 Consent Token Lifecycle

```
[System Admin creates/activates Consent]
       |
       v
[User created or logs in]
       |
       v
[consent_service determines target based on age]
       |
       v
[get_active_consent() finds latest active consent for target]
       |
       v
[create_consent_token() creates token with 48-hour expiry]
       |
       v
[email_service sends HTML email with consent link]
       |
       v
[User clicks link -> GET /consent/<token>]
       |
       v
[Validate token: not expired, not already accepted]
       |
       v
[Track: IP, browser, OS, device, user-agent on first open]
       |
       v
[User clicks Accept or Decline]
       |
       v
[ConsentLog record created with full audit trail]
       |
       v
[User flagged as consent_completed=True]
       |
       v
[Redirect to appropriate confirmation page]
```

### 9.4 Material Upload and Access Flow

```
[System Admin -> POST /materials]
       |
       v
[Validate file extension against ALLOWED_EXTENSIONS]
       |
       v
[Generate UUID filename, save to uploads/materials/]
       |
       v
[Create Material record in database]
       |
       v
[Create MaterialSchool junction records for selected schools]
       |
       v
[Material now accessible to students in assigned schools]

--- Student Access ---

[Student -> GET /student/materials]
       |
       v
[Query Materials via MaterialSchool JOIN (filtered by school_id + grade)]
       |
       v
[Render materials list]

[Student -> GET /student/material/<id>]
       |
       v
[Access check: material active AND assigned to student's school]
       |
       v
[Render viewer page (inline or download)]
```

### 9.5 Password Reset Flow

```
[User -> GET /forgot -> enters email]
       |
       v
[Find SystemAdmin by email]
       |
       v
[Generate 6-digit OTP, store in otp_code]
[Set otp_expiration = now + 10 min]
       |
       v
[Send OTP via email]
       |
       v
[Redirect to /verify_otp]
       |
       v
[User enters OTP -> POST /verify_otp]
       |
       v
[Validate: otp matches AND not expired]
       |
       v
[Store verified_admin_id in session]
       |
       v
[Redirect to /reset_password]
       |
       v
[User enters new password -> POST /reset_password]
       |
       v
[Hash password, update SystemAdmin record]
       |
       v
[Redirect to /system/login]
```

---

## 10. Consent Management System

### 10.1 Age-Based Routing

The consent system uses age to determine the correct consent flow:

| Age | Target | Flow |
|-----|--------|------|
| Under 18 | Parent | Student cannot consent directly. Parent receives email. |
| 18 or over | Student | Student receives consent email directly. |

### 10.2 Consent Token Lifecycle

1. Token created with UUID, 48-hour expiry
2. Status progresses: sent -> opened -> accepted/declined
3. Full geolocation and device fingerprinting captured at each step

### 10.3 Consent Audit Trail (ConsentLog)

Every consent action logs:
- IP address, country, region, county, city
- Latitude/longitude, GPS coordinates
- Device, browser, operating system
- User agent, screen resolution
- Withdrawal status and reason

### 10.4 Consent Enforcement

- Students cannot access dashboard/surveys without consent
- School admins cannot access their dashboard without consent
- Checked at login time and enforced via session flags

---

## 11. File Upload and Material Management

### 11.1 Allowed File Types

pdf, doc, docx, ppt, pptx, xls, xlsx, zip, mp4, png, jpg, jpeg

### 11.2 Upload Flow

1. System Admin selects file + title + description + subject + grade + target schools
2. File validated by extension check
3. UUID-based filename generated (prevents collisions)
4. Saved to uploads/materials/
5. Material record created in database
6. MaterialSchool junction records created for each assigned school

### 11.3 Access Control

- Students can only see materials assigned to their school
- Materials can be filtered by grade
- Materials can be activated/deactivated

---

## 12. Survey and Assessment System

### 12.1 Survey Lifecycle

1. System Admin creates survey with title, description, subject, grade, duration, instructions, passing %, attempts allowed
2. System Admin assigns survey to specific schools
3. System Admin adds questions (A/B/C/D options, correct answer, marks)
4. Student sees assigned surveys in dashboard

### 12.2 Attempt Flow

1. Student starts survey -> SurveyAttempt created (status="Assigned")
2. Timer starts (duration_minutes from survey config)
3. Student answers questions
4. On submit: answers graded against correct_answer
5. Score, percentage, grade (A-E) calculated
6. Result record created
7. SurveyAttempt updated to "Completed"

### 12.3 Grading Scale

| Grade | Percentage Range |
|-------|-----------------|
| A | 80-100% |
| B | 70-79% |
| C | 60-69% |
| D | 50-59% |
| E | Below 50% |

---

## 13. Email System

### 13.1 Configuration

- SMTP Server: smtp.gmail.com:587 (TLS)
- Sender: survitec3d@gmail.com
- Transport: Flask-Mail

### 13.2 Async Sending

Emails are sent in background threads to avoid blocking the HTTP worker:

```python
thread = Thread(target=_send_async_email, args=(app, msg))
thread.start()
```

### 13.3 Email Types

1. **OTP Password Reset** - 6-digit code to SystemAdmin email
2. **Student Consent Request** - HTML email with consent link
3. **Parent Consent Request** - HTML email for minor students
4. **School Admin Consent Request** - HTML email with consent link

---

## 14. Frontend Templates

### 14.1 Template Organization

| Group | Directory | Count | Audience |
|-------|-----------|-------|----------|
| System Admin | templates/ | 14 | Platform administrators |
| Admin Sub | templates/admin/ | 2 | Survey/question management |
| School Admin | templates/school/ | 2 | School administrators |
| Student | templates/students/ | 8 | Students |
| Consent/Status | templates/ | 10 | Public (token-based access) |

### 14.2 Key Pages

| Page | Purpose |
|------|---------|
| login.html | System admin authentication |
| schools.html | Full school CRUD with stats |
| materials.html | Material upload with multi-school assignment |
| admin/surveys.html | Survey creation and management |
| students/dashboard.html | Student home with stats |
| students/take_survey.html | Timed quiz interface |
| landing.html | Consent review/accept/decline |

---

## 15. Security Considerations

### 15.1 Current Security Posture

| Area | Status | Detail |
|------|--------|--------|
| Password Hashing | Good | werkzeug.security (PBKDF2) |
| Session Management | Basic | Flask signed cookies |
| CSRF Protection | Missing | No CSRF tokens on forms |
| Rate Limiting | Missing | No login attempt limits |
| Input Validation | Basic | File extension check only |
| SQL Injection | Protected | SQLAlchemy ORM parameterized queries |
| Secret Key | Weak | Hardcoded 'supersecretkey123' |
| SMTP Credentials | Hardcoded | In source code (main.py:140) |
| Default Admin | Hardcoded | admin/admin123 on first run |

### 15.2 Recommendations

1. Move SECRET_KEY to environment variable
2. Move SMTP credentials to .env
3. Add CSRF protection (Flask-WTF)
4. Add rate limiting on login endpoints (Flask-Limiter)
5. Remove hardcoded default admin credentials
6. Add input validation/sanitization
7. Add HTTPS enforcement
8. Add Content Security Policy headers

---

## 16. Deployment Architecture

### 16.1 Production Stack

```
[Client Browser]
       |
       v
[Render Cloud Platform]
       |
       v
[Gunicorn WSGI Server]
       |
       v
[Flask Application (main.py)]
       |
       +--- [PostgreSQL Database]
       |
       +--- [File System: uploads/materials/]
       |
       +--- [Gmail SMTP: smtp.gmail.com:587]
```

### 16.2 Environment Variables

| Variable | Purpose |
|----------|---------|
| DATABASE_URL | PostgreSQL connection string |

### 16.3 Server Configuration

- Host: 0.0.0.0
- Port: 5050 (dev) / gunicorn managed (production)
- Debug: True (dev only)
- Database pool: pre_ping=True, recycle=300

### 16.4 Background Processing

- Email: Python threading.Thread (background SMTP)
- No task queue (Celery/Redis) configured
- No periodic jobs configured (APScheduler available but unused)

---

*Documentation generated for SURVITEC-3D-PRINTING codebase.*