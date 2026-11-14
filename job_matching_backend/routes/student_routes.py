from flask import Blueprint, g, jsonify

from auth import require_auth
from routes.data_helpers import execute_maybe_single, json_object, normalize_projects, normalize_skills

student_bp = Blueprint("students", __name__)

PROFILE_FIELDS = (
    "name",
    "college",
    "course",
    "year",
    "graduation_year",
    "cv_name",
    "links",
    "preferences",
    "completed",
    "recruitment_visible",
)


def _validate_profile_payload(data):
    profile = {}
    for field in PROFILE_FIELDS:
        if field not in data:
            continue
        value = data[field]
        if field in {"links", "preferences"}:
            if not isinstance(value, dict):
                raise ValueError(f"{field} must be an object.")
        elif field in {"completed", "recruitment_visible"}:
            if not isinstance(value, bool):
                raise ValueError(f"{field} must be a boolean.")
        elif value is not None and not isinstance(value, str):
            raise ValueError(f"{field} must be text.")
        profile[field] = value

    if "name" in profile and not (profile["name"] or "").strip():
        raise ValueError("Name cannot be empty.")
    if "name" in profile:
        profile["name"] = profile["name"].strip()
    return profile


def _sync_skills(client, profile_id, desired):
    response = (
        client.table("student_skills")
        .select("skill_name,level")
        .eq("profile_id", profile_id)
        .execute()
    )
    existing = response.data or []
    existing_by_name = {
        row["skill_name"].casefold(): row
        for row in existing
    }
    desired_names = {skill["name"].casefold() for skill in desired}

    for skill in desired:
        current = existing_by_name.get(skill["name"].casefold())
        if current:
            if (
                current["skill_name"] != skill["name"]
                or current["level"] != skill["level"]
            ):
                (
                    client.table("student_skills")
                    .update({
                        "skill_name": skill["name"],
                        "level": skill["level"],
                    })
                    .eq("profile_id", profile_id)
                    .eq("skill_name", current["skill_name"])
                    .execute()
                )
        else:
            client.table("student_skills").insert({
                "profile_id": profile_id,
                "skill_name": skill["name"],
                "level": skill["level"],
            }).execute()

    for row in existing:
        if row["skill_name"].casefold() not in desired_names:
            (
                client.table("student_skills")
                .delete()
                .eq("profile_id", profile_id)
                .eq("skill_name", row["skill_name"])
                .execute()
            )


def _sync_projects(client, profile_id, desired):
    response = (
        client.table("projects")
        .select("id,title,description,link")
        .eq("profile_id", profile_id)
        .execute()
    )
    remaining = list(response.data or [])
    additions = []

    for project in desired:
        match_index = next(
            (
                index
                for index, row in enumerate(remaining)
                if all(
                    row.get(field, "") == project[field]
                    for field in ("title", "description", "link")
                )
            ),
            None,
        )
        if match_index is None:
            additions.append(project)
        else:
            remaining.pop(match_index)

    if additions:
        client.table("projects").insert([
            {"profile_id": profile_id, **project}
            for project in additions
        ]).execute()
    for row in remaining:
        client.table("projects").delete().eq("id", row["id"]).execute()


def _student_response(client, profile):
    profile_id = profile["id"]
    skills = (
        client.table("student_skills")
        .select("skill_name,level")
        .eq("profile_id", profile_id)
        .order("skill_name")
        .execute()
        .data
        or []
    )
    projects = (
        client.table("projects")
        .select("id,title,description,link")
        .eq("profile_id", profile_id)
        .order("created_at")
        .execute()
        .data
        or []
    )
    result = {
        key: value
        for key, value in profile.items()
        if key not in {"auth_user_id", "is_demo", "requested_role"}
    }
    result["skills"] = [
        {"name": row["skill_name"], "level": row["level"]}
        for row in skills
    ]
    result["projects"] = projects
    return result


def _visible_candidates_for_recruiter(client, profile_id):
    company = execute_maybe_single(
        client.table("companies")
        .select("id")
        .eq("owner_profile_id", profile_id)
    )
    if not company:
        return []

    jobs = (
        client.table("jobs")
        .select("id")
        .eq("company_id", company["id"])
        .execute()
        .data
        or []
    )
    candidates = {}
    for job in jobs:
        rows = client.rpc(
            "get_candidates_for_job",
            {"p_job_id": job["id"]},
        ).execute().data or []
        for candidate in rows:
            if candidate.get("is_demo"):
                continue
            candidates[candidate["candidate_profile_id"]] = candidate
    return list(candidates.values())


@student_bp.route("/", methods=["GET"])
@require_auth("student", "recruiter")
def get_students():
    if g.profile["role"] == "student":
        profile = execute_maybe_single(
            g.supabase.table("profiles")
            .select("*")
            .eq("id", g.profile["id"])
        )
        return jsonify([_student_response(g.supabase, profile)] if profile else []), 200

    return jsonify(
        _visible_candidates_for_recruiter(g.supabase, g.profile["id"])
    ), 200


@student_bp.route("/", methods=["POST"])
@require_auth("student")
def add_student():
    data, error_response = json_object("Student data is required.")
    if error_response:
        return error_response

    try:
        profile_data = _validate_profile_payload(data)
        skills = normalize_skills(data["skills"]) if "skills" in data else None
        projects = normalize_projects(data["projects"]) if "projects" in data else None
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    profile_id = g.profile["id"]
    if profile_data:
        (
            g.supabase.table("profiles")
            .update(profile_data)
            .eq("id", profile_id)
            .execute()
        )
    if skills is not None:
        _sync_skills(g.supabase, profile_id, skills)
    if projects is not None:
        _sync_projects(g.supabase, profile_id, projects)

    profile = (
        g.supabase.table("profiles")
        .select("*")
        .eq("id", profile_id)
        .single()
        .execute()
        .data
    )
    return jsonify({
        "message": "Student added successfully!",
        "student": _student_response(g.supabase, profile),
    }), 201


@student_bp.route("/<path:email>", methods=["PUT"])
@require_auth("student")
def update_student(email):
    data, error_response = json_object("Student data is required.")
    if error_response:
        return error_response

    authenticated_email = (getattr(g.auth_user, "email", None) or "").strip().lower()
    if not authenticated_email or email.strip().lower() != authenticated_email:
        return jsonify({"error": "You can update only your own profile."}), 403

    try:
        profile_data = _validate_profile_payload(data)
        skills = normalize_skills(data["skills"]) if "skills" in data else None
        projects = normalize_projects(data["projects"]) if "projects" in data else None
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    profile_id = g.profile["id"]
    if profile_data:
        (
            g.supabase.table("profiles")
            .update(profile_data)
            .eq("id", profile_id)
            .execute()
        )
    if skills is not None:
        _sync_skills(g.supabase, profile_id, skills)
    if projects is not None:
        _sync_projects(g.supabase, profile_id, projects)

    profile = (
        g.supabase.table("profiles")
        .select("*")
        .eq("id", profile_id)
        .single()
        .execute()
        .data
    )
    return jsonify({
        "message": "Student updated successfully!",
        "student": _student_response(g.supabase, profile),
    }), 200
