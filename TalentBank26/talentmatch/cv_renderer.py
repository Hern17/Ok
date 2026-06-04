import contextlib
import os

import yaml

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _load_yaml(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def get_questionnaire_schema():
    template = _load_yaml("cv_template.yaml")
    schema = {
        "skill_pool": template.get("skill_pool", []),
        "personality_questions": template.get("personality_questions", []),
        "sections": [],
    }
    for sec in template.get("sections", []):
        q = sec.get("questionnaire", [])
        has_questions = bool(q) or sec.get("type") in ("personality",)
        if has_questions:
            schema["sections"].append(
                {
                    "id": sec["id"],
                    "title": sec.get("label", ""),
                    "icon": sec.get("icon", ""),
                    "type": sec.get("type", ""),
                    "questions": q,
                }
            )
    return schema


# ── Data Builder ──────────────────────────────


def _build_user_data(profile, certifications, analysis):
    import json

    if profile is not None and not isinstance(profile, dict):
        profile = dict(profile)
    skills = analysis.get("skills", []) if analysis else []
    if not skills and profile and profile["skills"]:
        skills = (
            json.loads(profile["skills"])
            if isinstance(profile["skills"], str)
            else profile["skills"]
        )
    cert_list = []
    for c in certifications:
        if c is not None and not isinstance(c, dict):
            c = dict(c)
        cert_list.append(
            {"file": c.get("name", ""), "skills": ", ".join(c.get("skills", []))}
        )
    qdata = {}
    if profile and profile.get("questionnaire_data"):
        with contextlib.suppress(BaseException):
            qdata = (
                json.loads(profile["questionnaire_data"])
                if isinstance(profile["questionnaire_data"], str)
                else profile["questionnaire_data"]
            )
    profile_name = profile.get("full_name", "") if profile else ""
    profile_title = profile.get("title", "") if profile else ""
    profile_about = profile.get("about", "") if profile else ""
    data = {
        "name": qdata.get("full_name", profile_name),
        "title": qdata.get("title", profile_title),
        "email": qdata.get("email", ""),
        "mobile": qdata.get("mobile", ""),
        "location": qdata.get("location", ""),
        "social_media": qdata.get("social_media", ""),
        "about": qdata.get("about", profile_about),
        "experience": qdata.get("experience", "entry"),
        "skills": skills,
        "certifications": cert_list,
        "education": qdata.get("education", []),
        "work_experience": qdata.get("work_experience", []),
        "leadership": qdata.get("leadership", []),
        "projects": qdata.get("projects", []),
        "target_role": qdata.get("target_role", ""),
        "industry": qdata.get("industry", "technology"),
        "work_style": qdata.get("work_style", ""),
    }
    return data


# ── Typst Renderer ────────────────────────────


def _esc(text):
    if not text:
        return ""
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("#", "\\#")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


def _render_typst(data, meta, sections):
    lines = []
    lines.append(
        f'#set text(font: "{meta.get("font", "Libertinus Serif")}", size: {meta.get("font_size", "11pt")})'  # noqa: E501
    )
    lines.append(
        f'#show heading: set text(font: "{meta.get("font", "Libertinus Serif")}")'
    )
    lines.append("#show link: underline")
    mx, my = meta.get("margin_x", "0.9cm"), meta.get("margin_y", "1.3cm")
    lines.append(f"#set page(margin: (x: {mx}, y: {my}))")
    lines.append("#set par(justify: true)")
    lines.append("")
    lines.append("#let chiline() = { v(-3pt); line(length: 100%); v(-5pt) }")
    lines.append(
        '#let lastupdated(date) = { h(1fr); text("Last Updated in " + date, fill: gray) }'  # noqa: E501
    )
    lines.append("")
    # ── Render name + contact line ──
    name = data.get("name", "Your Name")
    contact_parts = [data.get(k) for k in ("email", "mobile", "location") if data.get(k)]
    contact_line = "  |  ".join(contact_parts) if contact_parts else ""
    lines.append(f"= {_esc(name)}")
    if contact_line:
        lines.append(f"{_esc(contact_line)} \\")
    if data.get("title"):
        lines.append(f"{_esc(data['title'])} \\")
    if data.get("social_media"):
        for line in data["social_media"].strip().split("\n"):
            if line.strip():
                lines.append(f"{_esc(line.strip())} \\")
    lines.append("")

    for sec in sections:
        stype = sec.get("type")
        sid = sec.get("id", "")
        slabel = sec.get("label", "")

        if stype == "header" or stype == "career" or stype == "personality":
            continue

        if stype == "text":
            text = data.get(sid, "") or data.get(
                sec.get("questionnaire", [{}])[0].get("key", ""), ""
            )
            if not text:
                continue
            lines.append(f"== {_esc(slabel)}")
            lines.append("#chiline()")
            lines.append("")
            lines.append(f"{_esc(text)}")
            lines.append("")
            continue

        if stype == "tags":
            items = data.get("skills", [])
            if not items:
                continue
            lines.append(f"== {_esc(slabel)}")
            lines.append("#chiline()")
            lines.append("")
            line = ", ".join([f"*{_esc(s)}*" for s in items])
            lines.append(line)
            lines.append("")
            continue

        if stype == "list":
            items = data.get("certifications", [])
            if not items:
                continue
            lines.append(f"== {_esc(slabel)}")
            lines.append("#chiline()")
            lines.append("")
            for item in items:
                label = item.get("file", item.get("name", ""))
                lines.append(f"- {_esc(label)}")
            lines.append("")
            continue

        if stype == "entries":
            entries = data.get(sid, [])
            if not entries:
                continue
            lines.append(f"== {_esc(slabel)}")
            lines.append("#chiline()")
            lines.append("")
            fields = (
                sec.get("questionnaire", [{}])[0].get("fields", [])
                if sec.get("questionnaire")
                else []
            )
            for entry in entries:
                name_k = next((f["key"] for f in fields if f["key"] in ("institution", "organisation", "name")), (fields[0]["key"] if fields else "name"))
                date_k = next((f["key"] for f in fields if f["key"] in ("duration", "dates")), None)
                role_k = next((f["key"] for f in fields if f["key"] in ("role", "course")), None)
                nv = _esc(entry.get(name_k, ""))
                rv = _esc(entry.get(role_k, "")) if role_k else ""
                dv = _esc(entry.get(date_k, "")) if date_k else ""
                if rv:
                    lines.append(f"*{nv}* — {rv} #h(1fr) {dv} \\")
                else:
                    lines.append(f"*{nv}* #h(1fr) {dv} \\")
                for f in fields:
                    k = f["key"]
                    if k in (name_k, role_k, date_k) or not entry.get(k):
                        continue
                    raw = entry[k]
                    if isinstance(raw, list):
                        for b in raw:
                            if b.strip():
                                lines.append(f"- {_esc(b)}")
                    elif f["type"] == "textarea":
                        for line in str(raw).strip().split("\n"):
                            line = line.strip()
                            if line:
                                lines.append(f"- {_esc(line)}")
                    else:
                        label = f["label"].replace(" (optional)", "").replace(" (comma separated)", "")
                        val = _esc(str(raw).strip())
                        if val:
                            lines.append(f"*{label}*: {val} \\")
                lines.append("")
            continue

    lines.append(f'#lastupdated("{data.get("_today", "today")}")')
    return "\n".join(lines)


# ── TXT Renderer ──────────────────────────────


def _render_txt(data, sections):
    lines = []
    width = 60
    name = data.get("name", "Your Name")
    lines.append(f"{'=' * width}")
    lines.append(f"    {name}")
    lines.append(f"{'=' * width}")
    if data.get("title"):
        lines.append(f"{data['title']}")
    contact_parts = [data.get(k) for k in ("email", "mobile", "location") if data.get(k)]
    if contact_parts:
        lines.append("  ".join(contact_parts))
    if data.get("social_media"):
        for line in data["social_media"].strip().split("\n"):
            if line.strip():
                lines.append(f"  {line.strip()}")
    lines.append("")

    for sec in sections:
        stype = sec.get("type")
        sid = sec.get("id", "")
        slabel = sec.get("label", "")

        if stype in ("header", "career", "personality"):
            continue

        if stype == "text":
            text = data.get(sid, "")
            if not text:
                continue
            lines.append(f"--- {slabel} ---")
            lines.append(f"{text}")
            lines.append("")
            continue

        if stype == "tags":
            items = data.get("skills", [])
            if not items:
                continue
            lines.append(f"--- {slabel} ---")
            for s in items:
                lines.append(f"  - {s}")
            lines.append("")
            continue

        if stype == "list":
            items = data.get("certifications", [])
            if not items:
                continue
            lines.append(f"--- {slabel} ---")
            for item in items:
                label = item.get("file", item.get("name", ""))
                lines.append(f"  - {label}")
            lines.append("")
            continue

        if stype == "entries":
            entries = data.get(sid, [])
            if not entries:
                continue
            lines.append(f"--- {slabel} ---")
            fields = (
                sec.get("questionnaire", [{}])[0].get("fields", [])
                if sec.get("questionnaire")
                else []
            )
            for entry in entries:
                name_k = next((f["key"] for f in fields if f["key"] in ("institution", "organisation", "name")), (fields[0]["key"] if fields else "name"))
                date_k = next((f["key"] for f in fields if f["key"] in ("duration", "dates")), None)
                role_k = next((f["key"] for f in fields if f["key"] in ("role", "course")), None)
                nv = entry.get(name_k, "")
                rv = entry.get(role_k, "") if role_k else ""
                dv = entry.get(date_k, "") if date_k else ""
                if rv:
                    lines.append(f"  {nv} — {rv} ({dv})")
                else:
                    lines.append(f"  {nv} ({dv})")
                for f in fields:
                    k = f["key"]
                    if k in (name_k, role_k, date_k) or not entry.get(k):
                        continue
                    raw = entry[k]
                    if isinstance(raw, list):
                        for b in raw:
                            if b.strip():
                                lines.append(f"    - {b}")
                    else:
                        for line in str(raw).strip().split("\n"):
                            line = line.strip()
                            if line:
                                lines.append(f"    - {line}")
                lines.append("")
            continue

    lines.append("Generated by TalentMatch AI")
    return "\n".join(lines)


# ── Public API ─────────────────────────────────


def generate_cv(profile, certifications, analysis=None, fmt="txt"):
    template = _load_yaml("cv_template.yaml")
    meta = template.get("meta", {})
    sections = template.get("sections", [])
    data = _build_user_data(profile, certifications, analysis)
    from datetime import date

    data["_today"] = date.today().strftime("%b %d, %Y")

    if fmt == "typst":
        return _render_typst(data, meta, sections)
    return _render_txt(data, sections)
