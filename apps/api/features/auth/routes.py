from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, status

from core.audit import AuditEvent, AuthEvent
from core.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    TokenError,
    success_response,
)
from core.logging import get_logger
from features.auth.dependencies import get_auth_service, get_token_service
from features.auth.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
    UsernameAlreadyExistsError,
    UserNotActiveError,
    UserNotFoundError,
)
from features.auth.jwt.service import TokenService
from features.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UserResponse,
)
from features.auth.services import AuthenticationService, AuthResult, RegistrationData

router = APIRouter(tags=["auth"])
log = get_logger("auth")


def _format_auth_result(result: AuthResult) -> dict:
    """Build the standardized success body shared by signup and login."""
    return success_response(
        {
            "access_token": result.access_token,
            "refresh_token": result.refresh_token,
            "token_type": "bearer",
            "user": UserResponse(
                id=result.user.id,
                email=result.user.email,
                username=result.user.username,
                display_name=result.user.display_name,
                email_verified=result.user.email_verified,
                created_at=result.user.created_at,
            ).model_dump(),
        }
    )


@router.post(
    "/auth/signup",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def signup(
    body: RegisterRequest,
    request: Request,
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> dict:
    try:
        result = await auth_service.register(
            RegistrationData(
                email=body.email,
                username=body.username,
                display_name=body.display_name,
                password=body.password,
            )
        )
    except EmailAlreadyExistsError:
        log.info("registration blocked — duplicate email", extra={"email_hash": body.email[:3] + "…"})
        raise ConflictError("Email is already registered")
    except UsernameAlreadyExistsError:
        log.info("registration blocked — duplicate username")
        raise ConflictError("Username is already taken")

    request.state.audit.log(
        AuditEvent(
            AuthEvent.REGISTER,
            user_id=str(result.user.id),
            email=result.user.email,
        )
    )
    return _format_auth_result(result)


@router.post(
    "/auth/login",
    status_code=status.HTTP_200_OK,
    summary="Authenticate with email and password",
)
async def login(
    body: LoginRequest,
    request: Request,
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> dict:
    try:
        result = await auth_service.login(body.email, body.password)
    except InvalidCredentialsError:
        request.state.audit.log(
            AuditEvent(
                AuthEvent.LOGIN_FAILED,
                email=body.email,
                outcome="failure",
                failure_reason="invalid_credentials",
            )
        )
        raise AuthenticationError("Invalid email or password")
    except UserNotActiveError as exc:
        request.state.audit.log(
            AuditEvent(
                AuthEvent.LOGIN_FAILED,
                email=body.email,
                outcome="failure",
                failure_reason="account_inactive",
            )
        )
        raise AuthorizationError(str(exc))

    request.state.audit.log(
        AuditEvent(
            AuthEvent.LOGIN,
            user_id=str(result.user.id),
            email=result.user.email,
        )
    )
    return _format_auth_result(result)


@router.post(
    "/auth/logout",
    status_code=status.HTTP_200_OK,
    summary="Revoke the current refresh token",
)
async def logout(
    body: RefreshRequest,
    request: Request,
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> dict:
    try:
        await auth_service.logout(body.refresh_token)
    except InvalidTokenError as exc:
        raise TokenError(str(exc))

    request.state.audit.log(
        AuditEvent(
            AuthEvent.LOGOUT,
        )
    )
    return success_response({"message": "Logged out successfully"})


@router.post(
    "/auth/refresh",
    status_code=status.HTTP_200_OK,
    summary="Issue new access and refresh tokens via a refresh token",
)
async def refresh(
    body: RefreshRequest,
    request: Request,
    auth_service: AuthenticationService = Depends(get_auth_service),
    token_service: TokenService = Depends(get_token_service),
) -> dict:
    try:
        result = await auth_service.refresh(body.refresh_token)
    except InvalidTokenError:
        claims = token_service.peek(body.refresh_token)
        family = claims.get("token_family", "")
        email_from_claims = claims.get("sub", "")
        if family:
            expires_at = datetime.fromtimestamp(claims.get("exp", 0), tz=UTC)
            await token_service.revoke_family(family, expires_at)
            request.state.audit.log(
                AuditEvent(
                    AuthEvent.TOKEN_REFRESH_REJECTED,
                    email=email_from_claims,
                    outcome="failure",
                    failure_reason="replay_detected",
                    metadata={"token_family": family},
                )
            )
        else:
            request.state.audit.log(
                AuditEvent(
                    AuthEvent.TOKEN_REFRESH_REJECTED,
                    email=email_from_claims,
                    outcome="failure",
                    failure_reason="invalid_token",
                )
            )
        raise TokenError("Invalid or expired refresh token")
    except UserNotFoundError as exc:
        raise NotFoundError(str(exc))
    except UserNotActiveError as exc:
        raise AuthorizationError(str(exc))

    request.state.audit.log(
        AuditEvent(
            AuthEvent.TOKEN_REFRESHED,
            user_id=str(result.user.id),
            email=result.user.email,
        )
    )
    return _format_auth_result(result)


@router.post(
    "/auth/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Send a password reset link",
)
async def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> dict:
    await auth_service.forgot_password(body.email)

    request.state.audit.log(
        AuditEvent(
            AuthEvent.PASSWORD_RESET_REQUESTED,
            email=body.email,
        )
    )
    return success_response({"message": "If an account with that email exists, a reset link has been sent"})


@router.post(
    "/auth/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Complete a password reset",
)
async def reset_password(
    body: ResetPasswordRequest,
    request: Request,
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> dict:
    try:
        await auth_service.reset_password(body.token, body.new_password)
    except InvalidTokenError as exc:
        request.state.audit.log(
            AuditEvent(
                AuthEvent.PASSWORD_RESET_COMPLETED,
                outcome="failure",
                failure_reason="invalid_or_expired_token",
            )
        )
        raise TokenError(str(exc))
    except UserNotFoundError as exc:
        raise NotFoundError(str(exc))
    except UserNotActiveError as exc:
        raise AuthorizationError(str(exc))

    request.state.audit.log(
        AuditEvent(
            AuthEvent.PASSWORD_RESET_COMPLETED,
        )
    )
    return success_response({"message": "Password has been reset successfully"})
