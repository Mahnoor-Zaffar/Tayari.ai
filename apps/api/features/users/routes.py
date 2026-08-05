from uuid import UUID

from fastapi import APIRouter, Depends, Query

from core.errors import NotFoundError, success_response
from features.auth.guard import CurrentUser, RoleChecker
from features.users.dependencies import get_user_service
from features.users.schemas import UpdateUserRequest, UserProfileResponse
from features.users.service import UserService

router = APIRouter(tags=["users"])


# ── Current user (non-admin) ────────────────────────────────────────────────


@router.get("/users/me")
async def get_current_user(
    current_user: CurrentUser = Depends(RoleChecker("user", "admin")),
) -> dict:
    return success_response(
        UserProfileResponse(
            id=current_user.id,
            email=current_user.email,
            display_name=current_user.display_name,
            email_verified=current_user.email_verified,
            created_at=current_user.created_at if hasattr(current_user, "created_at") else None,
        )
    )


@router.patch("/users/me")
async def update_current_user(
    data: UpdateUserRequest,
    current_user: CurrentUser = Depends(RoleChecker("user", "admin")),
    service: UserService = Depends(get_user_service),
) -> dict:
    result = await service.update_user(current_user.id, data)
    if result is None:
        raise NotFoundError("User not found")
    return success_response(result)


@router.delete("/users/me", summary="Soft-delete the current user's account")
async def delete_current_user(
    current_user: CurrentUser = Depends(RoleChecker("user", "admin")),
    service: UserService = Depends(get_user_service),
) -> dict:
    await service.delete_user(current_user.id)
    return success_response({"deleted": True})


# ── Admin: user management ──────────────────────────────────────────────────


@router.get("/users", summary="List all users (admin)")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: str | None = Query(None),
    _admin: CurrentUser = Depends(RoleChecker("admin")),
    service: UserService = Depends(get_user_service),
) -> dict:
    result = await service.list_users(skip=skip, limit=limit, search=search)
    return success_response(result)


@router.get("/users/{user_id}", summary="Get user details (admin)")
async def get_user(
    user_id: UUID,
    _admin: CurrentUser = Depends(RoleChecker("admin")),
    service: UserService = Depends(get_user_service),
) -> dict:
    result = await service.get_user(user_id)
    if result is None:
        raise NotFoundError("User not found")
    return success_response(result)


@router.patch("/users/{user_id}", summary="Update user (admin)")
async def update_user(
    user_id: UUID,
    data: UpdateUserRequest,
    _admin: CurrentUser = Depends(RoleChecker("admin")),
    service: UserService = Depends(get_user_service),
) -> dict:
    result = await service.update_user(user_id, data)
    if result is None:
        raise NotFoundError("User not found")
    return success_response(result)


@router.delete("/users/{user_id}", summary="Soft-delete user (admin)")
async def delete_user(
    user_id: UUID,
    _admin: CurrentUser = Depends(RoleChecker("admin")),
    service: UserService = Depends(get_user_service),
) -> dict:
    await service.delete_user(user_id)
    return success_response({"deleted": True})
