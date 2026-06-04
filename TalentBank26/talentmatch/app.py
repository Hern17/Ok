import contextlib
import csv
import json
import os

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from ai_helper import (
    analyze_questionnaire,
    skill_gap_analysis,
    suggest_learning,
)
from auth import login_required, login_user, register_user, role_required
from db import get_db, init_db

app = Flask(__name__)
app.secret_key = "talentmatch-secret-key-2026"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {"pdf"}


@app.template_filter("fromjson")
def fromjson_filter(value):
    try:
        return json.loads(value)
    except:  # noqa: E722
        return []


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = login_user(username, password)
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password", "danger")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        user_id, error = register_user(username, email, password, role)
        if user_id:
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        flash(f"Registration failed: {error}", "danger")
    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    role = session["role"]
    if role == "candidate":
        return redirect(url_for("candidate_dashboard"))
    elif role == "employer":
        return redirect(url_for("employer_dashboard"))
    elif role == "university":
        return redirect(url_for("university_dashboard"))
    return redirect(url_for("login"))


@app.route("/candidate/dashboard")
@login_required
@role_required("candidate")
def candidate_dashboard():
    conn = get_db()
    candidate = conn.execute(
        "SELECT * FROM candidates WHERE user_id = ?", (session["user_id"],)
    ).fetchone()
    conn.close()
    if candidate and candidate["questionnaire_completed"]:
        return redirect(url_for("candidate_results"))
    return redirect(url_for("candidate_questionnaire"))


@app.route("/candidate/questionnaire")
@login_required
@role_required("candidate")
def candidate_questionnaire():
    conn = get_db()
    candidate = conn.execute(
        "SELECT * FROM candidates WHERE user_id = ?", (session["user_id"],)
    ).fetchone()
    conn.close()
    from cv_renderer import get_questionnaire_schema

    schema = get_questionnaire_schema()
    schema["sections"] = [s for s in schema["sections"] if s["type"] != "personality"]
    schema["sections"].append(
        {
            "id": "personality",
            "title": "Work Personality",
            "icon": "🧠",
            "type": "personality",
            "questions": [],
        }
    )
    questions_json = json.dumps(schema)
    prefill = {}
    if candidate and candidate["questionnaire_data"]:
        with contextlib.suppress(BaseException):
            prefill = json.loads(candidate["questionnaire_data"])
    return render_template(
        "candidate_questionnaire.html",
        questions_json=questions_json,
        prefill_json=json.dumps(prefill),
    )


@app.route("/candidate/save_questionnaire", methods=["POST"])
@login_required
@role_required("candidate")
def candidate_save_questionnaire():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data received"}), 400
    skills = data.get("skills", [])
    full_name = data.get("full_name", "")
    title = data.get("title", "")
    about = data.get("about", "")
    data.get("target_role", "")
    conn = get_db()
    conn.execute(
        "UPDATE candidates SET full_name=?, title=?, about=?, skills=?, questionnaire_data=?, questionnaire_completed=1 WHERE user_id=?",
        (
            full_name,
            title,
            about,
            json.dumps(skills),
            json.dumps(data),
            session["user_id"],
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/candidate/results")
@login_required
@role_required("candidate")
def candidate_results():
    conn = get_db()
    candidate = conn.execute(
        "SELECT * FROM candidates WHERE user_id = ?", (session["user_id"],)
    ).fetchone()
    conn.close()
    if not candidate or not candidate["questionnaire_completed"]:
        return redirect(url_for("candidate_questionnaire"))
    qdata = (
        json.loads(candidate["questionnaire_data"])
        if candidate["questionnaire_data"]
        else {}
    )
    analysis = analyze_questionnaire(qdata)
    certifications = (
        json.loads(candidate["certifications"]) if candidate["certifications"] else []
    )
    return render_template(
        "candidate_results.html",
        analysis=analysis,
        about=candidate["about"],
        username=session["username"],
        certifications=certifications,
        qdata=qdata,
    )


@app.route("/candidate/occupations")
@login_required
@role_required("candidate")
def candidate_occupations():
    titles = []
    csv_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "occupations.csv"
    )
    if os.path.exists(csv_path):
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                titles.append(row["title"])
    return jsonify(titles)


@app.route("/candidate/upload", methods=["POST"])
@login_required
@role_required("candidate")
def candidate_upload():
    is_ajax = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.accept_mimetypes.accept_json
    )
    if "cert" not in request.files:
        if is_ajax:
            return jsonify({"success": False, "error": "No file uploaded"}), 400
        flash("No file uploaded", "danger")
        return redirect(url_for("candidate_dashboard"))
    file = request.files["cert"]
    if file.filename == "" or not allowed_file(file.filename):
        if is_ajax:
            return jsonify({"success": False, "error": "Please upload a PDF file"}), 400
        flash("Please upload a PDF file", "danger")
        return redirect(url_for("candidate_dashboard"))
    filename = secure_filename(f"{session['user_id']}_{file.filename}")
    filepath = "uploads/" + filename
    file.save(filepath)
    from ai_helper import extract_cert_data
    cert_data = extract_cert_data(filepath)
    skills = cert_data["skills"]
    conn = get_db()
    existing = conn.execute(
        "SELECT skills, certifications FROM candidates WHERE user_id = ?",
        (session["user_id"],),
    ).fetchone()
    current_skills = (
        json.loads(existing["skills"]) if existing and existing["skills"] else []
    )
    current_certs = (
        json.loads(existing["certifications"])
        if existing and existing["certifications"]
        else []
    )
    new_cert = {"name": filename, "path": filepath, "skills": skills}
    merged_skills = list(set(current_skills + skills))
    current_certs.append(new_cert)
    conn.execute(
        "UPDATE candidates SET skills = ?, certifications = ? WHERE user_id = ?",
        (json.dumps(merged_skills), json.dumps(current_certs), session["user_id"]),
    )
    conn.commit()
    conn.close()
    if is_ajax:
        return jsonify({
            "success": True,
            "skills": cert_data["skills"],
            "cert_name": filename,
            "project_name": cert_data["project_name"],
            "project_type": cert_data["project_type"],
            "project_achievements": cert_data["project_achievements"],
            "project_duration": cert_data["project_duration"],
            "leadership_organisation": cert_data["leadership_organisation"],
            "leadership_role": cert_data["leadership_role"],
            "leadership_note": cert_data["leadership_note"],
            "leadership_duration": cert_data["leadership_duration"],
        })
    flash(f"Certification processed! Skills detected: {', '.join(skills)}", "success")
    return redirect(url_for("candidate_dashboard"))


