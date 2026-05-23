import os
import requests
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

print(f"[supabase_client] Loading .env from: {ENV_PATH}")
print(f"[supabase_client] .env exists: {ENV_PATH.exists()}")

load_dotenv(dotenv_path=ENV_PATH)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

print(f"[supabase_client] SUPABASE_URL loaded: {bool(SUPABASE_URL)}")
print(f"[supabase_client] SUPABASE_ANON_KEY loaded: {bool(SUPABASE_ANON_KEY)}")


class SupabaseRestClient:
    """Minimal Supabase REST API client using requests library."""

    def __init__(self, url: str, key: str):
        if not url:
            raise ValueError("SUPABASE_URL is missing from .env")
        if not key:
            raise ValueError("SUPABASE_ANON_KEY is missing from .env")

        self.base_url = url.rstrip("/")
        self.rest_url = f"{self.base_url}/rest/v1"

        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

        print("[supabase_client] REST client initialized")

    def insert(self, table: str, data: dict) -> dict:
        """Insert a row into a table."""
        url = f"{self.rest_url}/{table}"

        try:
            response = requests.post(
                url,
                json=data,
                headers=self.headers,
                timeout=10,
            )
            response.raise_for_status()
            print(f"[supabase_client] INSERT {table} success")
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"[supabase_client] INSERT {table} error: {e}")

            if hasattr(e, "response") and e.response is not None:
                print(f"[supabase_client] Response: {e.response.text}")

            raise

    def select(self, table: str, query: str = "*") -> list:
        """Select rows from a table."""
        url = f"{self.rest_url}/{table}?{query}"

        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10,
            )
            response.raise_for_status()
            print(f"[supabase_client] SELECT {table} success")
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"[supabase_client] SELECT {table} error: {e}")

            if hasattr(e, "response") and e.response is not None:
                print(f"[supabase_client] Response: {e.response.text}")

            return []

    def update(self, table: str, data: dict, query: str) -> dict:
        """Update rows in a table using a Supabase REST query filter."""
        url = f"{self.rest_url}/{table}?{query}"

        try:
            response = requests.patch(
                url,
                json=data,
                headers=self.headers,
                timeout=10,
            )
            response.raise_for_status()
            print(f"[supabase_client] UPDATE {table} success")
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"[supabase_client] UPDATE {table} error: {e}")

            if hasattr(e, "response") and e.response is not None:
                print(f"[supabase_client] Response: {e.response.text}")

            raise


try:
    supabase = SupabaseRestClient(SUPABASE_URL, SUPABASE_ANON_KEY)
    print("[supabase_client] Module initialized successfully")

except Exception as e:
    print(f"[supabase_client] ERROR: Failed to initialize Supabase client: {e}")
    supabase = None