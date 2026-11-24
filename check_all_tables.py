from database import get_db

conn = get_db()

try:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
        """)

        for row in cur.fetchall():
            print(row)

finally:
    conn.close()