from datetime import date

from flask import Blueprint, g, jsonify

from auth import require_auth
from routes.data_helpers import (
    JOB_TYPES,
    execute_maybe_single,
    json_object,
    job_response,
    normalize_skills,
)

job_bp = Blueprint("jobs", __name__)
JOB_UPDATE_FIELDS = (
    "title",
    "company",
    "location",
    "type",
    "remote",
    "salary",
    "description",
    "skills",
    "experience",
)
DECISION_STATUSES = {"shortlisted", "contacted", "rejected"}


def _owned_job(job_id):
    job = execute_maybe_single(
        g.supabase.table("jobs")
        .select("*")
        .eq("id", job_id)
    )
    if not job:
        return None, (jsonify({"error": "Job not found."}), 404)

    company = None
    if job.get("company_id"):
        company = execute_maybe_single(
            g.supabase.table("companies")
            .select("id")
            .eq("id", job["company_id"])
            .eq("owner_profile_id", g.profile["id"])
        )
    if not company:
        return None, (jsonify({"error": "You cannot manage this job."}), 403)
    return job, None


def _company_for_recruiter():
    return execute_maybe_single(
        g.supabase.table("companies")
        .select("id,name")
        .eq("owner_profile_id", g.profile["id"])
    )


def _validate_job_fields(data, *, creating):
    fields = {}
    source_fields = (
        ("title", "title"),
        ("company", "company_name"),
        ("location", "location"),
        ("type", "type"),
        ("remote", "remote"),
        ("salary", "salary"),
        ("description", "description"),
        ("skills", "skills"),
        ("experience", "experience"),
    )
    for input_name, column_name in source_fields:
        if input_name not in data:
            continue
        value = data[input_name]
        if input_name == "skills":
            fields[column_name] = [skill["name"] for skill in normalize_skills(value)]
        elif input_name == "remote":
            if not isinstance(value, bool):
                raise ValueError("remote must be a boolean.")
            fields[column_name] = value
        elif input_name == "type":
            if not isinstance(value, str) or value not in JOB_TYPES:
                raise ValueError("Invalid job type.")
            fields[column_name] = value
        elif not isinstance(value, str):
            raise ValueError(f"{input_name} must be text.")
        elif input_name == "title":
            if not value.strip():
                raise ValueError("Job title is required.")
            fields[column_name] = value.strip()
        else:
            fields[column_name] = value

    if creating:
        if not fields.get("title"):
            raise ValueError("Job title is required.")
        fields.setdefault("location", "Not specified")
        fields.setdefault("type", "Full-time")
        fields.setdefault("remote", False)
        fields.setdefault("salary", "")
        fields.setdefault("description", "")
        fields.setdefault("skills", [])
        fields.setdefault("experience", "")
        fields["apply_url"] = data.get("apply_url", "")
        if not isinstance(fields["apply_url"], str):
            raise ValueError("apply_url must be text.")
        fields["posted_at"] = data.get("posted_at") or date.today().isoformat()
        if not isinstance(fields["posted_at"], str):
            raise ValueError("posted_at must be a YYYY-MM-DD date.")
        try:
            fields["posted_at"] = date.fromisoformat(fields["posted_at"]).isoformat()
        except ValueError:
            raise ValueError("posted_at must be a valid YYYY-MM-DD date.") from None
    return fields


def _visible_job_candidates(job_id):
    return (
        g.supabase.rpc(
            "get_candidates_for_job",
            {"p_job_id": job_id},
        )
        .execute()
        .data
        or []
    )


def _decisions_for_job(job_id):
    candidates = _visible_job_candidates(job_id)
    candidate_ids = {
        row["candidate_profile_id"]: row["id"]
        for row in candidates
    }
    decisions = (
        g.supabase.table("candidate_decisions")
        .select("candidate_profile_id,status")
        .eq("job_id", job_id)
        .execute()
        .data
        or []
    )
    return {
        f"{job_id}:{candidate_ids[row['candidate_profile_id']]}": row["status"]
        for row in decisions
        if row["candidate_profile_id"] in candidate_ids
    }


@job_bp.route("/", methods=["GET"])
@require_auth("student", "recruiter")
def get_jobs():
    jobs = (
        g.supabase.table("jobs")
        .select("*")
        .order("posted_at", desc=True)
        .execute()
        .data
        or []
    )
    if g.profile["role"] == "recruiter":
        company = _company_for_recruiter()
        if not company:
            return jsonify([]), 200
        jobs = [
            job
            for job in jobs
            if job.get("company_id") == company["id"]
        ]
    return jsonify([job_response(job) for job in jobs]), 200


