class AuthError(Exception):
    """Base exception for all auth-domain business rule violations."""


class InvalidCredentialsError(AuthError):
    """Email/password combination is incorrect."""


class EmailAlreadyExistsError(AuthError):
    """Registration attempted with an existing email."""


class UsernameAlreadyExistsError(AuthError):
    """Registration attempted with an existing username."""


class UserNotFoundError(AuthError):
    """Requested user does not exist."""


class UserNotActiveError(AuthError):
    """Account is disabled or soft-deleted."""


class InvalidTokenError(AuthError):
    """Token is malformed, expired, or of the wrong type."""
