from database import get_db

conn = get_db()

try:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                LOWER(TRIM(name)) AS student_name,
                REGEXP_REPLACE(TRIM(phone), '[^0-9]', '', 'g') AS mobile,
                COUNT(*) AS total_entries,
                ARRAY_AGG(id ORDER BY created_at ASC NULLS LAST, id ASC) AS student_ids
            FROM students
            WHERE NULLIF(TRIM(name), '') IS NOT NULL
              AND NULLIF(TRIM(phone), '') IS NOT NULL
            GROUP BY
                LOWER(TRIM(name)),
                REGEXP_REPLACE(TRIM(phone), '[^0-9]', '', 'g')
            HAVING COUNT(*) > 1
            ORDER BY total_entries DESC
        """)

        results = cur.fetchall()

        if results:
            print("\nDUPLICATE STUDENTS FOUND:\n")
            for row in results:
                print(row)
        else:
            print("No duplicate students found.")

finally:
    conn.close()