import json
import os
import random
import re

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


SKILL_KEYWORDS = {
    "python": [
        "Python",
        "Django",
        "Flask",
        "pandas",
        "numpy",
        "FastAPI",
        "PyTorch",
        "TensorFlow",
    ],
    "javascript": [
        "JavaScript",
        "React",
        "Vue",
        "Angular",
        "Node.js",
        "TypeScript",
        "jQuery",
    ],
    "java": ["Java", "Spring Boot", "Hibernate", "Maven", "Gradle"],
    "data": [
        "SQL",
        "Machine Learning",
        "Data Analysis",
        "Tableau",
        "Power BI",
        "Statistics",
    ],
    "web": ["HTML", "CSS", "Responsive Design", "REST API", "GraphQL"],
    "devops": ["Docker", "Kubernetes", "AWS", "Azure", "CI/CD", "Linux"],
    "mobile": ["Android", "iOS", "React Native", "Flutter", "Kotlin", "Swift"],
    "soft": [
        "Communication",
        "Teamwork",
        "Leadership",
        "Problem Solving",
        "Time Management",
    ],
}


def extract_skills_mock(filename):
    all_skills = []
    for category, skills in SKILL_KEYWORDS.items():
        all_skills.extend(skills)
    count = random.randint(3, 6)
    return random.sample(all_skills, min(count, len(all_skills)))


def extract_cert_data(filepath):
    import PyPDF2

    result = {
        "skills": [],
        "project_name": "",
        "project_type": "personal",
        "project_achievements": "",
        "project_duration": "",
        "leadership_organisation": "",
        "leadership_role": "",
        "leadership_note": "",
        "leadership_duration": "",
    }

    try:
        reader = PyPDF2.PdfReader(filepath)
        lines = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                for line in text.split("\n"):
                    stripped = line.strip()
                    if stripped and len(stripped) > 3:
                        lines.append(stripped)
    except Exception:
        all_skills = [s for cat in SKILL_KEYWORDS.values() for s in cat]
        result["skills"] = random.sample(all_skills, min(3, len(all_skills)))
        result["project_name"] = os.path.splitext(os.path.basename(filepath))[0]
        result["project_achievements"] = "Certification details extracted from PDF."
        result["project_duration"] = "2025"
        return result

    if not lines:
        return result

    full_text = " ".join(lines).lower()

    # ── Extract skills ──
    all_skills_map = {}
    for cat_skills in SKILL_KEYWORDS.values():
        for s in cat_skills:
            all_skills_map[s.lower()] = s
    found_skills = []
    for sk_lower, sk_orig in all_skills_map.items():
        if sk_lower in full_text:
            found_skills.append(sk_orig)
    if not found_skills:
        all_skills = list(all_skills_map.values())
        found_skills = random.sample(all_skills, min(3, len(all_skills)))
    result["skills"] = found_skills

    # ── Date extraction ──
    date_patterns = [
        r"\b(20\d{2})\b",
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*20\d{2}\b",
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s*20\d{2}\b",
    ]
    for pat in date_patterns:
        m = re.search(pat, lines[0] + " " + " ".join(lines[:5]) if lines else "", re.IGNORECASE)
        if m:
            result["project_duration"] = m.group(0)
            result["leadership_duration"] = m.group(0)
            break

    # ── Name extraction ──
    name_candidates = []
    for line in lines[:5]:
        cleaned = re.sub(r"[^a-zA-Z0-9\s\-\&\.\,\:\/\(\)]", "", line).strip()
        if 4 < len(cleaned) < 80 and not cleaned.lower().startswith(("page", "cert", "pdf")):
            name_candidates.append(cleaned)
    if name_candidates:
        result["project_name"] = name_candidates[0][:60]
    else:
        result["project_name"] = os.path.splitext(os.path.basename(filepath))[0]

    # ── Type detection ──
    if any(w in full_text for w in ["personal", "side project", "hobby"]):
        result["project_type"] = "personal"
    elif any(w in full_text for w in ["thesis", "university", "college", "course", "assignment", "academic"]):
        result["project_type"] = "academic"
    elif any(w in full_text for w in ["open source", "github", "community"]):
        result["project_type"] = "open_source"
    elif any(w in full_text for w in ["volunteer", "ngo", "nonprofit"]):
        result["project_type"] = "volunteer"
    else:
        result["project_type"] = "professional"

    # ── Achievements / Note ──
    body_lines = lines[2:8] if len(lines) > 2 else lines[1:]
    summary = ". ".join(line.strip() for line in body_lines if len(line.strip()) > 5)[:400]
    if summary:
        result["project_achievements"] = summary
        result["leadership_note"] = summary

    # ── Organisation ──
    org_patterns = [
        r"\b(University of [\w\s]+)\b",
        r"\b([\w\s]+ University)\b",
        r"\b([\w\s]+ Academy)\b",
        r"\b([\w\s]+ Institute)\b",
        r"\b([\w\s]+ College)\b",
        r"\b([\w\s]+ Centre)\b",
        r"\b([\w\s]+ Center)\b",
    ]
    for pat in org_patterns:
        m = re.search(pat, " ".join(lines[:8]), re.IGNORECASE)
        if m:
            result["leadership_organisation"] = m.group(1).strip().title()
            break
    if not result["leadership_organisation"]:
        result["leadership_organisation"] = "Certification Body"

    # ── Role ──
    if "intern" in full_text:
        result["leadership_role"] = "Intern"
    elif "manager" in full_text:
        result["leadership_role"] = "Manager"
    elif "developer" in full_text or "engineer" in full_text:
        result["leadership_role"] = "Developer"
    elif "student" in full_text:
        result["leadership_role"] = "Student"
    else:
        result["leadership_role"] = "Certified Participant"

    return result


