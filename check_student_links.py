from database import get_db

conn = get_db()

try:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS referenced_table,
                ccu.column_name AS referenced_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.constraint_schema = kcu.constraint_schema
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.constraint_schema = tc.constraint_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND ccu.table_name = 'students';
        """)

        rows = cur.fetchall()

        print("\nSTUDENT TABLE REFERENCES:\n")

        if rows:
            for row in rows:
                print(row)
        else:
            print("No foreign key references found.")

finally:
    conn.close()