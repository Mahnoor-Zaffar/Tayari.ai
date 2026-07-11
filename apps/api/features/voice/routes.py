from fastapi import APIRouter

router = APIRouter(tags=["voice"])


@router.websocket("/voice/stream/{interview_id}")
async def voice_stream():
    pass  # WebSocket handler for voice chunks