def infer_skills_from_title(title):
    title_lower = title.lower()
    skills = set()
    if any(
        w in title_lower
        for w in [
            "engineer",
            "developer",
            "software",
            "programmer",
            "architect",
            "full stack",
        ]
    ):
        skills.update(["Python", "JavaScript", "SQL", "Git", "REST API"])
    if any(
        w in title_lower
        for w in ["data", "analyst", "analytics", "statistics", "scientist"]
    ):
        skills.update(
            ["Python", "SQL", "Statistics", "Machine Learning", "Data Analysis"]
        )
    if any(
        w in title_lower
        for w in ["web", "frontend", "front-end", "backend", "back-end", "full stack"]
    ):
        skills.update(["HTML", "CSS", "JavaScript", "React", "Node.js", "REST API"])
    if any(
        w in title_lower
        for w in ["mobile", "ios", "android", "swift", "kotlin", "flutter"]
    ):
        skills.update(
            ["Android", "iOS", "Kotlin", "Swift", "React Native", "Flutter", "REST API"]
        )
    if any(
        w in title_lower
        for w in ["devops", "cloud", "infrastructure", "sre", "platform"]
    ):
        skills.update(["Docker", "Kubernetes", "AWS", "CI/CD", "Linux", "Python"])
    if any(
        w in title_lower
        for w in [
            "design",
            "designer",
            "ux",
            "ui",
            "user experience",
            "product",
            "creative",
        ]
    ):
        skills.update(
            [
                "HTML",
                "CSS",
                "Figma",
                "Responsive Design",
                "User Research",
                "Prototyping",
            ]
        )
    if any(
        w in title_lower
        for w in ["manager", "director", "lead", "head", "chief", "supervisor"]
    ):
        skills.update(
            ["Communication", "Leadership", "Project Management", "Problem Solving"]
        )
    if any(
        w in title_lower
        for w in ["network", "security", "cyber", "system admin", "sysadmin"]
    ):
        skills.update(["Linux", "Networking", "Security", "Python", "Docker"])
    if any(
        w in title_lower
        for w in ["finance", "accounting", "audit", "accountant", "financial"]
    ):
        skills.update(["Excel", "Financial Analysis", "Accounting", "Data Analysis"])
    if any(
        w in title_lower
        for w in ["health", "nurse", "doctor", "medical", "clinical", "pharma"]
    ):
        skills.update(
            ["Patient Care", "Clinical Research", "Data Analysis", "Communication"]
        )
    if any(
        w in title_lower for w in ["market", "sales", "marketing", "advertising", "pr "]
    ):
        skills.update(["Communication", "Data Analysis", "Marketing Strategy", "CRM"])
    if any(
        w in title_lower
        for w in ["teacher", "professor", "lecturer", "instructor", "educator"]
    ):
        skills.update(
            ["Communication", "Curriculum Design", "Leadership", "Public Speaking"]
        )
    if any(
        w in title_lower
        for w in ["mechanical", "electrical", "civil", "chemical", "structural"]
    ):
        skills.update(
            ["CAD", "Project Management", "Data Analysis", "Technical Writing"]
        )
    if any(
        w in title_lower
        for w in ["legal", "lawyer", "attorney", "paralegal", "compliance"]
    ):
        skills.update(["Legal Research", "Communication", "Writing", "Data Analysis"])
    if any(
        w in title_lower
        for w in ["hr ", "human resources", "recruiter", "talent", "people"]
    ):
        skills.update(
            ["Communication", "HR Management", "Data Analysis", "Interviewing"]
        )
    if not skills:
        skills.update(
            [
                "Communication",
                "Problem Solving",
                "Teamwork",
                "Data Analysis",
                "Time Management",
            ]
        )
    return list(skills)


