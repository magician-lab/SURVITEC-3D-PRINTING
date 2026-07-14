from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, abort
from models import db, School, SchoolAdmin, Student, Subscription, SurveySchool, Material, Result, SystemAdmin,Survey,StudentAnswer, SurveyAttempt, MaterialSchool, Question
from werkzeug.security import generate_password_hash, check_password_hash
from decimal import Decimal
from datetime import datetime, date, timedelta
from flask_mail import Mail, Message
from functools import wraps
from sqlalchemy import extract, func
from sqlalchemy.exc import IntegrityError
import os
import random
from werkzeug.utils import secure_filename
from flask import send_from_directory
import uuid
from flask import send_file

app = Flask(__name__)

from dotenv import load_dotenv

load_dotenv()

import os

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {

    "pool_pre_ping": True,

    "pool_recycle": 300

}
app.config['SECRET_KEY'] = 'supersecretkey123'

db.init_app(app)
UPLOAD_FOLDER = "uploads/materials"

ALLOWED_EXTENSIONS = {

    "pdf",

    "doc",

    "docx",

    "ppt",

    "pptx",

    "xls",

    "xlsx",

    "zip",

    "mp4",

    "png",

    "jpg",

    "jpeg"

}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(

    UPLOAD_FOLDER,

    exist_ok=True

)

def allowed_file(filename):

    return (

        "." in filename

        and

        filename.rsplit(".",1)[1].lower()

        in ALLOWED_EXTENSIONS

    )

with app.app_context():
    db.create_all()
    # =====================================================
    # CHECK IF ADMIN EXISTS
    # =====================================================

    existing_admin = SystemAdmin.query.filter_by(
        username="admin"
    ).first()

    # =====================================================
    # CREATE DEFAULT ADMIN ONLY ONCE
    # =====================================================

    if not existing_admin:

        admin = SystemAdmin(

            username="admin",

            email="kephakimathikanyola@gmail.com",

            password=generate_password_hash("admin123"),

        )

        db.session.add(admin)

        db.session.commit()

        print("✅ Default admin created")

    else:

        print("✅ Admin already exists")


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'magicdevelopers9@gmail.com'
app.config['MAIL_PASSWORD'] = 'rjgp cifh gqim wkln'
app.config['MAIL_DEFAULT_SENDER'] = 'SURVITEC 3D <magicdevelopers9@gmail.com>'

mail = Mail(app)


@app.route("/system/login", methods=["GET", "POST"])
def system_login():

    # -----------------------------------
    # ALREADY LOGGED IN?
    # -----------------------------------
    if session.get("system_admin_id"):
        return redirect(url_for("manage_schools"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "warning")
            return render_template("login.html")

        # -----------------------------------
        # FIND ADMIN
        # -----------------------------------
        admin = SystemAdmin.query.filter_by(
            username=username
        ).first()

        if admin is None:
            flash("Invalid username or password.", "danger")
            return render_template("login.html")

        # -----------------------------------
        # VERIFY PASSWORD
        # -----------------------------------
        if not check_password_hash(admin.password, password):
            flash("Invalid username or password.", "danger")
            return render_template("login.html")

        # -----------------------------------
        # CREATE SYSTEM SESSION
        # -----------------------------------
        session["system_admin_id"] = admin.id
        session["system_admin_logged_in"] = True

        # Optional but recommended
        session.permanent = True
        session.modified = True

        # Debug (remove later)
        print("SYSTEM LOGIN SESSION:", dict(session))

        flash("Welcome back!", "success")

        return redirect(url_for("manage_schools"))

    return render_template("login.html")




def system_admin_required(f):

    @wraps(f)
    def wrapper(*args, **kwargs):

        system_admin_id = session.get("system_admin_id")

        # No system login
        if not system_admin_id:

            flash(
                "You must login as a System Administrator.",
                "danger"
            )

            return redirect(url_for("system_login"))

        # Verify admin still exists
        admin = SystemAdmin.query.get(system_admin_id)

        if admin is None:

            session.pop("system_admin_id", None)
            session.pop("system_admin_logged_in", None)

            flash(
                "System administrator session expired.",
                "warning"
            )

            return redirect(url_for("system_login"))

        return f(*args, **kwargs)

    return wrapper

def shared_access(f):
    @wraps(f)
    def wrapper(*args, **kwargs):

        school_admin = session.get("school_admin_id")
        system_admin = session.get("system_admin_id")

        # -----------------------------------
        # MUST BE EITHER ONE
        # -----------------------------------
        if not school_admin and not system_admin:
            flash("Login required.", "warning")
            return redirect(url_for("school_login"))

        return f(*args, **kwargs)

    return wrapper

from functools import wraps

from functools import wraps
from flask import session, redirect, url_for, flash
from models import SchoolAdmin

def school_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):

        school = session.get("school")

        if not school:
            flash("Please log in as a school administrator.", "warning")
            return redirect(url_for("school_login"))

        admin = SchoolAdmin.query.get(school["admin_id"])

        if not admin:
            session.pop("school", None)
            flash("Your session has expired.", "warning")
            return redirect(url_for("school_login"))

        return f(*args, **kwargs)

    return wrapper



@app.route("/school/logout")
def school_logout():

    # -----------------------------------
    # REMOVE SCHOOL SESSION ONLY
    # -----------------------------------
    session.pop("school_admin_id", None)
    session.pop("school_id", None)

    flash("You have been logged out successfully.", "success")

    return redirect(url_for("school_login"))

@app.route("/admin/logout")
def admin_logout():

    for key in list(session.keys()):

        if key.startswith("system_admin"):

            session.pop(key, None)

    flash(
        "Logged out successfully.",
        "success"
    )

    return redirect(url_for("system_login"))

@app.route("/users", methods=["GET", "POST"])
@system_admin_required
def manage_users():

    # =====================================================
    # ADD USER
    # =====================================================

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")


        # =================================================
        # VALIDATION
        # =================================================

        if not username or not email or not password:

            flash(
                "All fields are required",
                "error"
            )

            return redirect(url_for("manage_users"))

        # =================================================
        # CHECK DUPLICATE EMAIL
        # =================================================

        existing_email = SystemAdmin.query.filter_by(email=email).first()

        if existing_email:

            flash(
                "Email already exists",
                "error"
            )

            return redirect(url_for("manage_users"))

        # =================================================
        # CHECK DUPLICATE USERNAME
        # =================================================

        existing_user = SystemAdmin.query.filter_by(username=username).first()

        if existing_user:

            flash(
                "Username already exists",
                "error"
            )

            return redirect(url_for("manage_users"))

        # =================================================
        # CREATE USER
        # =================================================

        new_user = SystemAdmin(
            username=username,
            email=email,
            password=generate_password_hash(password),
        )

        db.session.add(new_user)
        db.session.commit()

        flash(
            "User added successfully",
            "success"
        )

        return redirect(url_for("manage_users"))

    # =====================================================
    # VIEW USERS
    # =====================================================

    users = SystemAdmin.query.all()

    return render_template(
        "users.html",
        users=users
    )


# =========================================================
# EDIT USER
# =========================================================

