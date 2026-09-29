
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session
)

import sqlite3

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database import get_db


auth_bp = Blueprint("auth", __name__)


# =========================================
# REGISTER
# =========================================

@auth_bp.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    error = None

    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not full_name:

            error = (
                "Please enter your full name."
            )

        elif not email:

            error = (
                "Please enter your email address."
            )

        elif not password:

            error = (
                "Please create a password."
            )

        elif len(password) < 6:

            error = (
                "Password must be at least 6 characters."
            )

        else:

            hashed_password = generate_password_hash(
                password
            )

            connection = get_db()

            try:

                connection.execute("""
                    INSERT INTO users
                    (
                        full_name,
                        email,
                        password
                    )
                    VALUES (?, ?, ?)
                """, (
                    full_name,
                    email,
                    hashed_password
                ))

                connection.commit()

                connection.close()

                return redirect(
                    url_for("auth.login")
                )

            except sqlite3.IntegrityError:

                connection.close()

                error = (
                    "An account with this email already exists. "
                    "Please use another email or sign in."
                )

    return render_template(
        "register.html",
        error=error
    )


# =========================================
# NORMAL USER LOGIN
# =========================================

@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()

        password = request.form["password"]

        connection = get_db()

        user = connection.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (
            email,
        )).fetchone()

        connection.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            # Clear previous authentication state
            session.pop(
                "user_id",
                None
            )

            session.pop(
                "admin_id",
                None
            )

            # Normal users are not administrators
            session["is_admin"] = 0

            # Establish normal user session
            session["user_id"] = user["id"]

            return redirect(
                url_for("user.dashboard")
            )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "login.html"
    )


# =========================================
# ADMIN LOGIN
# =========================================

@auth_bp.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()

        password = request.form["password"]

        connection = get_db()

        admin = connection.execute("""
            SELECT *
            FROM users
            WHERE email = ?
            AND is_admin = 1
        """, (
            email,
        )).fetchone()

        connection.close()

        if admin and check_password_hash(
            admin["password"],
            password
        ):

            # Clear normal user authentication
            session.pop(
                "user_id",
                None
            )

            session.pop(
                "admin_id",
                None
            )

            # Establish admin session
            session["admin_id"] = admin["id"]

            # Mark this session as administrator
            session["is_admin"] = 1

            session.pop(
                "admin_view_user_id",
                None
            )

            return redirect(
                url_for("admin.admin_dashboard")
            )

        return redirect(
            url_for("auth.admin_login")
        )

    return render_template(
        "admin_login.html"
    )


# =========================================
# ADMIN LOGOUT
# =========================================

@auth_bp.route("/admin/logout")
def admin_logout():

    session.pop(
        "admin_id",
        None
    )

    session.pop(
        "is_admin",
        None
    )

    session.pop(
        "admin_view_user_id",
        None
    )

    return redirect(
        url_for("auth.admin_login")
    )


# =========================================
# USER LOGOUT
# =========================================

@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("auth.login")
    )

