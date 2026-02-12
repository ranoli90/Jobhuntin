import psycopg2
import os
from dotenv import load_dotenv

def list_tables():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found")
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("SELECT current_user, current_database();")
        user, db = cur.fetchone()
        print(f"Connected as {user} to database {db}")

        cur.execute("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_schema, table_name;
        """)
        tables = cur.fetchall()
        print(f"Found {len(tables)} tables:")
        for t in tables:
            print(f"- {t[0]}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_tables()
