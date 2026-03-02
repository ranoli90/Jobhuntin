import asyncpg
import stripe
from fastapi import APIRouter, Depends, HTTPException

from apps.api.dependencies import get_current_user_id, get_pool
from backend.domain.services.user_service import get_current_user

router = APIRouter()


@router.get("/invoices")
async def get_invoices(user_id: str = Depends(get_current_user_id), pool: asyncpg.Pool = Depends(get_pool)):
    async with pool.acquire() as conn:
        user = await get_current_user(user_id, conn)
        if not user.get("stripe_customer_id"):
            return []

        try:
            invoices = stripe.Invoice.list(customer=user["stripe_customer_id"])
            return invoices["data"]
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))