def skill_gap_analysis(current_skills, target_role):
    required = infer_skills_from_title(target_role)
    current_set = set(s.lower() for s in current_skills)
    required_set = set(s.lower() for s in required)
    missing = [s for s in required if s.lower() not in current_set]
    matched = [s for s in required if s.lower() in current_set]
    score = round((len(matched) / len(required)) * 100, 1) if required else 0
    return {
        "target_role": target_role,
        "match_score": score,
        "matched_skills": matched,
        "missing_skills": missing,
        "required_skills": required,
    }


def suggest_learning(current_skills):
    course_map = {
        "Python": {"name": "Complete Python Bootcamp", "platform": "Udemy", "url": "#"},
        "JavaScript": {
            "name": "JavaScript: The Complete Guide",
            "platform": "Udemy",
            "url": "#",
        },
        "React": {
            "name": "React - The Complete Guide",
            "platform": "Udemy",
            "url": "#",
        },
        "SQL": {"name": "The Complete SQL Bootcamp", "platform": "Udemy", "url": "#"},
        "Machine Learning": {
            "name": "Machine Learning A-Z",
            "platform": "Udemy",
            "url": "#",
        },
        "Docker": {"name": "Docker Mastery", "platform": "Udemy", "url": "#"},
        "AWS": {
            "name": "AWS Certified Solutions Architect",
            "platform": "Udemy",
            "url": "#",
        },
        "Java": {
            "name": "Java Programming Masterclass",
            "platform": "Udemy",
            "url": "#",
        },
    }
    current_lower = set(s.lower() for s in current_skills)
    suggestions = []
    for skill, course in course_map.items():
        if skill.lower() not in current_lower:
            suggestions.append(course)
        if len(suggestions) >= 3:
            break
    if not suggestions:
        suggestions = [
            {"name": "Advanced Python Programming", "platform": "Coursera", "url": "#"},
            {
                "name": "Data Structures & Algorithms",
                "platform": "AlgoExpert",
                "url": "#",
            },
            {"name": "System Design Interview", "platform": "Grokking", "url": "#"},
        ]
    return {"suggestions": suggestions}


