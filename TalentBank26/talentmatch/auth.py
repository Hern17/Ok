import sqlite3
from functools import wraps

from flask import redirect, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "role" not in session or session["role"] not in roles:
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def register_user(username, email, password, role):
    conn = get_db()
    cursor = conn.cursor()
    try:
        hashed = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
            (username, email, hashed, role),
        )  # noqa: E501
        user_id = cursor.lastrowid
        if role == "candidate":
            cursor.execute(
                "INSERT INTO candidates (user_id, full_name) VALUES (?, ?)",
                (user_id, username),
            )  # noqa: E501
        conn.commit()
        return user_id, None
    except sqlite3.IntegrityError as e:
        return None, str(e)
    finally:
        conn.close()


def login_user(username, password):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user["password"], password):
        return dict(user)
    return None
