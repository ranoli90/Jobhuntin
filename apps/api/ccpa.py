from api.dependencies import get_current_user_id, get_pool
from fastapi import APIRouter, Depends

from backend.domain.ccpa import CCPAComplianceManager

router = APIRouter()


@router.post("/data-access-request")
async def data_access_request(
    user_id: str = Depends(get_current_user_id), pool=Depends(get_pool)
):
    async with pool.acquire() as conn:
        user_data = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        application_data = await conn.fetch(
            "SELECT * FROM applications WHERE user_id = $1", user_id
        )

        # Handle None user_data and application_data gracefully
        user_dict = dict(user_data) if user_data else {}
        app_list = [dict(app) for app in application_data] if application_data else []

        return CCPAComplianceManager.handle_data_access_request(
            user_id, user_dict, app_list
        )


@router.post("/data-deletion-request")
async def data_deletion_request(
    user_id: str = Depends(get_current_user_id), pool=Depends(get_pool)
):
    return await CCPAComplianceManager.handle_data_deletion_request(user_id, pool)
