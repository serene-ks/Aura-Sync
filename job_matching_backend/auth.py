from functools import wraps

import httpx
from flask import current_app, g, jsonify, request
from supabase_auth.errors import AuthError

from supabase_client import request_supabase_client


def require_auth(*allowed_roles):
    def decorate(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            authorization = request.headers.get("Authorization", "")
            scheme, separator, access_token = authorization.partition(" ")
            if (
                not separator
                or scheme.lower() != "bearer"
                or not access_token.strip()
            ):
                return jsonify({"error": "A valid Bearer access token is required."}), 401

            access_token = access_token.strip()
            client = request_supabase_client(access_token)
            try:
                user_response = client.auth.get_user(access_token)
            except AuthError:
                return jsonify({"error": "The access token is invalid or expired."}), 401
            except httpx.HTTPError:
                current_app.logger.error("Supabase token validation is unavailable.")
                return jsonify({"error": "Authentication service is unavailable."}), 503

            user = getattr(user_response, "user", None)
            user_id = getattr(user, "id", None)
            if not user_id:
                return jsonify({"error": "The access token is invalid or expired."}), 401

            profile_response = (
                client.table("profiles")
                .select("id,auth_user_id,role,is_demo")
                .eq("auth_user_id", str(user_id))
                .maybe_single()
                .execute()
            )
            profile = profile_response.data
            if not profile or profile.get("is_demo"):
                return jsonify({"error": "An authenticated profile is required."}), 403

            if allowed_roles and profile.get("role") not in allowed_roles:
                return jsonify({"error": "Your account cannot perform this operation."}), 403

            g.supabase = client
            g.auth_user = user
            g.user_id = str(user_id)
            g.profile = profile
            return view(*args, **kwargs)

        return wrapped

    return decorate
