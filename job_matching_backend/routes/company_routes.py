from flask import Blueprint, g, jsonify

from auth import require_auth
from routes.data_helpers import execute_maybe_single, json_object

company_bp = Blueprint("company", __name__)
COMPANY_FIELDS = ("name", "website", "location", "size", "about")


@company_bp.route("/", methods=["GET"])
@require_auth("recruiter")
def get_company():
    company = execute_maybe_single(
        g.supabase.table("companies")
        .select("id,name,website,location,size,about,created_at,updated_at")
        .eq("owner_profile_id", g.profile["id"])
    )
    return jsonify(company or {}), 200


@company_bp.route("/", methods=["POST"])
@require_auth("recruiter")
def create_company():
    data, error_response = json_object("Company data is required.")
    if error_response:
        return error_response

    company_data = {}
    for field in COMPANY_FIELDS:
        if field in data:
            if not isinstance(data[field], str):
                return jsonify({"error": f"{field} must be text."}), 400
            company_data[field] = data[field].strip() if field == "name" else data[field]

    if not company_data.get("name"):
        return jsonify({"error": "Company name is required."}), 400

    existing = execute_maybe_single(
        g.supabase.table("companies")
        .select("id")
        .eq("owner_profile_id", g.profile["id"])
    )
    if existing:
        saved = (
            g.supabase.table("companies")
            .update(company_data)
            .eq("id", existing["id"])
            .select("id,name,website,location,size,about,created_at,updated_at")
            .single()
            .execute()
            .data
        )
        status = 200
    else:
        saved = (
            g.supabase.table("companies")
            .insert({
                "owner_profile_id": g.profile["id"],
                **company_data,
            })
            .select("id,name,website,location,size,about,created_at,updated_at")
            .single()
            .execute()
            .data
        )
        status = 201

    return jsonify({
        "message": "Company profile saved successfully!",
        "company": saved,
    }), status
