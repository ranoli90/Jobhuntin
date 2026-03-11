# PRIV-004: Expanded data inventory for CCPA "Right to Know" — align with GDPR export
DATA_INVENTORY = {
    "users": [
        "id",
        "email",
        "full_name",
        "headline",
        "bio",
        "resume_url",
        "created_at",
        "updated_at",
    ],
    "applications": [
        "id",
        "application_url",
        "status",
        "created_at",
        "updated_at",
        "submitted_at",
        "job_id",
        "job_title",
        "company",
    ],
    "profiles": ["user_id", "profile_data", "resume_url", "preferences", "updated_at"],
    "saved_jobs": ["user_id", "job_id", "saved_at"],
    "cover_letters": ["user_id", "job_id", "content", "created_at"],
    "user_preferences": [
        "user_id",
        "min_salary",
        "max_salary",
        "preferred_locations",
        "remote_only",
    ],
}


class CCPAComplianceManager:
    @staticmethod
    def _filter_by_inventory(data: dict | list, inventory_keys: list[str]) -> dict | list:
        """Filter dict or list of dicts to only include allowed keys."""
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if k in inventory_keys}
        return [
            {k: v for k, v in item.items() if k in inventory_keys}
            for item in data
        ]

    @staticmethod
    def handle_data_access_request(
        user_id: str,
        user_data: dict | None = None,
        application_data: list[dict] | None = None,
        profile_data: dict | None = None,
        saved_jobs: list[dict] | None = None,
        cover_letters: list[dict] | None = None,
        user_preferences: dict | None = None,
    ):
        """Handles a data access request by returning all data associated with the user."""
        result: dict = {
            "user": CCPAComplianceManager._filter_by_inventory(
                user_data or {}, DATA_INVENTORY["users"]
            ),
            "applications": CCPAComplianceManager._filter_by_inventory(
                application_data or [], DATA_INVENTORY["applications"]
            ),
        }
        if profile_data:
            result["profiles"] = CCPAComplianceManager._filter_by_inventory(
                profile_data, DATA_INVENTORY["profiles"]
            )
        if saved_jobs:
            result["saved_jobs"] = CCPAComplianceManager._filter_by_inventory(
                saved_jobs, DATA_INVENTORY["saved_jobs"]
            )
        if cover_letters:
            result["cover_letters"] = CCPAComplianceManager._filter_by_inventory(
                cover_letters, DATA_INVENTORY["cover_letters"]
            )
        if user_preferences:
            result["user_preferences"] = CCPAComplianceManager._filter_by_inventory(
                user_preferences, DATA_INVENTORY["user_preferences"]
            )
        return result

    @staticmethod
    async def handle_data_deletion_request(user_id: str, db_pool):
        """Handles a data deletion request by actually deleting user data."""

        deleted_tables = {}
        errors = []

        try:
            async with db_pool.acquire() as conn:
                # Begin transaction for atomic deletion
                async with conn.transaction():
                    # Delete from tables in order of dependency (child tables first)
                    tables_to_delete = [
                        ("public.analytics_events", "user_id"),
                        ("public.input_answers", "user_id"),
                        ("public.cover_letters", "user_id"),
                        ("public.saved_jobs", "user_id"),
                        ("public.profile_embeddings", "user_id"),
                        ("public.user_preferences", "user_id"),
                        ("public.applications", "user_id"),
                        ("public.profiles", "user_id"),
                        ("public.billing_customers", "user_id"),
                        ("public.tenant_members", "user_id"),
                        ("public.users", "id"),
                    ]

                    for table, user_col in tables_to_delete:
                        try:
                            # PRIV-003: Remove profile from vector DB before deleting profile_embeddings
                            if table == "public.profile_embeddings":
                                try:
                                    from packages.backend.domain.semantic_matching import (
                                        get_matching_service,
                                    )

                                    svc = get_matching_service()
                                    await svc.remove_profile(user_id, conn=conn)
                                except Exception as ve:
                                    errors.append(f"profile_embeddings(vector): {str(ve)}")

                            # PRIV-002: Delete resume file from storage before deleting profile
                            if table == "public.profiles":
                                try:
                                    row = await conn.fetchrow(
                                        "SELECT resume_url FROM public.profiles WHERE user_id = $1",
                                        user_id,
                                    )
                                    if row and row.get("resume_url"):
                                        from shared.storage import get_storage_service

                                        storage = get_storage_service()
                                        await storage.delete_file(row["resume_url"])
                                except Exception as se:
                                    errors.append(f"profiles(resume_file): {str(se)}")

                            # Use parameterized query to prevent SQL injection
                            result = await conn.execute(
                                f"DELETE FROM {table} WHERE {user_col} = $1", user_id
                            )
                            deleted_count = int(result.split()[-1]) if result else 0
                            deleted_tables[table] = deleted_count
                        except Exception as e:
                            error_msg = f"{table}: {str(e)}"
                            errors.append(error_msg)

        except Exception as e:
            errors.append(f"database_error: {str(e)}")

        return {
            "status": "completed" if not errors else "partial",
            "deleted_tables": deleted_tables,
            "errors": errors,
            "user_id": user_id,
            "deleted_records_total": sum(deleted_tables.values()),
        }
