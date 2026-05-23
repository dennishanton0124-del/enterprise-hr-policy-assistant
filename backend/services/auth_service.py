from backend.db.supabase_client import supabase


def get_users():
    if supabase is None:
        print("[auth_service] ERROR: Supabase client is None")
        return []

    try:
        users = supabase.select(
            "users",
            "select=id,email,role,department,created_at&order=email.asc"
        )

        return users or []

    except Exception as e:
        print(f"[auth_service] ERROR loading users: {e}")
        return []


def get_user_by_email(email: str):
    if supabase is None:
        print("[auth_service] ERROR: Supabase client is None")
        return None

    try:
        users = supabase.select(
            "users",
            f"select=id,email,role,department,created_at&email=eq.{email}"
        )

        if users:
            return users[0]

        return None

    except Exception as e:
        print(f"[auth_service] ERROR loading user by email: {e}")
        return None


def has_role(user: dict | None, allowed_roles: list[str]) -> bool:
    if not user:
        return False

    return user.get("role") in allowed_roles


def require_role(user: dict | None, allowed_roles: list[str]) -> bool:
    if has_role(user, allowed_roles):
        return True

    return False