@app.route("/edit_user/<int:id>", methods=["POST"])
@system_admin_required
def edit_user(id):

    user = SystemAdmin.query.get_or_404(id)

    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")


    # =====================================================
    # VALIDATION
    # =====================================================

    if not username or not email:

        flash(
            "Username, email and role are required",
            "error"
        )

        return redirect(url_for("manage_users"))

    # =====================================================
    # CHECK DUPLICATE EMAIL
    # =====================================================

    existing_email = SystemAdmin.query.filter_by(email=email).first()

    if existing_email and existing_email.id != user.id:

        flash(
            "Email already exists",
            "error"
        )

        return redirect(url_for("manage_users"))

    # =====================================================
    # CHECK DUPLICATE USERNAME
    # =====================================================

    existing_username = SystemAdmin.query.filter_by(username=username).first()

    if existing_username and existing_username.id != user.id:

        flash(
            "Username already exists",
            "error"
        )

        return redirect(url_for("manage_users"))

    # =====================================================
    # UPDATE USER
    # =====================================================

    user.username = username
    user.email = email

    if password:
        user.password = generate_password_hash(password)

    db.session.commit()

    flash(
        "User updated successfully",
        "success"
    )

    return redirect(url_for("manage_users"))


# =========================================================
# DELETE USER
# =========================================================

@app.route("/delete_user/<int:id>", methods=["POST"])
@system_admin_required
def delete_user(id):

    user = SystemAdmin.query.get_or_404(id)

    # =====================================================
    # PREVENT SELF DELETE
    # =====================================================

    if session.get("user_id") == user.id:

        flash(
            "You cannot delete your own account",
            "error"
        )

        return redirect(url_for("manage_users"))

    db.session.delete(user)
    db.session.commit()

    flash(
        "User deleted successfully",
        "success"
    )

    return redirect(url_for("manage_users"))

@app.route("/forgot", methods=["GET", "POST"])
def forgot():

    if request.method == "POST":

        email = request.form.get("email")

        user = SystemAdmin.query.filter_by(email=email).first()

        if user:

            # =================================================
            # GENERATE OTP
            # =================================================

            otp = str(random.randint(100000, 999999))

            user.otp_code = otp
            user.otp_expiration = datetime.utcnow() + timedelta(minutes=10)

            db.session.commit()

            # =================================================
            # SEND EMAIL
            # =================================================

            msg = Message(
                subject="Password Reset OTP",
                recipients=[email]
            )

            msg.body = f"""
Your OTP is: {otp}

It expires in 10 minutes.
"""

            mail.send(msg)

            session["reset_email"] = email

            flash(
                "OTP sent to your email",
                "success"
            )

            return redirect(url_for("verify_otp"))

        else:

            flash(
                "Email not found",
                "error"
            )

    return render_template("forgot.html")


# =========================================================
# VERIFY OTP
# =========================================================

@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():

    if request.method == "POST":

        otp = request.form.get("otp")

        email = session.get("reset_email")

        if not email:

            flash(
                "Session expired",
                "error"
            )

            return redirect(url_for("forgot"))

        user = SystemAdmin.query.filter_by(email=email).first()

        if user and user.otp_code == otp:

            # =============================================
            # CHECK OTP EXPIRATION
            # =============================================

            if datetime.utcnow() <= user.otp_expiration:

                session["otp_verified"] = True

                flash(
                    "OTP verified successfully",
                    "success"
                )

                return redirect(url_for("reset_password"))

            else:

                flash(
                    "OTP expired",
                    "error"
                )

        else:

            flash(
                "Invalid OTP",
                "error"
            )

    return render_template("verify_otp.html")


# =========================================================
# RESET PASSWORD
# =========================================================

@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():

    # =====================================================
    # CHECK OTP VERIFIED
    # =====================================================

    if not session.get("otp_verified"):
        return redirect(url_for("login"))

    if request.method == "POST":

        new_password = request.form.get("password")

        email = session.get("reset_email")

        if not email:

            flash(
                "Session expired",
                "error"
            )

            return redirect(url_for("forgot"))

        user = SystemAdmin.query.filter_by(email=email).first()

        if not user:

            flash(
                "User not found",
                "error"
            )

            return redirect(url_for("forgot"))

        # =================================================
        # UPDATE PASSWORD
        # =================================================

        user.password = generate_password_hash(new_password)

        # CLEAR OTP
        user.otp_code = None
        user.otp_expiration = None

        db.session.commit()

        # CLEAR SESSION
        session.clear()

        flash(
            "Password reset successful",
            "success"
        )

        return redirect(url_for("login"))

    return render_template("reset.html")



@app.route(
"/schools",
methods=["GET", "POST"]
)
@system_admin_required
def manage_schools():

    if request.method == "POST":

        school_code = request.form.get(
            "school_code"
        )

        name = request.form.get(
            "name"
        )

        email = request.form.get(
            "email"
        )

        phone = request.form.get(
            "phone"
        )


        existing = School.query.filter_by(
            school_code=school_code
        ).first()

        if existing:

            flash(
                "School code already exists",
                "error"
            )

            return redirect(
                url_for(
                    "manage_schools"
                )
            )

        school = School(

            school_code=school_code,

            name=name,

            email=email,

            phone=phone
        )

        db.session.add(school)

        db.session.commit()

        flash(
            "School added successfully",
            "success"
        )

        return redirect(
            url_for(
                "manage_schools"
            )
        )

    schools = School.query.order_by(
        School.id.desc()
    ).all()
    active_schools = School.query.filter_by(
        active=True
    ).count()

    inactive_schools = School.query.filter_by(
        active=False
    ).count()

    return render_template(
        "schools.html",
        schools=schools,
        active_schools=active_schools,
        inactive_schools=inactive_schools
    )


@app.route(
"/edit_school/[int:id](int:id)",
methods=["POST"])
@system_admin_required
def edit_school(id):


    school = School.query.get_or_404(id)

    school.school_code = request.form.get(
        "school_code"
    )

    school.name = request.form.get(
        "name"
    )

    school.email = request.form.get(
        "email"
    )

    school.phone = request.form.get(
        "phone"
    )

    db.session.commit()

    flash(
        "School updated successfully",
        "success"
    )

    return redirect(
        url_for(
            "manage_schools"
        )
    )

@app.route(
    "/delete_school/<int:id>",
    methods=["POST"]
)
@system_admin_required
def delete_school(id):

    school = School.query.get_or_404(id)

    db.session.delete(school)

    db.session.commit()

    flash(
        "School deleted successfully",
        "success"
    )

    return redirect(
        url_for(
            "manage_schools"
        )
    )

@app.route(
    "/toggle_school/<int:id>",
    methods=["POST"]
)
@system_admin_required
def toggle_school(id):

    school = School.query.get_or_404(id)

    school.active = not school.active

    db.session.commit()

    flash(
        "School status updated",
        "success"
    )

    return redirect(
        url_for(
            "manage_schools"
        )
    )

@app.route(
    "/school_admins",
    methods=["GET", "POST"]
)
@system_admin_required

def manage_school_admins():

    if request.method == "POST":

        school_id = request.form.get(
            "school_id"
        )

        username = request.form.get(
            "username"
        )

        password = request.form.get(
            "password"
        )

        existing = SchoolAdmin.query.filter_by(
            username=username
        ).first()

        if existing:

            flash(
                "Username already exists",
                "error"
            )

            return redirect(
                url_for(
                    "manage_school_admins"
                )
            )

        admin = SchoolAdmin(

            school_id=school_id,

            username=username,

            password_hash=generate_password_hash(
                password
            )
        )

        db.session.add(admin)

        db.session.commit()

        flash(
            "School admin created successfully",
            "success"
        )

        return redirect(
            url_for(
                "manage_school_admins"
            )
        )

    admins = SchoolAdmin.query.all()
    active_schools = SchoolAdmin.query.filter_by(
        active=True
    ).count()

    inactive_schools = SchoolAdmin.query.filter_by(
        active=False
    ).count() 
    schools = School.query.order_by(
        School.name
    ).all()

    return render_template(
        "school_admins.html",
        admins=admins,
        schools=schools,
        active_schools=active_schools,
        inactive_schools=inactive_schools
    )
