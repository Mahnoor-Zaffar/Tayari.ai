from fastapi import APIRouter

router = APIRouter(tags=["auth"])


@router.post("/auth/signup")
async def signup():
    return {"message": "Not implemented"}


@router.post("/auth/login")
async def login():
    return {"message": "Not implemented"}


@router.post("/auth/logout")
async def logout():
    return {"message": "Not implemented"}


@router.post("/auth/refresh")
async def refresh():
    return {"message": "Not implemented"}


@router.post("/auth/forgot-password")
async def forgot_password():
    return {"message": "Not implemented"}


@router.post("/auth/reset-password")
async def reset_password():
    return {"message": "Not implemented"}
