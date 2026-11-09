import csv
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from database import DB_PATH

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "generated"
REPORT_DIR = BASE_DIR / "data" / "reports"

SEED = 20261022

TABLES = [
    "students",
    "programs",
    "fee_schedules",
    "enrollments",
    "invoices",
    "invoice_lines",
    "scholarships",
    "eligibility",
    "payments",
    "payment_allocations",
    "refunds",
    "event_history",
    "late_fee_assessments"
]


def calculate_checksum(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def export_data():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    manifest = {
        "project": "Student Finance Data Generator",
        "seed": SEED,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "database": DB_PATH.name,
        "tables": {}
    }

    try:
        cursor = connection.cursor()

        for table in TABLES:
            rows = cursor.execute(
                f"SELECT * FROM {table} ORDER BY 1"
            ).fetchall()

            records = [dict(row) for row in rows]

            columns = [
                column[1]
                for column in cursor.execute(
                    f"PRAGMA table_info({table})"
                ).fetchall()
            ]

            csv_path = OUTPUT_DIR / f"{table}.csv"
            json_path = OUTPUT_DIR / f"{table}.json"

            with open(
                csv_path, "w", newline="", encoding="utf-8"
            ) as file:
                writer = csv.DictWriter(file, fieldnames=columns)
                writer.writeheader()
                writer.writerows(records)

            with open(json_path, "w", encoding="utf-8") as file:
                json.dump(records, file, indent=4)

            manifest["tables"][table] = {
                "record_count": len(records),
                "csv_file": csv_path.name,
                "json_file": json_path.name,
                "csv_sha256": calculate_checksum(csv_path),
                "json_sha256": calculate_checksum(json_path)
            }

            print(f"Exported {table}: {len(records)} records")

        anomaly_path = REPORT_DIR / "anomaly_manifest.json"

        if anomaly_path.exists():
            manifest["anomaly_manifest"] = str(
                anomaly_path.relative_to(BASE_DIR)
            )

        manifest_path = OUTPUT_DIR / "source_manifest.json"

        with open(manifest_path, "w", encoding="utf-8") as file:
            json.dump(manifest, file, indent=4)

        print("\nEXPORT COMPLETED SUCCESSFULLY")
        print("Total tables exported:", len(TABLES))
        print("Output directory:", OUTPUT_DIR)

    finally:
        connection.close()


if __name__ == "__main__":
    export_data()