def analyze_questionnaire(data):
    ai_data = _load_json("mock_ai_responses.json")
    personality_types = ai_data.get("personality_types", {})
    skill_gap_insights = ai_data.get("skill_gap_insights", {})
    learning_reasons = ai_data.get("learning_reasons", {})
    career_insights_data = ai_data.get("career_insights", {})

    # --- Helper to convert any field to a string ---
    def to_str(value, default=""):
        if value is None:
            return default
        if not isinstance(value, str):
            return str(value)
        return value

    # --- Extract and sanitize fields ---
    skills = data.get("skills", [])
    target_role = to_str(data.get("target_role", ""))
    personality = data.get("personality", {})
    experience = to_str(data.get("experience", "entry"), default="entry")
    full_name = to_str(data.get("full_name", ""))
    title = to_str(data.get("title", ""))
    industry = to_str(data.get("industry", "technology"), default="technology")

    # Sanitize personality sub-fields
    clean_personality = {
        "recharge": to_str(personality.get("recharge", "balanced"), default="balanced"),
        "process": to_str(
            personality.get("process", "balanced"), default="big-picture"
        ),
        "decisions": to_str(
            personality.get("decisions", "analytical"), default="analytical"
        ),
        "approach": to_str(personality.get("approach", "planned"), default="planned"),
    }

    # --- Rest of the function remains the same, but use clean_personality ---
    exp_labels = {
        "entry": "Entry Level",
        "mid": "Mid Level",
        "senior": "Senior Level",
        "lead": "Lead / Manager",
    }
    industry_labels = {
        "technology": "Technology",
        "finance": "Finance & Banking",
        "healthcare": "Healthcare",
        "education": "Education",
        "manufacturing": "Manufacturing",
        "retail": "Retail & E-commerce",
        "media": "Media & Entertainment",
        "consulting": "Consulting",
        "government": "Government",
        "nonprofit": "Non-Profit",
    }

    gap = skill_gap_analysis(skills, target_role)

    traits = []
    if clean_personality.get("recharge") == "extrovert":
        traits.append({"emoji": "🎉", "label": "Energy", "value": "Social"})
    elif clean_personality.get("recharge") == "introvert":
        traits.append({"emoji": "🧘", "label": "Energy", "value": "Solo"})
    else:
        traits.append({"emoji": "⚖️", "label": "Energy", "value": "Balanced"})

    if clean_personality.get("process") == "big-picture":
        traits.append({"emoji": "🔭", "label": "Focus", "value": "Big Picture"})
    else:
        traits.append({"emoji": "🔍", "label": "Focus", "value": "Detail"})

    if clean_personality.get("decisions") == "analytical":
        traits.append({"emoji": "🧠", "label": "Decisions", "value": "Analytical"})
    else:
        traits.append({"emoji": "💛", "label": "Decisions", "value": "Empathetic"})

    if clean_personality.get("approach") == "planned":
        traits.append({"emoji": "📋", "label": "Style", "value": "Planned"})
    else:
        traits.append({"emoji": "🎨", "label": "Style", "value": "Flexible"})

    pt_key = None
    if (
        personality.get("recharge") == "introvert"
        and personality.get("process") == "big-picture"
        and personality.get("decisions") == "analytical"
        and personality.get("approach") == "planned"
    ):
        pt_key = "The Architect"
    elif (
        personality.get("recharge") == "extrovert"
        and personality.get("process") == "big-picture"
        and personality.get("decisions") == "empathetic"
        and personality.get("approach") == "spontaneous"
    ):
        pt_key = "The Visionary"
    elif (
        personality.get("recharge") == "extrovert"
        and personality.get("process") == "detail"
        and personality.get("decisions") == "analytical"
        and personality.get("approach") == "planned"
    ):
        pt_key = "The Organizer"
    elif (
        personality.get("recharge") == "introvert"
        and personality.get("process") == "detail"
        and personality.get("decisions") == "analytical"
        and personality.get("approach") == "planned"
    ):
        pt_key = "The Specialist"
    elif (
        personality.get("recharge") == "extrovert"
        and personality.get("process") == "big-picture"
        and personality.get("decisions") == "analytical"
        and personality.get("approach") == "planned"
    ):
        pt_key = "The Strategist"
    elif (
        personality.get("recharge") == "introvert"
        and personality.get("process") == "detail"
        and personality.get("decisions") == "empathetic"
        and personality.get("approach") == "spontaneous"
    ):
        pt_key = "The Supporter"
    elif (
        personality.get("recharge") == "extrovert"
        and personality.get("process") == "detail"
        and personality.get("decisions") == "empathetic"
        and personality.get("approach") == "spontaneous"
    ):
        pt_key = "The Connector"
    elif (
        personality.get("recharge") == "introvert"
        and personality.get("process") == "big-picture"
        and personality.get("decisions") == "empathetic"
        and personality.get("approach") == "planned"
    ):
        pt_key = "The Philosopher"
    else:
        pt_key = "The Balanced Professional"

    pt_data = personality_types.get(
        pt_key, personality_types.get("The Balanced Professional", {})
    )
    personality_desc = pt_data.get(
        "description", "You have a well-rounded working style."
    )
    recommended_roles = pt_data.get("recommended_roles", [])
    work_advice = pt_data.get("work_advice", "")

    if gap["match_score"] >= 70:
        gap_insight_key = "high_match"
    elif gap["match_score"] >= 40:
        gap_insight_key = "medium_match"
    else:
        gap_insight_key = "low_match"
    gap_insight = skill_gap_insights.get(gap_insight_key, "")

    learning = suggest_learning(gap["missing_skills"] + skills)
    learning_with_reasons = []
    for i, course in enumerate(learning["suggestions"]):
        skill_name = (
            course["name"]
            .replace("Complete ", "")
            .replace(" Bootcamp", "")
            .replace(" A-Z", "")
            .replace(" Masterclass", "")
            .replace(" - The Complete Guide", "")
        )
        for ls_name, reason in learning_reasons.items():
            if (
                ls_name.lower() in skill_name.lower()
                or skill_name.lower() in ls_name.lower()
            ):
                course["reason"] = reason
                break
        if "reason" not in course:
            course["reason"] = (
                "This skill is highly valued in the industry and will strengthen your overall profile."
            )
        learning_with_reasons.append(course)

    career_insight = f"Based on your profile, you are well-positioned for roles in {industry_labels.get(data.get('industry', ''), 'Technology')}. "
    if gap["match_score"] >= 70:
        career_insight += f"Your skills strongly align with {target_role}. Focus on deepening your expertise and gaining practical experience through projects or internships."
    elif gap["match_score"] >= 40:
        career_insight += f"You have a solid foundation for {target_role}. Focus on developing the missing skills highlighted below to strengthen your profile."
    else:
        career_insight += f"To pursue {target_role}, you will need to build several key skills. The recommended learning path below will help you get started."
    industry_insight = career_insights_data.get(data.get("industry", ""), "")

    return {
        "full_name": full_name,
        "title": title,
        "experience": experience,
        "experience_label": exp_labels.get(experience, "Entry Level"),
        "personality_type": pt_key,
        "personality_description": personality_desc,
        "personality_traits": traits,
        "recommended_roles": recommended_roles,
        "work_advice": work_advice,
        "target_role": target_role,
        "industry_label": industry_labels.get(data.get("industry", ""), "Technology"),
        "skills": skills,
        "match_score": gap["match_score"],
        "matched_skills": gap["matched_skills"],
        "missing_skills": gap["missing_skills"],
        "required_skills": gap["required_skills"],
        "gap_insight": gap_insight,
        "career_insight": career_insight,
        "industry_insight": industry_insight,
        "learning_suggestions": learning_with_reasons,
    }
