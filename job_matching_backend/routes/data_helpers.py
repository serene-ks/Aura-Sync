from datetime import date

from flask import jsonify, request

SKILL_LEVELS = {"Beginner", "Intermediate", "Advanced"}
APPLICATION_STATUSES = {
    "saved",
    "applied",
    "interview",
    "offer",
    "closed",
    "rejected",
    "no_reply",
}
JOB_TYPES = {"Internship", "Full-time", "Part-time", "Contract"}


def json_object(required_message):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return None, (jsonify({"error": required_message}), 400)
    return data, None


def normalize_skills(value):
    if not isinstance(value, list):
        raise ValueError("Skills must be a list.")

    result = []
    seen = set()
    for skill in value:
        if isinstance(skill, str):
            name, level = skill.strip(), "Beginner"
        elif isinstance(skill, dict):
            name = skill.get("name") or skill.get("skill") or ""
            level = skill.get("level") or "Beginner"
            if not isinstance(name, str):
                raise ValueError("Skill names must be text.")
            name = name.strip()
        else:
            raise ValueError("Each skill must be a name or an object.")

        if not name:
            raise ValueError("Skill names cannot be empty.")
        if not isinstance(level, str) or level not in SKILL_LEVELS:
            raise ValueError(f"Invalid skill level for {name}.")
        key = name.casefold()
        if key in seen:
            raise ValueError(f"Duplicate skill: {name}.")
        seen.add(key)
        result.append({"name": name, "level": level})
    return result


def normalize_projects(value):
    if not isinstance(value, list):
        raise ValueError("Projects must be a list.")

    result = []
    for project in value:
        if not isinstance(project, dict):
            raise ValueError("Each project must be an object.")
        title = project.get("title") or ""
        if not isinstance(title, str):
            raise ValueError("Project titles must be text.")
        title = title.strip()
        if not title:
            continue
        description = project.get("description") or ""
        link = project.get("link") or ""
        if not isinstance(description, str) or not isinstance(link, str):
            raise ValueError("Project descriptions and links must be text.")
        result.append({
            "title": title,
            "description": description,
            "link": link,
        })
    return result


def iso_date_or_none(value, field_name):
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid YYYY-MM-DD date.") from None


def job_response(row):
    result = dict(row)
    result["company"] = result.get("company_name", "")
    return result


def execute_maybe_single(query):
    response = query.maybe_single().execute()
    return response.data if response else None


def tracker_response(row):
    job = row.get("job") or {}
    if isinstance(job, list):
        job = job[0] if job else {}
    if job:
        job = job_response(job)
    result = {
        **job,
        "id": row["id"],
        "job_id": row["job_id"],
        "status": row["status"],
        "notes": row.get("notes", ""),
        "applied_at": row.get("applied_at"),
    }
    result["job"] = job
    return result