@app.route(
    "/edit_school_admin/<int:id>",
    methods=["POST"]
)
@system_admin_required
def edit_school_admin(id):

    admin = SchoolAdmin.query.get_or_404(id)

    admin.username = request.form.get(
        "username"
    )


    admin.school_id = request.form.get(
        "school_id"
    )

    password = request.form.get(
        "password"
    )

    if password:

        admin.password_hash = (
            generate_password_hash(
                password
            )
        )

    db.session.commit()

    flash(
        "Admin updated"
    )

    return redirect(
        url_for(
            "manage_school_admins"
        )
    )

@app.route(
    "/delete_school_admin/<int:id>",
    methods=["POST"]
)
@system_admin_required
def delete_school_admin(id):

    admin = SchoolAdmin.query.get_or_404(id)

    db.session.delete(admin)

    db.session.commit()

    flash(
        "Admin deleted"
    )

    return redirect(
        url_for(
            "manage_school_admins"
        )
    )

@app.route(
    "/toggle_school_admin/<int:id>",
    methods=["POST"]
)
@system_admin_required
def toggle_school_admin(id):

    admin = SchoolAdmin.query.get_or_404(id)

    admin.active = not admin.active

    db.session.commit()

    flash(
        "Status updated"
    )

    return redirect(
        url_for(
            "manage_school_admins"
        )
    )

@app.route("/students/<int:school_id>")
@shared_access
def school_students(school_id):

    school = School.query.get_or_404(
        school_id
    )

    students = Student.query.filter_by(
        school_id=school.id
    ).order_by(
        Student.fullname
    ).all()

    total_students = len(students)

    active_count = Student.query.filter_by(
        school_id=school.id,
        active=True
    ).count()

    inactive_count = Student.query.filter_by(
        school_id=school.id,
        active=False
    ).count()

    return render_template(

        "school_students.html",

        school=school,

        students=students,

        total_students=total_students,

        active_count=active_count,

        inactive_count=inactive_count
    )

@app.route(
    "/students/add/<int:school_id>",
    methods=["POST"]
)
@shared_access
def add_student(school_id):

    school = School.query.get_or_404(
        school_id
    )

    admission_no = request.form.get(
        "admission_no"
    ).strip()

    fullname = request.form.get(
        "fullname"
    ).strip()

    grade = request.form.get(
        "grade"
    ).strip()

    password = request.form.get(
        "password"
    )

    if not all([admission_no, fullname, grade, password]):

        flash(
            "All fields are required.",
            "error"
        )

        return redirect(
            url_for(
                "school_students",
                school_id=school.id
            )
        )

    existing = Student.query.filter_by(

        school_id=school.id,

        admission_no=admission_no

    ).first()

    if existing:

        flash(
            "Admission number already exists.",
            "error"
        )

        return redirect(
            url_for(
                "school_students",
                school_id=school.id
            )
        )

    student = Student(

        school_id=school.id,

        admission_no=admission_no,

        fullname=fullname,

        grade=grade,

        password_hash=generate_password_hash(
            password
        )
    )

    db.session.add(student)

    db.session.commit()

    flash(
        "Student added successfully.",
        "success"
    )

    return redirect(
        url_for(
            "school_students",
            school_id=school.id
        )
    )

@app.route(
    "/students/edit/<int:id>",
    methods=["POST"]
)
@shared_access
def edit_student(id):

    student = Student.query.get_or_404(
        id
    )

    admission_no = request.form.get(
        "admission_no"
    ).strip()

    fullname = request.form.get(
        "fullname"
    ).strip()

    grade = request.form.get(
        "grade"
    ).strip()

    password = request.form.get(
        "password"
    )

    duplicate = Student.query.filter(

        Student.school_id == student.school_id,

        Student.admission_no == admission_no,

        Student.id != student.id

    ).first()

    if duplicate:

        flash(
            "Admission number already exists.",
            "error"
        )

        return redirect(
            url_for(
                "school_students",
                school_id=student.school_id
            )
        )

    student.admission_no = admission_no

    student.fullname = fullname

    student.grade = grade

    if password:

        student.password_hash = generate_password_hash(
            password
        )

    db.session.commit()

    flash(
        "Student updated successfully.",
        "success"
    )

    return redirect(
        url_for(
            "school_students",
            school_id=student.school_id
        )
    )

@app.route(
    "/students/toggle/<int:id>",
    methods=["POST"]
)
@shared_access
def toggle_student(id):

    student = Student.query.get_or_404(
        id
    )

    student.active = not student.active

    db.session.commit()

    if student.active:

        flash(
            "Student activated.",
            "success"
        )

    else:

        flash(
            "Student deactivated.",
            "warning"
        )

    return redirect(
        url_for(
            "school_students",
            school_id=student.school_id
        )
    )

@app.route(
    "/students/delete/<int:id>",
    methods=["POST"]
)
@shared_access
def delete_student(id):

    student = Student.query.get_or_404(
        id
    )

    school_id = student.school_id

    db.session.delete(student)

    db.session.commit()

    flash(
        "Student deleted successfully.",
        "success"
    )

    return redirect(
        url_for(
            "school_students",
            school_id=school_id
        )
    )

##########################################################
# MATERIAL MANAGEMENT
##########################################################

@app.route(

    "/materials",

    methods=["GET","POST"]

)
@system_admin_required
def manage_materials():

    ######################################################
    # UPLOAD MATERIAL
    ######################################################

    if request.method == "POST":

        title = request.form.get("title")

        description = request.form.get("description")

        subject = request.form.get("subject")

        grade = request.form.get("grade")

        active = request.form.get("active")

        schools = request.form.getlist("schools")

        uploaded_file = request.files.get("file")


        ##################################################
        # VALIDATION
        ##################################################

        if not title:

            flash(

                "Title is required",

                "error"

            )

            return redirect(

                url_for("manage_materials")

            )


        if not subject:

            flash(

                "Subject is required",

                "error"

            )

            return redirect(

                url_for("manage_materials")

            )


        if not grade:

            flash(

                "Grade is required",

                "error"

            )

            return redirect(

                url_for("manage_materials")

            )


        if not uploaded_file:

            flash(

                "Please choose a file",

                "error"

            )

            return redirect(

                url_for("manage_materials")

            )


        ##################################################
        # FILE VALIDATION
        ##################################################

        if uploaded_file.filename == "":

            flash(

                "No file selected",

                "error"

            )

            return redirect(

                url_for("manage_materials")

            )


        if not allowed_file(

            uploaded_file.filename

        ):

            flash(

                "Unsupported file type",

                "error"

            )

            return redirect(

                url_for("manage_materials")

            )


        ##################################################
        # GENERATE UNIQUE FILE NAME
        ##################################################

        extension = uploaded_file.filename.rsplit(

            ".",

            1

        )[1].lower()

        unique_name = (

            str(uuid.uuid4())

            + "."

            + extension

        )

        save_path = os.path.join(

            app.config["UPLOAD_FOLDER"],

            unique_name

        )

        uploaded_file.save(

            save_path

        )


        ##################################################
        # SAVE MATERIAL
        ##################################################

        material = Material(

            title=title,

            description=description,

            subject=subject,

            grade=grade,

            file_name=uploaded_file.filename,   # Original filename shown to users

            file_path=save_path,                 # Full server path

            active=True if active else False

        )

        db.session.add(

            material

        )

        db.session.flush()


        ##################################################
        # ASSIGN SCHOOLS
        ##################################################

        for school_id in schools:

            assignment = MaterialSchool(

                material_id=material.id,

                school_id=int(school_id)

            )

            db.session.add(

                assignment

            )


        db.session.commit()


        flash(

            "Material uploaded successfully.",

            "success"

        )

        return redirect(

            url_for("manage_materials")

        )


    ######################################################
    # DISPLAY MATERIALS
    ######################################################

    materials = Material.query.order_by(

        Material.uploaded_at.desc()

    ).all()

    schools = School.query.order_by(

        School.name

    ).all()

    total_materials = Material.query.count()

    active_materials = Material.query.filter_by(

        active=True

    ).count()

    inactive_materials = Material.query.filter_by(

        active=False

    ).count()

    return render_template(

        "materials.html",

        materials=materials,

        schools=schools,

        total_materials=total_materials,

        active_materials=active_materials,

        inactive_materials=inactive_materials

    )

