import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "student_fees.db"


def test_database_integrity():
    with sqlite3.connect(DB_PATH) as con:
        result = con.execute("PRAGMA integrity_check").fetchone()[0]
    assert result == "ok"


def test_no_foreign_key_violations():
    with sqlite3.connect(DB_PATH) as con:
        violations = con.execute("PRAGMA foreign_key_check").fetchall()
    assert violations == []


def test_required_baseline_record_counts():
    expected = {
        "students": 10000,
        "programs": 20,
        "invoices": 30000,
        "eligibility": 15000,
        "payments": 50000,
    }

    with sqlite3.connect(DB_PATH) as con:
        for table, count in expected.items():
            actual = con.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            assert actual == count, (
                f"{table}: expected {count}, got {actual}"
            )


def test_validation_report_passed():
    report_path = BASE_DIR / "data" / "reports" / "validation_report.json"

    with open(report_path, encoding="utf-8") as file:
        report = json.load(file)

    assert report["overall_status"] == "PASS"
    assert len(report["failed_checks"]) == 0


def test_csv_and_json_exports_exist():
    output_dir = BASE_DIR / "data" / "generated"

    for table in [
        "students", "programs", "fee_schedules", "enrollments",
        "invoices", "invoice_lines", "scholarships", "eligibility",
        "payments", "payment_allocations", "refunds"
    ]:
        assert (output_dir / f"{table}.csv").exists()
        assert (output_dir / f"{table}.json").exists()



