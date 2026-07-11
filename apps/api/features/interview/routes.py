from fastapi import APIRouter

router = APIRouter(tags=["interviews"])


@router.post("/interviews")
async def create_interview():
    return {"message": "Not implemented"}


@router.get("/interviews")
async def list_interviews():
    return {"message": "Not implemented"}


@router.get("/interviews/{interview_id}")
async def get_interview():
    return {"message": "Not implemented"}
