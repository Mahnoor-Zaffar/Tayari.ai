from core.config import settings


def _get_admin_emails() -> frozenset[str]:
    """Return admin emails from settings, falling back to the default."""
    raw = settings.ADMIN_EMAILS or "admin@tayari.ai"
    return frozenset(email.strip().lower() for email in raw.split(",") if email.strip())


def user_roles(email: str, *, email_verified: bool = False) -> tuple[list[str], list[str]]:
    """Return (roles, permissions) for a user based on their email.

    Admin elevation requires BOTH a configured admin email AND a verified
    email address.  New accounts are unverified (see ``register``), so an
    attacker who registers with an admin email only gets the ``user`` role
    until they prove ownership of the address.
    """
    if email_verified and email.lower() in _get_admin_emails():
        return (["admin", "user"], ["users:read", "users:write", "users:delete"])
    return (["user"], [])