@app.route("/candidate/skill_gap", methods=["POST"])
@login_required
@role_required("candidate")
def candidate_skill_gap():
    target_role = request.form.get("target_role", "")
    conn = get_db()
    candidate = conn.execute(
        "SELECT skills FROM candidates WHERE user_id = ?", (session["user_id"],)
    ).fetchone()
    conn.close()
    current_skills = (
        json.loads(candidate["skills"]) if candidate and candidate["skills"] else []
    )
    analysis = skill_gap_analysis(current_skills, target_role)
    return jsonify(analysis)


@app.route("/candidate/learning", methods=["POST"])
@login_required
@role_required("candidate")
def candidate_learning():
    conn = get_db()
    candidate = conn.execute(
        "SELECT skills FROM candidates WHERE user_id = ?", (session["user_id"],)
    ).fetchone()
    conn.close()
    current_skills = (
        json.loads(candidate["skills"]) if candidate and candidate["skills"] else []
    )
    suggestions = suggest_learning(current_skills)
    return jsonify(suggestions)


@app.route("/candidate/download_cv")
@app.route("/candidate/download_cv/<fmt>")
@login_required
@role_required("candidate")
def candidate_download_cv(fmt="pdf"):
    import subprocess

    conn = get_db()
    candidate = conn.execute(
        "SELECT * FROM candidates WHERE user_id = ?", (session["user_id"],)
    ).fetchone()
    conn.close()
    if not candidate:
        flash("Profile not found", "danger")
        return redirect(url_for("candidate_dashboard"))
    certs = (
        json.loads(candidate["certifications"]) if candidate["certifications"] else []
    )
    qdata = (
        json.loads(candidate["questionnaire_data"])
        if candidate["questionnaire_data"]
        else {}
    )
    from cv_renderer import generate_cv

    analysis = analyze_questionnaire(qdata) if qdata else None

    if fmt == "txt":
        content = generate_cv(candidate, certs, analysis=analysis, fmt="txt")
        path = f"uploads/cv_{session['user_id']}.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return send_file(
            path, as_attachment=True, download_name=f"{session['username']}_CV.txt"
        )

    if fmt == "typst":
        content = generate_cv(candidate, certs, analysis=analysis, fmt="typst")
        path = f"uploads/cv_{session['user_id']}.typ"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return send_file(
            path, as_attachment=True, download_name=f"{session['username']}_CV.typ"
        )

    content = generate_cv(candidate, certs, analysis=analysis, fmt="typst")
    typ_path = f"uploads/cv_{session['user_id']}.typ"
    pdf_path = f"uploads/cv_{session['user_id']}.pdf"
    with open(typ_path, "w", encoding="utf-8") as f:
        f.write(content)
    try:
        subprocess.run(
            ["typst", "compile", typ_path, pdf_path],
            check=True,
            capture_output=True,
            timeout=30,
        )
        return send_file(
            pdf_path, as_attachment=True, download_name=f"{session['username']}_CV.pdf"
        )
    except Exception:
        return send_file(
            typ_path, as_attachment=True, download_name=f"{session['username']}_CV.typ"
        )


@app.route("/employer/dashboard")
@login_required
@role_required("employer")
def employer_dashboard():
    conn = get_db()
    jobs = conn.execute(
        "SELECT * FROM jobs WHERE employer_id = ? ORDER BY created_at DESC",
        (session["user_id"],),
    ).fetchall()
    conn.close()
    return render_template("employer_dashboard.html", jobs=jobs)


