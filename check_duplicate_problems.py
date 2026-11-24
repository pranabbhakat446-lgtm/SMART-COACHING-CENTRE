from database import get_db

conn = get_db()

try:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, student_name, student_code, category, status
            FROM problems
            WHERE student_code IN (
                '01', '03', '04', '05', '06',
                '16', '21', '22', '23',
                '27', '28', '30', '31'
            )
            ORDER BY id;
        """)

        rows = cur.fetchall()

        if rows:
            for row in rows:
                print(row)
        else:
            print("No related problem records found.")

finally:
    conn.close()