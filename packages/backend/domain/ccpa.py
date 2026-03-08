DATA_INVENTORY = {
    "users": ["email", "full_name", "headline", "bio", "resume_url"],
    "applications": ["status", "created_at", "submitted_at"],
}


class CCPAComplianceManager:
    @staticmethod
    def handle_data_access_request(
        user_id: str, user_data: dict | None, application_data: list[dict] | None
    ):
        """Handles a data access request by returning all data associated with the user."""
        if not user_data:
            user_data = {}
        if not application_data:
            application_data = []

        return {
            "user": {
                k: v for k, v in user_data.items() if k in DATA_INVENTORY["users"]
            },
            "applications": [
                {k: v for k, v in app.items() if k in DATA_INVENTORY["applications"]}
                for app in application_data
            ],
        }

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
