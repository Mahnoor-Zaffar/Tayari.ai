from fastapi import APIRouter

router = APIRouter(tags=["users"])


@router.get("/users/me")
async def get_current_user():
    return {"message": "Not implemented"}


@router.patch("/users/me")
async def update_user():
    return {"message": "Not implemented"}
