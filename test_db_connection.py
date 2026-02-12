import psycopg2
import os
from dotenv import load_dotenv

def test_connection():
    """Test the DATABASE_URL connection from .env"""
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        print("❌ DATABASE_URL not found in .env")
        return False

    print("Testing DATABASE_URL connection...")
    # Mask password for security in logs
    masked_url = db_url.split("@")[1] if "@" in db_url else "..."
    print(f"Connecting to: ...@{masked_url}")
    print()

    try:
        conn = psycopg2.connect(db_url)
        conn.close()
        print("✅ Connection successful!")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
