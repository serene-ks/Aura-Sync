from flask import Blueprint, g, jsonify

from auth import require_auth
from routes.data_helpers import (
    APPLICATION_STATUSES,
    execute_maybe_single,
    iso_date_or_none,
    json_object,
    tracker_response,
)

tracker_bp = Blueprint("tracker", __name__)
TRACKER_SELECT = (
    "id,job_id,status,notes,applied_at,"
    "job:jobs(id,title,company_name,location,type,remote,salary,posted_at,"
    "apply_url,source,description,skills,experience)"
)


def _tracker_item(item_id):
    return execute_maybe_single(
        g.supabase.table("applications")
        .select(TRACKER_SELECT)
        .eq("id", item_id)
    )


@tracker_bp.route("/", methods=["GET"])
@require_auth("student")
def get_tracker():
    rows = (
        g.supabase.table("applications")
        .select(TRACKER_SELECT)
        .eq("student_profile_id", g.profile["id"])
        .order("created_at")
        .execute()
        .data
        or []
    )
    return jsonify([tracker_response(row) for row in rows]), 200


@tracker_bp.route("/", methods=["POST"])
@require_auth("student")
def add_tracker_item():
    data, error_response = json_object("Tracker data is required.")
    if error_response:
        return error_response

    job_id = data.get("job_id") or data.get("id")
    if not isinstance(job_id, (str, int)) or not str(job_id).strip():
        return jsonify({"error": "Job ID is required."}), 400
    job_id = str(job_id)

    job = execute_maybe_single(
        g.supabase.table("jobs")
        .select("id")
        .eq("id", job_id)
    )
    if not job:
        return jsonify({"error": "Job not found."}), 404

    existing = execute_maybe_single(
        g.supabase.table("applications")
        .select(TRACKER_SELECT)
        .eq("student_profile_id", g.profile["id"])
        .eq("job_id", job_id)
    )
    if existing:
        return jsonify(tracker_response(existing)), 200

    status = data.get("status") or "saved"
    notes = data.get("notes") or ""
    try:
        applied_at = iso_date_or_none(data.get("applied_at"), "applied_at")
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    if not isinstance(status, str) or status not in APPLICATION_STATUSES:
        return jsonify({"error": "Invalid tracker status."}), 400
    if not isinstance(notes, str):
        return jsonify({"error": "notes must be text."}), 400

    saved = (
        g.supabase.table("applications")
        .insert({
            "student_profile_id": g.profile["id"],
            "job_id": job_id,
            "status": status,
            "notes": notes,
            "applied_at": applied_at,
        })
        .select(TRACKER_SELECT)
        .single()
        .execute()
        .data
    )
    return jsonify(tracker_response(saved)), 201


@tracker_bp.route("/<item_id>", methods=["PUT"])
@require_auth("student")
def update_tracker_item(item_id):
    data, error_response = json_object("Tracker data is required.")
    if error_response:
        return error_response

    update_data = {}
    if "status" in data:
        if (
            not isinstance(data["status"], str)
            or data["status"] not in APPLICATION_STATUSES
        ):
            return jsonify({"error": "Invalid tracker status."}), 400
        update_data["status"] = data["status"]
    if "notes" in data:
        if not isinstance(data["notes"], str):
            return jsonify({"error": "notes must be text."}), 400
        update_data["notes"] = data["notes"]
    if "applied_at" in data:
        try:
            update_data["applied_at"] = iso_date_or_none(
                data["applied_at"], "applied_at"
            )
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
    if not update_data:
        return jsonify({"error": "No supported tracker fields were provided."}), 400

    existing = _tracker_item(item_id)
    if not existing:
        return jsonify({"error": "Tracker item not found."}), 404
    (
        g.supabase.table("applications")
        .update(update_data)
        .eq("id", item_id)
        .execute()
    )
    return jsonify(tracker_response(_tracker_item(item_id))), 200


@tracker_bp.route("/<item_id>", methods=["DELETE"])
@require_auth("student")
def delete_tracker_item(item_id):
    if not _tracker_item(item_id):
        return jsonify({"error": "Tracker item not found."}), 404
    (
        g.supabase.table("applications")
        .delete()
        .eq("id", item_id)
        .execute()
    )
    return jsonify({"message": "Tracker item deleted successfully!"}), 200
