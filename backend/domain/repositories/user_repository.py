from backend.domain.repositories import db_transaction


class UserRepository:
    @staticmethod
    async def get_by_id(conn, user_id: str):
        async with db_transaction(conn) as conn:
            return await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)

    @staticmethod
    async def create(conn, email: str, password_hash: str, stripe_customer_id: str):
        async with db_transaction(conn) as conn:
            return await conn.fetchrow(
                "INSERT INTO users (email, password_hash, stripe_customer_id) VALUES ($1, $2, $3) RETURNING *",
                email,
                password_hash,
                stripe_customer_id,
            )
