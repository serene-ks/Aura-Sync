from flask import current_app
from supabase import ClientOptions, create_client


def create_authenticated_client(supabase_url, supabase_key, access_token):
    options = ClientOptions(
        headers={"Authorization": f"Bearer {access_token}"},
        auto_refresh_token=False,
        persist_session=False,
    )
    return create_client(supabase_url, supabase_key, options=options)


def request_supabase_client(access_token):
    factory = current_app.config["SUPABASE_CLIENT_FACTORY"]
    return factory(
        current_app.config["SUPABASE_URL"],
        current_app.config["SUPABASE_KEY"],
        access_token,
    )