from flask import jsonify

@app.route("/material_schools/<int:material_id>")
@system_admin_required
def material_schools(material_id):

    material = Material.query.get_or_404(material_id)

    schools = [
        {
            "id": assignment.school.id,
            "name": assignment.school.name
        }
        for assignment in material.assigned_schools
    ]

    return jsonify(schools)

@app.route(
    "/toggle_material/<int:id>",
    methods=["POST"]
)
@system_admin_required
def toggle_material(id):

    material = Material.query.get_or_404(id)

    # ==========================================
    # TOGGLE STATUS
    # ==========================================

    material.active = not material.active

    db.session.commit()

    if material.active:

        flash(
            "Material activated successfully.",
            "success"
        )

    else:

        flash(
            "Material deactivated successfully.",
            "warning"
        )

    return redirect(
        url_for("manage_materials")
    )



@app.route("/download_material/<int:id>")
@system_admin_required
def download_material(id):

    material = Material.query.get_or_404(id)

    print("=" * 60)
    print("FILE NAME :", material.file_name)
    print("FILE PATH :", material.file_path)
    print("EXISTS :", os.path.exists(material.file_path))
    print("=" * 60)

    return send_file(
        material.file_path,
        as_attachment=True
    )

from flask import jsonify


@app.route(
    "/get_material/<int:id>"
)
@system_admin_required
def get_material(id):

    material = Material.query.get_or_404(id)

    assigned_school_ids = [

        assignment.school_id

        for assignment in material.assigned_schools

    ]

    return jsonify({

        "id": material.id,

        "title": material.title,

        "description": material.description or "",

        "subject": material.subject,

        "grade": material.grade,

        "active": material.active,

        "schools": assigned_school_ids,

        "file_name": material.file_name

    })

@app.route(
    "/edit_material/<int:id>",
    methods=["POST"]
)
@system_admin_required
def edit_material(id):

    material = Material.query.get_or_404(id)

    ###################################################
    # BASIC DETAILS
    ###################################################

    material.title = request.form.get(
        "title"
    )

    material.description = request.form.get(
        "description"
    )

    material.subject = request.form.get(
        "subject"
    )

    material.grade = request.form.get(
        "grade"
    )

    material.active = (

        request.form.get("active")

        is not None

    )

    ###################################################
    # REPLACE FILE (OPTIONAL)
    ###################################################

    uploaded_file = request.files.get(
        "file"
    )

    if uploaded_file and uploaded_file.filename != "":

        if allowed_file(uploaded_file.filename):

            # Delete old file if it exists
            if (

                material.file_path

                and

                os.path.exists(material.file_path)

            ):

                os.remove(

                    material.file_path

                )

            extension = uploaded_file.filename.rsplit(

                ".",

                1

            )[1].lower()

            unique_name = (

                str(uuid.uuid4())

                + "."

                + extension

            )

            save_path = os.path.join(

                app.config["UPLOAD_FOLDER"],

                unique_name

            )

            uploaded_file.save(

                save_path

            )

            material.file_name = (

                uploaded_file.filename

            )

            material.file_path = (

                save_path

            )

        else:

            flash(

                "Unsupported file type.",

                "error"

            )

            return redirect(

                url_for(

                    "manage_materials"

                )

            )

    ###################################################
    # UPDATE SCHOOL ASSIGNMENTS
    ###################################################

    MaterialSchool.query.filter_by(

        material_id=material.id

    ).delete()

    selected_schools = request.form.getlist(

        "schools"

    )

    for school_id in selected_schools:

        db.session.add(

            MaterialSchool(

                material_id=material.id,

                school_id=int(school_id)

            )

        )

    ###################################################
    # SAVE
    ###################################################

    db.session.commit()

    flash(

        "Material updated successfully.",

        "success"

    )

    return redirect(

        url_for(

            "manage_materials"

        )

    )
import os

@app.route(
    "/delete_material/<int:id>",
    methods=["POST"]
)
@system_admin_required
def delete_material(id):

    material = Material.query.get_or_404(id)

    try:

        # ==========================================
        # DELETE PHYSICAL FILE
        # ==========================================

        if material.file_path:

            if os.path.exists(material.file_path):

                os.remove(material.file_path)

        # ==========================================
        # DELETE SCHOOL ASSIGNMENTS
        # ==========================================

        MaterialSchool.query.filter_by(
            material_id=material.id
        ).delete()

        # ==========================================
        # DELETE MATERIAL RECORD
        # ==========================================

        db.session.delete(material)

        db.session.commit()

        flash(
            "Material deleted successfully.",
            "success"
        )

    except Exception as e:

        db.session.rollback()

        flash(
            f"Error deleting material: {e}",
            "error"
        )

    return redirect(
        url_for("manage_materials")
    )

from functools import wraps

#########################################################
# STUDENT LOGIN REQUIRED
#########################################################

def student_login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        #################################################
        # Student Logged In?
        #################################################

        if "student_id" not in session:

            flash(
                "Please login to continue.",
                "warning"
            )

            return redirect(
                url_for("student_login")
            )

        #################################################
        # Student Still Exists?
        #################################################

        student = Student.query.get(
            session["student_id"]
        )

        if not student:

            session.clear()

            flash(
                "Your session has expired.",
                "warning"
            )

            return redirect(
                url_for("student_login")
            )

        #################################################
        # Student Active?
        #################################################

        if not student.active:

            session.clear()

            flash(
                "Your account has been deactivated.",
                "danger"
            )

            return redirect(
                url_for("student_login")
            )

        #################################################
        # School Still Exists?
        #################################################

        school = School.query.get(
            student.school_id
        )

        if not school:

            session.clear()

            flash(
                "School account not found.",
                "danger"
            )

            return redirect(
                url_for("student_login")
            )

        #################################################
        # School Active?
        #################################################

        if not school.active:

            session.clear()

            flash(
                "This school account has been disabled.",
                "danger"
            )

            return redirect(
                url_for("student_login")
            )

        #################################################

        return f(*args, **kwargs)

    return decorated_function

