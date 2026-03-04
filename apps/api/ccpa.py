from fastapi import APIRouter, Depends

from api.dependencies import get_current_user_id, get_pool
from backend.domain.ccpa import CCPAComplianceManager

router = APIRouter()


@router.post("/data-access-request")
async def data_access_request(user_id: str = Depends(get_current_user_id), pool=Depends(get_pool)):
    async with pool.acquire() as conn:
        user_data = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        application_data = await conn.fetch("SELECT * FROM applications WHERE user_id = $1", user_id)
        return CCPAComplianceManager.handle_data_access_request(user_id, user_data, application_data)


@router.post("/data-deletion-request")
async def data_deletion_request(user_id: str = Depends(get_current_user_id)):
    return CCPAComplianceManager.handle_data_deletion_request(user_id)
