from fastapi import APIRouter, Depends

from api.dependencies import get_current_user_id, get_pool
from packages.backend.domain.ccpa import CCPAComplianceManager

router = APIRouter(prefix="/ccpa", tags=["CCPA Compliance"])


@router.post("/data-access-request")
async def data_access_request(
    user_id: str = Depends(get_current_user_id), pool=Depends(get_pool)
):
    """PRIV-004: CCPA Right to Know — full data inventory including answer_memory, application_inputs."""
    async with pool.acquire() as conn:
        user_data = await conn.fetchrow(
            "SELECT * FROM public.users WHERE id = $1", user_id
        )
        application_data = await conn.fetch(
            "SELECT * FROM public.applications WHERE user_id = $1", user_id
        )
        profile_data = await conn.fetchrow(
            "SELECT * FROM public.profiles WHERE user_id = $1", user_id
        )
        saved_jobs = await conn.fetch(
            "SELECT * FROM public.saved_jobs WHERE user_id = $1", user_id
        )
        cover_letters = await conn.fetch(
            "SELECT * FROM public.cover_letters WHERE user_id = $1", user_id
        )
        user_prefs = await conn.fetchrow(
            "SELECT * FROM public.user_preferences WHERE user_id = $1", user_id
        )
        answer_memory = await conn.fetch(
            "SELECT * FROM public.answer_memory WHERE user_id = $1", user_id
        )
        app_ids = [r["id"] for r in application_data] if application_data else []
        application_inputs = []
        if app_ids:
            application_inputs = await conn.fetch(
                """
                SELECT application_id, selector, question, field_type, answer,
                       resolved, created_at
                FROM public.application_inputs
                WHERE application_id = ANY($1::uuid[])
                ORDER BY created_at DESC
                """,
                app_ids,
            )
            application_inputs = [dict(r) for r in application_inputs]

        user_dict = dict(user_data) if user_data else {}
        app_list = [dict(app) for app in application_data] if application_data else []
        profile_dict = dict(profile_data) if profile_data else None
        saved_list = [dict(r) for r in saved_jobs] if saved_jobs else None
        cover_list = [dict(r) for r in cover_letters] if cover_letters else None
        prefs_dict = dict(user_prefs) if user_prefs else None
        answer_memory_list = [dict(r) for r in answer_memory] if answer_memory else None

        return CCPAComplianceManager.handle_data_access_request(
            user_id,
            user_data=user_dict,
            application_data=app_list,
            profile_data=profile_dict,
            saved_jobs=saved_list,
            cover_letters=cover_list,
            user_preferences=prefs_dict,
            answer_memory=answer_memory_list,
            application_inputs=application_inputs,
        )


@router.post("/data-deletion-request")
async def data_deletion_request(
    user_id: str = Depends(get_current_user_id), pool=Depends(get_pool)
):
    return await CCPAComplianceManager.handle_data_deletion_request(user_id, pool)
