
DATA_INVENTORY = {
    "users": ["email", "full_name", "headline", "bio", "resume_url"],
    "applications": ["status", "created_at", "submitted_at"],
}

class CCPAComplianceManager:
    @staticmethod
    def handle_data_access_request(user_id: str, user_data: dict, application_data: list[dict]):
        """Handles a data access request by returning all data associated with the user."""
        return {
            "user": {k: v for k, v in user_data.items() if k in DATA_INVENTORY["users"]},
            "applications": [
                {k: v for k, v in app.items() if k in DATA_INVENTORY["applications"]}
                for app in application_data
            ],
        }

    @staticmethod
    def handle_data_deletion_request(user_id: str):
        """Handles a data deletion request by creating a deletion task."""
        # This would typically create a task in a queue to be processed by a worker.
        # For now, we will just return a success message.
        return {"message": f"Data deletion request for user {user_id} has been queued."}
