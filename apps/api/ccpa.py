"""
CCPA Compliance API endpoints — California Consumer Privacy Act rights.
"""

from __future__ import annotations

from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from backend.domain.ccpa import (
    CCPAComplianceManager,
    CCPARequestType,
    CCPARequestStatus,
    DATA_INVENTORY,
)
from shared.logging_config import get_logger

logger = get_logger("sorce.api.ccpa")

router = APIRouter(prefix="/ccpa", tags=["ccpa"])


def _get_pool():
    raise NotImplementedError("Pool dependency not injected")


async def _get_user_id() -> str:
    raise NotImplementedError("User ID dependency not injected")


class SubmitRequestRequest(BaseModel):
    request_type: str
    email: EmailStr
    phone: str | None = None
    details: dict[str, Any] | None = None


class SubmitRequestResponse(BaseModel):
    request_id: str
    request_type: str
    status: str
    message: str


class VerifyRequestRequest(BaseModel):
    request_id: str
    verification_code: str


class RequestStatusResponse(BaseModel):
    request_id: str
    request_type: str
    status: str
    created_at: str
    verified_at: str | None
    completed_at: str | None
    response: dict[str, Any] | None


class OptOutRequest(BaseModel):
    do_not_sell: bool


class DataInventoryResponse(BaseModel):
    categories: list[dict[str, Any]]
    third_parties: list[dict[str, Any]]


@router.post("/requests", response_model=SubmitRequestResponse)
async def submit_ccpa_request(
    body: SubmitRequestRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str | None = Depends(_get_user_id),
) -> SubmitRequestResponse:
    manager = CCPAComplianceManager(db)

    try:
        request_type = CCPARequestType(body.request_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request type. Valid types: {[t.value for t in CCPARequestType]}",
        )

    request = await manager.submit_request(
        request_type=request_type,
        email=body.email,
        phone=body.phone,
        user_id=user_id,
        details=body.details,
    )

    return SubmitRequestResponse(
        request_id=request.id,
        request_type=request.request_type.value,
        status=request.status.value,
        message="Your CCPA request has been submitted. You will receive a verification email.",
    )


@router.post("/requests/verify", response_model=RequestStatusResponse)
async def verify_ccpa_request(
    body: VerifyRequestRequest,
    db: asyncpg.Pool = Depends(_get_pool),
) -> RequestStatusResponse:
    manager = CCPAComplianceManager(db)

    success, request = await manager.verify_request(
        body.request_id,
        body.verification_code,
    )

    if not success or not request:
        raise HTTPException(
            status_code=400, detail="Invalid verification code or request"
        )

    return RequestStatusResponse(
        request_id=request.id,
        request_type=request.request_type.value,
        status=request.status.value,
        created_at=request.created_at.isoformat(),
        verified_at=request.verified_at.isoformat() if request.verified_at else None,
        completed_at=request.completed_at.isoformat() if request.completed_at else None,
        response=request.response,
    )


@router.get("/requests/{request_id}", response_model=RequestStatusResponse)
async def get_request_status(
    request_id: str,
    db: asyncpg.Pool = Depends(_get_pool),
) -> RequestStatusResponse:
    manager = CCPAComplianceManager(db)

    request = await manager.get_request_status(request_id)

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    return RequestStatusResponse(
        request_id=request.id,
        request_type=request.request_type.value,
        status=request.status.value,
        created_at=request.created_at.isoformat(),
        verified_at=request.verified_at.isoformat() if request.verified_at else None,
        completed_at=request.completed_at.isoformat() if request.completed_at else None,
        response=request.response,
    )


@router.get("/data-inventory", response_model=DataInventoryResponse)
async def get_data_inventory() -> DataInventoryResponse:
    return DataInventoryResponse(
        categories=[
            {
                "category": cat.category,
                "description": cat.description,
                "sources": cat.sources,
                "purposes": cat.purposes,
                "disclosed_to": cat.disclosed_to,
                "retention_days": cat.retention_days,
                "is_sold": cat.is_sold,
            }
            for cat in DATA_INVENTORY
        ],
        third_parties=[
            {"name": "Stripe", "purpose": "Payment processing", "data": "Billing info"},
            {"name": "Resend", "purpose": "Email delivery", "data": "Email address"},
            {"name": "OpenAI", "purpose": "AI matching", "data": "Job preferences"},
            {
                "name": "Job Boards",
                "purpose": "Job sourcing",
                "data": "Resume (with consent)",
            },
        ],
    )


@router.post("/opt-out")
async def set_opt_out_preference(
    body: OptOutRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
) -> dict[str, str]:
    manager = CCPAComplianceManager(db)

    await manager.set_opt_out_preference(user_id, body.do_not_sell)

    return {
        "status": "updated",
        "do_not_sell": str(body.do_not_sell).lower(),
    }


@router.get("/opt-out")
async def get_opt_out_status(
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
) -> dict[str, Any]:
    manager = CCPAComplianceManager(db)

    opted_out = await manager.get_user_opt_out_status(user_id)

    return {
        "do_not_sell": opted_out,
    }


@router.post("/requests/{request_id}/process")
async def process_ccpa_request(
    request_id: str,
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    manager = CCPAComplianceManager(db)

    request = await manager.process_request(request_id)

    if not request:
        raise HTTPException(status_code=404, detail="Request not found or not verified")

    return {
        "request_id": request.id,
        "status": request.status.value,
        "response": request.response,
    }
