from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status

from core.errors import AppError, ErrorCode, success_response
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
from features.auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, UserResponse
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
    except EmailAlreadyExistsError as exc:
        raise AppError(ErrorCode.CONFLICT, str(exc), status.HTTP_409_CONFLICT)
    except UsernameAlreadyExistsError as exc:
        raise AppError(ErrorCode.CONFLICT, str(exc), status.HTTP_409_CONFLICT)

    log.info("user registered", extra={"user_id": str(result.user.id), "email": result.user.email})
    return _format_auth_result(result)


@router.post(
    "/auth/login",
    status_code=status.HTTP_200_OK,
    summary="Authenticate with email and password",
)
async def login(
    body: LoginRequest,
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> dict:
    try:
        result = await auth_service.login(body.email, body.password)
    except InvalidCredentialsError:
        log.warning("failed login attempt", extra={"email": body.email})
        raise AppError(
            ErrorCode.UNAUTHORIZED,
            "Invalid email or password",
            status.HTTP_401_UNAUTHORIZED,
        )
    except UserNotActiveError as exc:
        log.warning("login blocked — inactive account", extra={"email": body.email})
        raise AppError(ErrorCode.FORBIDDEN, str(exc), status.HTTP_403_FORBIDDEN)

    log.info("user logged in", extra={"user_id": str(result.user.id), "email": result.user.email})
    return _format_auth_result(result)


@router.post("/auth/logout")
async def logout():
    return {"message": "Not implemented"}


@router.post(
    "/auth/refresh",
    status_code=status.HTTP_200_OK,
    summary="Issue new access and refresh tokens via a refresh token",
)
async def refresh(
    body: RefreshRequest,
    auth_service: AuthenticationService = Depends(get_auth_service),
    token_service: TokenService = Depends(get_token_service),
) -> dict:
    try:
        result = await auth_service.refresh(body.refresh_token)
    except InvalidTokenError:
        # Check whether the token was rejected because it was revoked
        # (rotation reuse) vs. expired / malformed.
        claims = token_service.peek(body.refresh_token)
        family = claims.get("token_family", "")
        if family:
            expires_at = datetime.fromtimestamp(claims.get("exp", 0), tz=UTC)
            await token_service.revoke_family(family, expires_at)
            log.warning(
                "refresh token reused — possible replay attack, family revoked",
                extra={"token_family": family, "email": claims.get("sub", "")},
            )
        raise AppError(
            ErrorCode.INVALID_TOKEN,
            "Invalid or expired refresh token",
            status.HTTP_401_UNAUTHORIZED,
        )
    except UserNotFoundError as exc:
        raise AppError(ErrorCode.NOT_FOUND, str(exc), status.HTTP_404_NOT_FOUND)
    except UserNotActiveError as exc:
        raise AppError(ErrorCode.FORBIDDEN, str(exc), status.HTTP_403_FORBIDDEN)

    log.info(
        "token refresh succeeded",
        extra={"user_id": str(result.user.id), "email": result.user.email},
    )
    return _format_auth_result(result)


@router.post("/auth/forgot-password")
async def forgot_password():
    return {"message": "Not implemented"}


@router.post("/auth/reset-password")
async def reset_password():
    return {"message": "Not implemented"}
