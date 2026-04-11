"""
Export all data from local SQLite database to JSON files for backup/migration.
"""
import os
import sys
import json
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'thepulse.db')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'export')


def export_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row['name'] for row in cursor.fetchall()]

    summary = {}
    for table in tables:
        cursor.execute(f'SELECT * FROM "{table}"')
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]

        # Convert non-serializable types
        for row in data:
            for k, v in row.items():
                if isinstance(v, bytes):
                    row[k] = v.hex()

        filepath = os.path.join(OUTPUT_DIR, f'{table}.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        summary[table] = len(data)
        print(f"  {table}: {len(data)} rows → {filepath}")

    conn.close()

    # Save summary
    with open(os.path.join(OUTPUT_DIR, '_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\nTotal: {sum(summary.values())} rows across {len(summary)} tables")
    print(f"Exported to: {OUTPUT_DIR}")


if __name__ == '__main__':
    export_all()
