
from database import get_db

# Keep the original student records
keep_ids = [1, 3, 21, 27, 30]

# Delete only confirmed duplicate records
delete_ids = [4, 5, 6, 16, 22, 23, 28, 31]

conn = get_db()

try:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM students WHERE id = ANY(%s) ORDER BY id",
            (delete_ids,)
        )

        found_ids = [row["id"] for row in cur.fetchall()]

        if sorted(found_ids) != sorted(delete_ids):
            raise Exception("ID verification failed. No records deleted.")

        cur.execute(
            "DELETE FROM students WHERE id = ANY(%s)",
            (delete_ids,)
        )

        print("Deleted duplicate records:", cur.rowcount)

    conn.commit()
    print("SUCCESS: Duplicate students deleted.")

except Exception as e:
    conn.rollback()
    print("ERROR:", e)

finally:
    conn.close()

