"""
One-off cleanup script: removes duplicate rows from test_availabilities and stocks.

For each table, finds groups with the same (phc_id, test_name/medicine_id, date),
keeps the latest row (highest id) per group, and deletes the rest.

Usage:
    python data/dedupe_cleanup.py
"""
import os
import sys

# Add backend to path so we can use the same connection
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

from app.database.connection import engine
from sqlalchemy import text


def cleanup_table(table_name, group_columns):
    """Remove duplicate rows, keeping the one with the highest id per group."""
    col_list = ", ".join(group_columns)

    with engine.connect() as conn:
        # Before count
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        before = result.fetchone()[0]

        # Find duplicate groups
        dup_query = text(f"""
            SELECT {col_list}, COUNT(*) as cnt
            FROM {table_name}
            GROUP BY {col_list}
            HAVING COUNT(*) > 1
        """)
        dup_groups = conn.execute(dup_query).fetchall()

        if not dup_groups:
            print(f"  {table_name}: No duplicates found ({before} rows)")
            return before, before

        total_deleted = 0
        for group in dup_groups:
            # Build WHERE clause for this group
            conditions = " AND ".join(
                f"{col} = :{col}" for col in group_columns
            )
            params = {col: val for col, val in zip(group_columns, group)}

            # Delete all but the highest-id row
            delete_sql = text(f"""
                DELETE FROM {table_name}
                WHERE {conditions}
                AND id NOT IN (
                    SELECT MAX(id) FROM {table_name}
                    WHERE {conditions}
                    GROUP BY {col_list}
                )
            """)
            result = conn.execute(delete_sql, params)
            total_deleted += result.rowcount

        conn.commit()

        # After count
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        after = result.fetchone()[0]

        print(f"  {table_name}: {before} -> {after} rows (deleted {total_deleted} duplicates)")
        return before, after


if __name__ == "__main__":
    print("=" * 60)
    print("Deduplication Cleanup Script")
    print("=" * 60)
    print(f"Database: {engine.url}")
    print()

    print("Cleaning test_availabilities...")
    cleanup_table("test_availabilities", ["phc_id", "test_name", "date"])

    print("Cleaning stocks...")
    cleanup_table("stocks", ["phc_id", "medicine_id", "date"])

    print()
    print("✓ Cleanup complete!")