@app.route("/employer/post_job", methods=["POST"])
@login_required
@role_required("employer")
def employer_post_job():
    title = request.form.get("title", "")
    company = request.form.get("company", "")
    description = request.form.get("description", "")
    skills_raw = request.form.get("skills", "")
    skills_list = [s.strip() for s in skills_raw.split(",") if s.strip()]
    conn = get_db()
    conn.execute(
        "INSERT INTO jobs (employer_id, title, company, description, required_skills) VALUES (?, ?, ?, ?, ?)",
        (session["user_id"], title, company, description, json.dumps(skills_list)),
    )
    conn.commit()
    conn.close()
    flash("Job posted successfully!", "success")
    return redirect(url_for("employer_dashboard"))


@app.route("/employer/matches/<int:job_id>")
@login_required
@role_required("employer")
def employer_matches(job_id):
    conn = get_db()
    job = conn.execute(
        "SELECT * FROM jobs WHERE id = ? AND employer_id = ?",
        (job_id, session["user_id"]),
    ).fetchone()
    if not job:
        conn.close()
        flash("Job not found", "danger")
        return redirect(url_for("employer_dashboard"))
    required_skills = (
        json.loads(job["required_skills"]) if job["required_skills"] else []
    )
    candidates = conn.execute(
        "SELECT c.*, u.username FROM candidates c JOIN users u ON c.user_id = u.id"
    ).fetchall()
    view_type = request.args.get("view", "table")
    matches = []
    for cand in candidates:
        cand_skills = json.loads(cand["skills"]) if cand["skills"] else []
        score = 0
        if required_skills and cand_skills:
            overlap = len(set(cand_skills) & set(required_skills))
            score = round((overlap / len(required_skills)) * 100, 1)
        existing = conn.execute(
            "SELECT * FROM matches WHERE job_id = ? AND candidate_id = ?",
            (job_id, cand["id"]),
        ).fetchone()
        matches.append(
            {
                "candidate_id": cand["id"],
                "name": cand["full_name"] or cand["username"],
                "title": cand["title"] or "",
                "skills": cand_skills,
                "score": score,
                "status": existing["status"] if existing else "pending",
                "match_id": existing["id"] if existing else None,
            }
        )
    matches.sort(key=lambda x: x["score"], reverse=True)
    conn.close()
    return render_template(
        "employer_matches.html", job=job, matches=matches, view_type=view_type
    )


@app.route("/employer/update_match", methods=["POST"])
@login_required
@role_required("employer")
def employer_update_match():
    data = request.get_json()
    job_id = data["job_id"]
    candidate_id = data["candidate_id"]
    status = data["status"]
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM matches WHERE job_id = ? AND candidate_id = ?",
        (job_id, candidate_id),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE matches SET status = ? WHERE id = ?", (status, existing["id"])
        )
    else:
        conn.execute(
            "INSERT INTO matches (job_id, candidate_id, employer_id, status) VALUES (?, ?, ?, ?)",
            (job_id, candidate_id, session["user_id"], status),
        )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/university/dashboard")
@login_required
@role_required("university")
def university_dashboard():
    conn = get_db()
    jobs = conn.execute(
        "SELECT * FROM jobs ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    matches = conn.execute(
        "SELECT m.*, j.title as job_title, j.required_skills, j.company, c.full_name as candidate_name, c.skills as candidate_skills FROM matches m JOIN jobs j ON m.job_id = j.id JOIN candidates c ON m.candidate_id = c.id ORDER BY m.created_at DESC"
    ).fetchall()
    all_skills = {}
    for job in jobs:
        skills = json.loads(job["required_skills"]) if job["required_skills"] else []
        for s in skills:
            all_skills[s] = all_skills.get(s, 0) + 1
    top_skills = sorted(all_skills.items(), key=lambda x: x[1], reverse=True)[:10]
    accepted = sum(1 for m in matches if m["status"] == "accepted")
    rejected = sum(1 for m in matches if m["status"] == "rejected")
    pending = sum(1 for m in matches if m["status"] == "pending")
    total_jobs = len(jobs)
    alerts = conn.execute(
        "SELECT * FROM university_alerts WHERE university_id = ? ORDER BY created_at DESC LIMIT 5",
        (session["user_id"],),
    ).fetchall()
    if total_jobs > 0 and not alerts:
        alert_skills = ", ".join([s for s, _ in top_skills[:3]])
        conn.execute(
            "INSERT INTO university_alerts (university_id, message, alert_type) VALUES (?, ?, ?)",
            (
                session["user_id"],
                f"Top in-demand skills: {alert_skills}. Consider updating curriculum.",
                "warning",
            ),
        )
        conn.commit()
        alerts = conn.execute(
            "SELECT * FROM university_alerts WHERE university_id = ? ORDER BY created_at DESC LIMIT 5",
            (session["user_id"],),
        ).fetchall()
    conn.close()
    return render_template(
        "university_dashboard.html",
        top_skills=top_skills,
        total_jobs=total_jobs,
        accepted=accepted,
        rejected=rejected,
        pending=pending,
        alerts=alerts,
        matches=matches,
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
