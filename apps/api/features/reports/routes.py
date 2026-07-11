from fastapi import APIRouter

router = APIRouter(tags=["reports"])


@router.get("/interviews/{interview_id}/evaluation")
async def get_evaluation():
    return {"message": "Not implemented"}


@router.post("/interviews/{interview_id}/evaluation")
async def generate_evaluation():
    return {"message": "Not implemented"}
