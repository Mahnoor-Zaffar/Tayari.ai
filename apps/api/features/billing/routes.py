from fastapi import APIRouter

router = APIRouter(tags=["billing"])


@router.post("/billing/create-checkout")
async def create_checkout():
    return {"message": "Not implemented"}


@router.get("/billing/portal")
async def billing_portal():
    return {"message": "Not implemented"}


@router.get("/billing/subscription")
async def get_subscription():
    return {"message": "Not implemented"}


@router.post("/billing/webhook")
async def stripe_webhook():
    return {"message": "Not implemented"}