###########################################################
# STUDENT LOGIN
###########################################################

@app.route(
    "/student/login",
    methods=["GET", "POST"]
)
def student_login():

    # Already logged in
    if session.get("student_id"):

        return redirect(
            url_for("student_dashboard")
        )

    if request.method == "POST":

        school_code = request.form.get(
            "school_code",
            ""
        ).strip()

        admission_no = request.form.get(
            "admission_no",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        ####################################################
        # Validate School
        ####################################################

        school = School.query.filter_by(
            school_code=school_code
        ).first()

        if not school:

            flash(
                "Invalid school code.",
                "danger"
            )

            return redirect(
                url_for("student_login")
            )

        ####################################################
        # School Active?
        ####################################################

        if not school.active:

            flash(
                "This school account has been disabled.",
                "danger"
            )

            return redirect(
                url_for("student_login")
            )

        ####################################################
        # Find Student
        ####################################################

        student = Student.query.filter_by(

            school_id=school.id,

            admission_no=admission_no

        ).first()

        if not student:

            flash(
                "Invalid admission number.",
                "danger"
            )

            return redirect(
                url_for("student_login")
            )

        ####################################################
        # Student Active?
        ####################################################

        if not student.active:

            flash(
                "Your account has been deactivated. Contact your school administrator.",
                "danger"
            )

            return redirect(
                url_for("student_login")
            )

        ####################################################
        # Verify Password
        ####################################################

        if not check_password_hash(

            student.password_hash,

            password

        ):

            flash(
                "Incorrect password.",
                "danger"
            )

            return redirect(
                url_for("student_login")
            )

        ####################################################
        # LOGIN SUCCESS
        ####################################################

        session.clear()

        session["student_id"] = student.id

        session["school_id"] = school.id

        session["student_name"] = student.fullname

        session["school_name"] = school.name

        session["grade"] = student.grade

        flash(
            f"Welcome {student.fullname}!",
            "success"
        )

        return redirect(
            url_for("student_dashboard")
        )

    ########################################################

    return render_template(
        "students/login.html"
    )

from sqlalchemy import func

##########################################################
# STUDENT DASHBOARD
##########################################################

@app.route("/student/dashboard")
@student_login_required
def student_dashboard():

    #######################################################
    # Logged-in Student
    #######################################################

    student = Student.query.get_or_404(
        session["student_id"]
    )

    #######################################################
    # SCHOOL
    #######################################################

    school = student.school

    #######################################################
    # MATERIALS AVAILABLE
    #######################################################

    materials = (

        Material.query

        .join(
            MaterialSchool,
            Material.id == MaterialSchool.material_id
        )

        .filter(

            Material.active == True,

            Material.grade == student.grade,

            MaterialSchool.school_id == student.school_id

        )

        .order_by(
            Material.uploaded_at.desc()
        )

        .all()

    )

    materials_count = len(
        materials
    )

    #######################################################
    # SURVEYS AVAILABLE
    #######################################################

    surveys = (

        Survey.query

        .join(
            SurveySchool,
            Survey.id == SurveySchool.survey_id
        )

        .filter(

            Survey.active == True,
            Survey.grade == student.grade,
            SurveySchool.school_id == student.school_id

        )

        .all()

    )

    surveys_count = len(
        surveys
    )

    #######################################################
    # COMPLETED SURVEYS
    #######################################################

    completed = Result.query.filter_by(

        student_id=student.id

    ).count()

    #######################################################
    # PENDING SURVEYS
    #######################################################

    pending = max(

        surveys_count - completed,

        0

    )

    #######################################################
    # AVERAGE SCORE
    #######################################################

    average_score = (

        db.session.query(

            func.avg(
                Result.percentage
            )

        )

        .filter(

            Result.student_id == student.id

        )

        .scalar()

    )

    if average_score is None:

        average_score = 0

    average_score = round(
        average_score,
        1
    )

    #######################################################
    # HIGHEST SCORE
    #######################################################

    highest_score = (

        db.session.query(

            func.max(
                Result.percentage
            )

        )

        .filter(

            Result.student_id == student.id

        )

        .scalar()

    )

    if highest_score is None:

        highest_score = 0

    #######################################################
    # ATTENDANCE
    #######################################################

    if surveys_count == 0:

        attendance = 0

    else:

        attendance = round(

            (completed / surveys_count) * 100,

            1

        )

    #######################################################
    # RECENT RESULTS
    #######################################################

    recent_results = (

        Result.query

        .filter_by(

            student_id=student.id

        )

        .order_by(

            Result.id.desc()

        )

        .limit(5)

        .all()

    )

    #######################################################
    # RECENT MATERIALS
    #######################################################

    recent_materials = materials[:5]

    #######################################################
    # PASS EVERYTHING
    #######################################################

    return render_template(

        "students/dashboard.html",

        student=student,

        school=school,

        materials=materials,

        recent_materials=recent_materials,

        surveys=surveys,

        recent_results=recent_results,

        materials_count=materials_count,

        surveys_count=surveys_count,

        completed=completed,

        pending=pending,

        average_score=average_score,

        highest_score=highest_score,

        attendance=attendance

    )

#########################################################
# STUDENT LOGOUT
#########################################################

@app.route("/student/logout")
@student_login_required
def student_logout():

    session.pop("student_id", None)

    flash(
        "You have logged out successfully.",
        "success"
    )

    return redirect(
        url_for("student_login")
    )

#############################################################
# STUDENT READING MATERIALS
#############################################################

@app.route("/student/materials")
@student_login_required
def student_materials():

    student = Student.query.get_or_404(
        session["student_id"]
    )

    materials = (

        Material.query

        .join(
            MaterialSchool,
            Material.id == MaterialSchool.material_id
        )

        .filter(

            Material.active == True,

            Material.grade == student.grade,

            MaterialSchool.school_id == student.school_id

        )

        .order_by(
            Material.uploaded_at.desc()
        )

        .all()

    )

    return render_template(

        "students/materials.html",

        student=student,

        materials=materials

    )

#############################################################
# VERIFY STUDENT CAN ACCESS MATERIAL
#############################################################

def student_can_access_material(student, material):

    # Material must be active
    if not material.active:
        return False

    # Material must be assigned to student's school
    assignment = MaterialSchool.query.filter_by(
        material_id=material.id,
        school_id=student.school_id
    ).first()

    if assignment is None:
        return False

    return True

#############################################################
# MATERIAL VIEWER
#############################################################

@app.route("/student/material/<int:id>")
@student_login_required
def view_material(id):

    student = Student.query.get_or_404(
        session["student_id"]
    )

    material = Material.query.get_or_404(id)

    if not student_can_access_material(student, material):

        flash(
            "You are not authorized to access this material.",
            "danger"
        )

        return redirect(
            url_for("student_materials")
        )

    extension = material.file_name.rsplit(".", 1)[1].lower()

    return render_template(

        "students/viewer.html",

        student=student,

        material=material,

        extension=extension

    )

#############################################################
# STREAM MATERIAL
#############################################################

@app.route("/student/material/content/<int:id>")
@student_login_required
def material_content(id):

    student = Student.query.get_or_404(
        session["student_id"]
    )

    material = Material.query.get_or_404(id)

    if not student_can_access_material(student, material):

        abort(403)

    stored = material.file_path.replace("\\", "/")

    if "/" in stored:

        file_path = os.path.join(
            app.root_path,
            stored
        )

    else:

        file_path = os.path.join(
            app.root_path,
            app.config["UPLOAD_FOLDER"],
            stored
        )

    if not os.path.isfile(file_path):

        abort(404)

    return send_file(
        file_path,
        download_name=material.file_name,
        as_attachment=False
    )

#############################################################
# DOWNLOAD MATERIAL
#############################################################

@app.route("/student/material/download/<int:id>")
@student_login_required
def student_download_material(id):

    student = Student.query.get_or_404(
        session["student_id"]
    )

    material = Material.query.get_or_404(id)

    if not student_can_access_material(student, material):

        abort(403)

    stored = material.file_path.replace("\\", "/")

    if "/" in stored:

        file_path = os.path.join(
            app.root_path,
            stored
        )

    else:

        file_path = os.path.join(
            app.root_path,
            app.config["UPLOAD_FOLDER"],
            stored
        )

    if not os.path.isfile(file_path):

        abort(404)

    return send_file(

        file_path,

        download_name=material.file_name,

        as_attachment=True

    )

@app.route("/surveys", methods=["GET", "POST"])
@system_admin_required
def surveys():

    ####################################################
    # CREATE SURVEY
    ####################################################

    if request.method == "POST":

        title = request.form.get("title")
        description = request.form.get("description")
        subject = request.form.get("subject")
        grade = request.form.get("grade")
        duration = request.form.get("duration_minutes")
        instructions = request.form.get("instructions")
        passing = request.form.get("passing_percentage")
        attempts = request.form.get("attempts_allowed")
        active = request.form.get("active")

        school_ids = request.form.getlist("schools")

        ################################################
        # VALIDATION
        ################################################

        if not title:
            flash("Survey title is required.", "error")
            return redirect(url_for("surveys"))

        if not subject:
            flash("Subject is required.", "error")
            return redirect(url_for("surveys"))

        if not grade:
            flash("Grade is required.", "error")
            return redirect(url_for("surveys"))

        ################################################
        # SAVE SURVEY
        ################################################

        survey = Survey(

            title=title,

            description=description,

            subject=subject,

            grade=grade,

            duration_minutes=int(duration or 30),

            instructions=instructions,

            passing_percentage=int(passing or 40),

            attempts_allowed=int(attempts or 1),

            active=True if active else False

        )

        db.session.add(survey)

        db.session.flush()

        ################################################
        # ASSIGN SCHOOLS
        ################################################

        for school_id in school_ids:

            db.session.add(

                SurveySchool(

                    survey_id=survey.id,

                    school_id=int(school_id)

                )

            )

        db.session.commit()

        flash(

            "Survey created successfully.",

            "success"

        )

        return redirect(

            url_for("surveys")

        )

    ####################################################
    # DISPLAY PAGE
    ####################################################

    surveys = Survey.query.order_by(

        Survey.created_at.desc()

    ).all()

    schools = School.query.order_by(

        School.name

    ).all()

    return render_template(

        "admin/surveys.html",

        surveys=surveys,

        schools=schools

    )

@app.route("/survey/<int:id>/questions")
@system_admin_required
def survey_questions(id):

    survey = Survey.query.get_or_404(id)

    questions = Question.query.filter_by(
        survey_id=id
    ).order_by(
        Question.question_no
    ).all()

    return render_template(

        "admin/survey_questions.html",

        survey=survey,

        questions=questions

    )

@app.route("/survey/<int:id>/get")
@system_admin_required
def get_survey(id):

    survey = Survey.query.get_or_404(id)

    assigned = [

        item.school_id

        for item in survey.assigned_schools

    ]

    return jsonify({

        "id": survey.id,

        "title": survey.title,

        "description": survey.description,

        "subject": survey.subject,

        "grade": survey.grade,

        "duration_minutes": survey.duration_minutes,

        "instructions": survey.instructions,

        "passing_percentage": survey.passing_percentage,

        "attempts_allowed": survey.attempts_allowed,

        "active": survey.active,

        "schools": assigned

    })

@app.route("/survey/<int:id>/edit", methods=["POST"])
@system_admin_required
def edit_survey(id):

    survey = Survey.query.get_or_404(id)

    survey.title = request.form.get("title")

    survey.description = request.form.get("description")

    survey.subject = request.form.get("subject")

    survey.grade = request.form.get("grade")

    survey.duration_minutes = int(

        request.form.get("duration_minutes") or 30

    )

    survey.instructions = request.form.get(

        "instructions"

    )

    survey.passing_percentage = int(

        request.form.get(

            "passing_percentage"

        ) or 40

    )

    survey.attempts_allowed = int(

        request.form.get(

            "attempts_allowed"

        ) or 1

    )

    survey.active = True if request.form.get(

        "active"

    ) else False

    #################################################
    # UPDATE SCHOOLS
    #################################################

    SurveySchool.query.filter_by(

        survey_id=survey.id

    ).delete()

    for school_id in request.form.getlist(

        "schools"

    ):

        db.session.add(

            SurveySchool(

                survey_id=survey.id,

                school_id=int(school_id)

            )

        )

    db.session.commit()

    flash(

        "Survey updated successfully.",

        "success"

    )

    return redirect(

        url_for("surveys")

    )

@app.route("/survey/<int:id>/toggle", methods=["POST"])
@system_admin_required
def toggle_survey(id):

    survey = Survey.query.get_or_404(id)

    survey.active = not survey.active

    db.session.commit()

    flash(

        "Survey status updated.",

        "success"

    )

    return redirect(

        url_for("surveys")

    )

@app.route("/survey/<int:id>/delete", methods=["POST"])
@system_admin_required
def delete_survey(id):

    survey = Survey.query.get_or_404(id)

    db.session.delete(

        survey

    )

    db.session.commit()

    flash(

        "Survey deleted successfully.",

        "success"

    )

    return redirect(

        url_for("surveys")

    )

@app.route("/survey/<int:survey_id>/question/add", methods=["POST"])
@system_admin_required
def add_question(survey_id):

    survey = Survey.query.get_or_404(survey_id)

    ####################################################
    # NEXT QUESTION NUMBER
    ####################################################

    last_question = Question.query.filter_by(

        survey_id=survey.id

    ).order_by(

        Question.question_no.desc()

    ).first()

    next_number = 1

    if last_question:

        next_number = last_question.question_no + 1

    ####################################################
    # CREATE QUESTION
    ####################################################

    question = Question(

        survey_id=survey.id,

        question_no=next_number,

        question=request.form.get("question"),

        option_a=request.form.get("option_a"),

        option_b=request.form.get("option_b"),

        option_c=request.form.get("option_c"),

        option_d=request.form.get("option_d"),

        correct_answer=request.form.get(

            "correct_answer"

        )

    )

    db.session.add(question)

    db.session.commit()

    flash(

        "Question added successfully.",

        "success"

    )

    return redirect(

        url_for(

            "survey_questions",

            id=survey.id

        )

    )

@app.route("/question/<int:id>/get")
@system_admin_required
def get_question(id):

    question = Question.query.get_or_404(id)

    return jsonify({

        "id": question.id,

        "question": question.question,

        "option_a": question.option_a,

        "option_b": question.option_b,

        "option_c": question.option_c,

        "option_d": question.option_d,

        "correct_answer": question.correct_answer

    })

@app.route("/question/<int:id>/edit", methods=["POST"])
@system_admin_required
def edit_question(id):

    question = Question.query.get_or_404(id)

    question.question = request.form.get(

        "question"

    )

    question.option_a = request.form.get(

        "option_a"

    )

    question.option_b = request.form.get(

        "option_b"

    )

    question.option_c = request.form.get(

        "option_c"

    )

    question.option_d = request.form.get(

        "option_d"

    )

    question.correct_answer = request.form.get(

        "correct_answer"

    )

    db.session.commit()

    flash(

        "Question updated successfully.",

        "success"

    )

    return redirect(

        url_for(

            "survey_questions",

            id=question.survey_id

        )

    )

@app.route("/question/<int:id>/delete", methods=["POST"])
@system_admin_required
def delete_question(id):

    question = Question.query.get_or_404(id)

    survey_id = question.survey_id

    db.session.delete(question)

    db.session.commit()

    ####################################################
    # RENUMBER QUESTIONS
    ####################################################

    questions = Question.query.filter_by(

        survey_id=survey_id

    ).order_by(

        Question.question_no

    ).all()

    for index, q in enumerate(

        questions,

        start=1

    ):

        q.question_no = index

    db.session.commit()

    flash(

        "Question deleted successfully.",

        "success"

    )

    return redirect(

        url_for(

            "survey_questions",

            id=survey_id

        )

    )

from datetime import datetime

@app.route("/student/survey/<int:id>/start")
@student_login_required
def start_survey(id):

    ####################################################
    # LOAD STUDENT & SURVEY
    ####################################################

    student = Student.query.get_or_404(
        session["student_id"]
    )

    survey = Survey.query.get_or_404(id)

    ####################################################
    # SURVEY ACTIVE?
    ####################################################

    if not survey.active:

        flash(
            "This survey is currently unavailable.",
            "danger"
        )

        return redirect(
            url_for("student_dashboard")
        )

    ####################################################
    # CORRECT GRADE?
    ####################################################

    if survey.grade != student.grade:

        flash(
            "This survey is not assigned to your grade.",
            "danger"
        )

        return redirect(
            url_for("student_dashboard")
        )

    ####################################################
    # ASSIGNED TO SCHOOL?
    ####################################################

    assigned = SurveySchool.query.filter_by(

        survey_id=survey.id,

        school_id=student.school_id

    ).first()

    if not assigned:

        flash(
            "This survey is not assigned to your school.",
            "danger"
        )

        return redirect(
            url_for("student_dashboard")
        )

    ####################################################
    # ATTEMPTS USED
    ####################################################

    attempts_used = SurveyAttempt.query.filter_by(

        student_id=student.id,

        survey_id=survey.id,

        status="Completed"

    ).count()

    if attempts_used >= survey.attempts_allowed:

        flash(
            "You have exhausted all attempts for this survey.",
            "warning"
        )

        return redirect(
            url_for("student_dashboard")
        )

    ####################################################
    # RESUME EXISTING ATTEMPT
    ####################################################

    attempt = SurveyAttempt.query.filter_by(

        student_id=student.id,

        survey_id=survey.id,

        status="Started"

    ).first()

    if attempt:

        return redirect(

            url_for(

                "take_survey",

                attempt_id=attempt.id

            )

        )

    ####################################################
    # CREATE NEW ATTEMPT
    ####################################################

    attempt = SurveyAttempt(

        student_id=student.id,

        survey_id=survey.id,

        status="Started",

        started_at=datetime.utcnow()

    )

    db.session.add(attempt)

    db.session.commit()

    ####################################################
    # GO TO EXAM
    ####################################################

    return redirect(

        url_for(

            "take_survey",

            attempt_id=attempt.id

        )

    )

@app.route("/student/survey/attempt/<int:attempt_id>")
@student_login_required
def take_survey(attempt_id):

    attempt = SurveyAttempt.query.get_or_404(
        attempt_id
    )

    survey = Survey.query.get_or_404(
        attempt.survey_id
    )

    questions = Question.query.filter_by(

        survey_id=survey.id

    ).order_by(

        Question.question_no

    ).all()

    return render_template(

        "students/take_survey.html",

        attempt=attempt,

        survey=survey,

        questions=questions

    )

from datetime import datetime

@app.route(
    "/student/survey/<int:attempt_id>/submit",
    methods=["POST"]
)
@student_login_required
def submit_survey(attempt_id):

    ####################################################
    # LOAD ATTEMPT
    ####################################################

    attempt = SurveyAttempt.query.get_or_404(
        attempt_id
    )

    ####################################################
    # SECURITY
    ####################################################

    if attempt.student_id != session["student_id"]:

        abort(403)

    ####################################################
    # PREVENT DOUBLE SUBMISSION
    ####################################################

    if attempt.status == "Completed":

        flash(
            "This survey has already been submitted.",
            "warning"
        )

        return redirect(
            url_for("student_dashboard")
        )

    ####################################################
    # LOAD QUESTIONS
    ####################################################

    questions = Question.query.filter_by(

        survey_id=attempt.survey_id

    ).order_by(

        Question.question_no

    ).all()

    total_questions = len(questions)

    score = 0

    ####################################################
    # REMOVE OLD ANSWERS (SAFETY)
    ####################################################

    StudentAnswer.query.filter_by(

        student_id=attempt.student_id,

        survey_id=attempt.survey_id

    ).delete()

    ####################################################
    # MARK QUESTIONS
    ####################################################

    for question in questions:

        selected = request.form.get(

            f"q{question.id}"

        )

        correct = (

            selected == question.correct_answer

        )

        if correct:

            score += 1

        answer = StudentAnswer(

            student_id=attempt.student_id,

            survey_id=attempt.survey_id,

            question_id=question.id,

            selected_answer=selected,

            correct_answer=question.correct_answer,

            is_correct=correct

        )

        db.session.add(answer)

    ####################################################
    # CALCULATIONS
    ####################################################

    percentage = 0

    if total_questions > 0:

        percentage = round(

            (score / total_questions) * 100,

            2

        )

    completion = round(

        (
            sum(
                1 for q in questions
                if request.form.get(f"q{q.id}")
            ) / total_questions
        ) * 100,

        2

    ) if total_questions else 0

    ####################################################
    # GRADE
    ####################################################

    if percentage >= 80:

        grade = "A"

    elif percentage >= 70:

        grade = "B"

    elif percentage >= 60:

        grade = "C"

    elif percentage >= 50:

        grade = "D"

    else:

        grade = "E"

    ####################################################
    # REMOVE OLD RESULT
    ####################################################

    Result.query.filter_by(

        student_id=attempt.student_id,

        survey_id=attempt.survey_id

    ).delete()

    ####################################################
    # SAVE RESULT
    ####################################################

    result = Result(

        student_id=attempt.student_id,

        survey_id=attempt.survey_id,

        total_questions=total_questions,

        score=score,

        percentage=percentage,

        grade=grade,

        completion=completion,

        completed_at=datetime.utcnow()

    )

    db.session.add(result)

    ####################################################
    # UPDATE ATTEMPT
    ####################################################

    attempt.status = "Completed"

    attempt.submitted_at = datetime.utcnow()

    if attempt.started_at:

        attempt.time_taken = int(

            (
                attempt.submitted_at -

                attempt.started_at

            ).total_seconds()

        )

    db.session.commit()

    ####################################################
    # SHOW RESULT
    ####################################################

    return redirect(

        url_for(

            "student_result",

            survey_id=attempt.survey_id

        )

    )

@app.route("/student/result/<int:survey_id>")
@student_login_required
def student_result(survey_id):

    ####################################################
    # STUDENT
    ####################################################

    student = Student.query.get_or_404(
        session["student_id"]
    )

    ####################################################
    # RESULT
    ####################################################

    result = Result.query.filter_by(

        student_id=student.id,

        survey_id=survey_id

    ).first_or_404()

    ####################################################
    # SURVEY
    ####################################################

    survey = Survey.query.get_or_404(
        survey_id
    )
####################################################
# ATTEMPT INFORMATION
####################################################

    attempt = SurveyAttempt.query.filter_by(

        student_id=student.id,

        survey_id=survey.id

    ).first()

    ####################################################
    # ATTEMPTS USED
    ####################################################

    if attempt is None:

        used_attempts = 0

    else:

        try:

            used_attempts = int(attempt.attempt_number)

        except (TypeError, ValueError):

            used_attempts = 1

    ####################################################
    # ATTEMPTS ALLOWED
    ####################################################

    try:

        allowed_attempts = int(survey.attempts_allowed)

    except (TypeError, ValueError):

        allowed_attempts = 1

    ####################################################
    # REMAINING
    ####################################################

    remaining_attempts = allowed_attempts - used_attempts

    if remaining_attempts < 0:

        remaining_attempts = 0
    ####################################################
    # PERFORMANCE MESSAGE
    ####################################################

    if result.percentage >= 80:

        remark = "Excellent Performance 🎉"

    elif result.percentage >= 70:

        remark = "Very Good Work 👏"

    elif result.percentage >= 60:

        remark = "Good Job 👍"

    elif result.percentage >= 50:

        remark = "Fair Performance"

    else:

        remark = "Needs More Practice"

    ####################################################

    return render_template(

        "students/result.html",

        survey=survey,

        student=student,

        result=result,

        remark=remark,
        attempt=attempt,

        remaining_attempts=remaining_attempts

    )
    
@app.route("/student/survey/<int:survey_id>/retake")
@student_login_required
def retake_survey(survey_id):

    ####################################################
    # STUDENT
    ####################################################

    student = Student.query.get_or_404(
        session["student_id"]
    )

    ####################################################
    # SURVEY
    ####################################################

    survey = Survey.query.get_or_404(
        survey_id
    )

    ####################################################
    # ATTEMPT
    ####################################################

    attempt = SurveyAttempt.query.filter_by(

        student_id=student.id,

        survey_id=survey.id

    ).first_or_404()

    ####################################################
    # CHECK LIMIT
    ####################################################

    used_attempts = int(attempt.attempt_number or 1)

    allowed_attempts = int(survey.attempts_allowed or 1)

    if used_attempts >= allowed_attempts:

        flash(

            "Maximum attempts reached.",

            "warning"

        )

        return redirect(

            url_for(

                "student_result",

                survey_id=survey.id

            )

        )

    ####################################################
    # REMOVE OLD ANSWERS
    ####################################################

    StudentAnswer.query.filter_by(

        student_id=student.id,

        survey_id=survey.id

    ).delete()

    ####################################################
    # RESET ATTEMPT
    ####################################################

    attempt.status = "Started"

    attempt.started_at = datetime.utcnow()

    attempt.submitted_at = None

    attempt.time_taken = None

    attempt.attempt_number = used_attempts + 1

    ####################################################
    # REMOVE OLD RESULT
    ####################################################

    Result.query.filter_by(

        student_id=student.id,

        survey_id=survey.id

    ).delete()

    db.session.commit()

    ####################################################
    # START AGAIN
    ####################################################

    return redirect(

        url_for(

            "take_survey",

            attempt_id=attempt.id

        )

    )

@app.route("/student/surveys")
@student_login_required
def student_surveys():

    student = Student.query.get_or_404(
        session["student_id"]
    )

    surveys = Survey.query.join(
        SurveySchool,
        Survey.id == SurveySchool.survey_id
    ).filter(
        Survey.active == True,
        Survey.grade == student.grade,
        SurveySchool.school_id == student.school_id
    ).order_by(
        Survey.created_at.desc()
    ).all()

    survey_data = []

    for survey in surveys:

        attempt = SurveyAttempt.query.filter_by(
            student_id=student.id,
            survey_id=survey.id
        ).first()

        completed = False

        if attempt and attempt.status == "Completed":
            completed = True

        survey_data.append({
            "survey": survey,
            "completed": completed
        })

    return render_template(
        "students/surveys.html",
        survey_data=survey_data
    )

@app.route("/student/results")
@student_login_required
def student_results():

    student = Student.query.get_or_404(
        session["student_id"]
    )

    results = Result.query.filter_by(
        student_id=student.id

    ).order_by(

        Result.completed_at.desc()

    ).all()

    return render_template(

        "students/results.html",

        results=results

    )

from flask import request, session, redirect, url_for, flash, render_template
from werkzeug.security import check_password_hash

@app.route("/school/login", methods=["GET", "POST"])
def school_login():

    if request.method == "POST":

        school_code = request.form.get("school_code")
        username = request.form.get("username")
        password = request.form.get("password")

        # ------------------------------------
        # 1. FIND SCHOOL FIRST
        # ------------------------------------
        school = School.query.filter_by(school_code=school_code).first()
        
        if not school:
            flash("Invalid school code", "danger")
            return redirect(url_for("school_login"))
            
        if not school.active:

            flash("This school account has been disabled","danger")
            return redirect(url_for("school_login"))
        # ------------------------------------
        # 2. FIND ADMIN INSIDE SCHOOL
        # ------------------------------------
        admin = SchoolAdmin.query.filter_by(
            username=username,
            school_id=school.id
        ).first()

        if not admin:
            flash("Invalid username or password", "danger")
            return redirect(url_for("school_login"))
            
        if not admin.active:
            flash("your account suspended contact survitec 3d", "danger")
            return redirect(url_for("school_login"))
        # ------------------------------------
        # 3. CHECK PASSWORD
        # ------------------------------------
        if not check_password_hash(admin.password_hash, password):
            flash("Invalid username or password", "danger")
            return redirect(url_for("school_login"))

        # ------------------------------------
        # 4. SET SESSION
        # ------------------------------------
        session["school_admin_id"] = admin.id
        session["school_id"] = school.id

        flash("Login successful", "success")

        # ------------------------------------
        # 5. REDIRECT TO YOUR ROUTE
        # ------------------------------------
        return redirect(
            url_for("school_students", school_id=school.id)
        )

    return render_template("school/login.html")







# from sqlalchemy import text

# @app.route("/fix-survey-attempt-column")
# def fix_survey_attempt_column():

#     try:

#         ####################################################
#         # ADD attempt_number COLUMN
#         ####################################################

#         db.session.execute(text("""

#             ALTER TABLE survey_attempts

#             ADD COLUMN attempt_number INTEGER DEFAULT 1

#         """))

#         db.session.commit()

#         return "✅ attempt_number column added successfully."

#     except Exception as e:

#         db.session.rollback()

#         return f"⚠ {str(e)}"

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5050)),
        debug=True
    )