@job_bp.route("/<job_id>", methods=["GET"])
@require_auth("student", "recruiter")
def get_job(job_id):
    job = execute_maybe_single(
        g.supabase.table("jobs")
        .select("*")
        .eq("id", job_id)
    )
    if not job:
        return jsonify({"error": "Job not found."}), 404
    return jsonify(job_response(job)), 200


@job_bp.route("/", methods=["POST"])
@require_auth("recruiter")
def add_job():
    data, error_response = json_object("Job data is required.")
    if error_response:
        return error_response

    company = _company_for_recruiter()
    if not company:
        return jsonify({"error": "Create your company profile before posting a job."}), 403

    try:
        job_data = _validate_job_fields(data, creating=True)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    job_data.update({
        "company_id": company["id"],
        "company_name": company["name"],
        # NOTE: do not send "source". It is not in the INSERT column grant
        # (Postgres 42501 -> 403), and the column already defaults to 'recruiter'.
    })
    saved = (
        g.supabase.table("jobs")
        .insert(job_data)
        .select("*")
        .single()
        .execute()
        .data
    )
    return jsonify({
        "message": "Job added successfully!",
        "job": job_response(saved),
    }), 201


@job_bp.route("/<job_id>", methods=["PUT"])
@require_auth("recruiter")
def update_job(job_id):
    data, error_response = json_object("Updated job data is required.")
    if error_response:
        return error_response

    job, error_response = _owned_job(job_id)
    if error_response:
        return error_response

    update_data = {key: value for key, value in data.items() if key in JOB_UPDATE_FIELDS}
    if not update_data:
        return jsonify({"error": "No supported job fields were provided."}), 400

    try:
        update_data = _validate_job_fields(update_data, creating=False)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    if "company_name" in update_data:
        update_data["company_name"] = job["company_name"]
    saved = (
        g.supabase.table("jobs")
        .update(update_data)
        .eq("id", job_id)
        .select("*")
        .single()
        .execute()
        .data
    )
    return jsonify({
        "message": "Job updated successfully!",
        "job": job_response(saved),
    }), 200


@job_bp.route("/<job_id>", methods=["DELETE"])
@require_auth("recruiter")
def delete_job(job_id):
    _, error_response = _owned_job(job_id)
    if error_response:
        return error_response
    g.supabase.table("jobs").delete().eq("id", job_id).execute()
    return jsonify({"message": "Job deleted successfully."}), 200


@job_bp.route("/<job_id>/decisions/", methods=["GET"])
@require_auth("recruiter")
def get_decisions(job_id):
    _, error_response = _owned_job(job_id)
    if error_response:
        return error_response
    return jsonify(_decisions_for_job(job_id)), 200


@job_bp.route("/<job_id>/decisions/", methods=["POST"])
@require_auth("recruiter")
def update_decision(job_id):
    data, error_response = json_object("Decision data is required.")
    if error_response:
        return error_response

    _, error_response = _owned_job(job_id)
    if error_response:
        return error_response

    candidate_id = data.get("candidate_id")
    status = data.get("status")
    if not isinstance(candidate_id, (str, int)) or not str(candidate_id).strip():
        return jsonify({"error": "Candidate ID is required."}), 400
    if status is not None and (
        not isinstance(status, str) or status not in DECISION_STATUSES
    ):
        return jsonify({"error": "Invalid decision status."}), 400

    candidate = next(
        (
            row
            for row in _visible_job_candidates(job_id)
            if str(row["id"]) == str(candidate_id)
            or str(row["candidate_profile_id"]) == str(candidate_id)
        ),
        None,
    )
    if not candidate:
        return jsonify({
            "error": "Candidate is unavailable or has not consented to recruitment visibility."
        }), 404

    existing = execute_maybe_single(
        g.supabase.table("candidate_decisions")
        .select("candidate_profile_id")
        .eq("job_id", job_id)
        .eq("candidate_profile_id", candidate["candidate_profile_id"])
    )
    if status is None:
        if existing:
            (
                g.supabase.table("candidate_decisions")
                .delete()
                .eq("job_id", job_id)
                .eq("candidate_profile_id", candidate["candidate_profile_id"])
                .execute()
            )
    elif existing:
        (
            g.supabase.table("candidate_decisions")
            .update({"status": status})
            .eq("job_id", job_id)
            .eq("candidate_profile_id", candidate["candidate_profile_id"])
            .execute()
        )
    else:
        g.supabase.table("candidate_decisions").insert(
            {
                "job_id": job_id,
                "candidate_profile_id": candidate["candidate_profile_id"],
                "status": status,
            }
        ).execute()

    return jsonify({
        "message": "Decision updated successfully.",
        "decisions": _decisions_for_job(job_id),
    }), 200