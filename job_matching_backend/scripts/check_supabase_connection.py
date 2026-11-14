import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from supabase import ClientOptions, create_client

BACKEND_DIR = Path(__file__).resolve().parents[1]


def main():
    load_dotenv(BACKEND_DIR / ".env")
    supabase_url = os.environ.get("SUPABASE_URL", "").strip()
    supabase_key = os.environ.get("SUPABASE_KEY", "").strip()
    missing = [
        name
        for name, value in (
            ("SUPABASE_URL", supabase_url),
            ("SUPABASE_KEY", supabase_key),
        )
        if not value
    ]
    if missing:
        print(
            "Missing required environment variable(s): "
            + ", ".join(missing)
            + ". Check the backend .env file."
        )
        return 2

    create_client(
        supabase_url,
        supabase_key,
        options=ClientOptions(auto_refresh_token=False, persist_session=False),
    )
    url = f"{supabase_url.rstrip('/')}/auth/v1/health"
    request = Request(url, headers={"apikey": supabase_key}, method="GET")
    try:
        with urlopen(request, timeout=10) as response:
            if 200 <= response.status < 300:
                print("Supabase Auth health endpoint is reachable.")
                return 0
            print(f"Supabase health check returned HTTP {response.status}.")
            return 1
    except HTTPError as error:
        print(f"Supabase health check returned HTTP {error.code}.")
        return 1
    except (TimeoutError, URLError, OSError) as error:
        print(f"Supabase health check failed ({type(error).__name__}).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
