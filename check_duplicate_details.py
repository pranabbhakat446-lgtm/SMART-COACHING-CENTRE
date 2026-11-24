from database import get_db

conn = get_db()

try:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, student_code, name, phone, email, created_at
            FROM students
            WHERE id IN (1, 3, 4, 5, 6, 16, 21, 22, 23, 27, 28, 30, 31)
            ORDER BY id;
        """)

        print("\nDUPLICATE STUDENT DETAILS:\n")

        for row in cur.fetchall():
            print(row)

finally:
    conn.close()