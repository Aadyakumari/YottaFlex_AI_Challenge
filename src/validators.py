
import json
import sqlite3
from pathlib import Path

from database import DB_PATH

BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "data" / "reports"


def run_validations():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    results = {}

    try:
        cursor = connection.cursor()

        # 1. Database integrity check.
        integrity = cursor.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        results["database_integrity"] = {
            "status": "PASS" if integrity == "ok" else "FAIL",
            "details": integrity
        }

        # 2. Foreign key validation.
        foreign_key_errors = cursor.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        results["foreign_key_violations"] = {
            "status": "PASS" if not foreign_key_errors else "FAIL",
            "count": len(foreign_key_errors)
        }

        # 3. Detect payment over-allocation.
        over_allocations = cursor.execute("""
            SELECT
                il.invoice_line_id,
                il.amount_paise AS invoice_amount,
                SUM(pa.allocated_amount_paise) AS allocated_amount
            FROM invoice_lines il
            JOIN payment_allocations pa
                ON il.invoice_line_id = pa.invoice_line_id
            JOIN payments p
                ON pa.payment_id = p.payment_id
            WHERE p.status = 'RECEIVED'
            GROUP BY il.invoice_line_id, il.amount_paise
            HAVING SUM(pa.allocated_amount_paise) > il.amount_paise
        """).fetchall()

        results["payment_over_allocations"] = {
            "status": "PASS" if not over_allocations else "FAIL",
            "count": len(over_allocations),
            "records": [dict(row) for row in over_allocations]
        }

        # 4. Detect scholarship awards exceeding invoice fees.
        scholarship_errors = cursor.execute("""
            SELECT
                e.eligibility_id,
                e.enrollment_id,
                e.award_amount_paise,
                COALESCE(SUM(il.amount_paise), 0) AS eligible_fees
            FROM eligibility e
            JOIN enrollments en
                ON e.enrollment_id = en.enrollment_id
            LEFT JOIN invoices i
                ON en.enrollment_id = i.enrollment_id
            LEFT JOIN invoice_lines il
                ON i.invoice_id = il.invoice_id
            WHERE e.decision = 'ELIGIBLE'
            GROUP BY
                e.eligibility_id,
                e.enrollment_id,
                e.award_amount_paise
            HAVING e.award_amount_paise >
                COALESCE(SUM(il.amount_paise), 0)
        """).fetchall()

        results["scholarship_exceeds_fees"] = {
            "status": "PASS" if not scholarship_errors else "FAIL",
            "count": len(scholarship_errors),
            "records": [dict(row) for row in scholarship_errors]
        }

        # 5. Detect duplicate invoices for the same enrollment.
        duplicate_invoices = cursor.execute("""
            SELECT
                enrollment_id,
                COUNT(*) AS invoice_count,
                GROUP_CONCAT(invoice_id) AS invoice_ids
            FROM invoices
            GROUP BY enrollment_id
            HAVING COUNT(*) > 1
        """).fetchall()

        results["duplicate_invoices"] = {
            "status": "PASS" if not duplicate_invoices else "FAIL",
            "count": len(duplicate_invoices),
            "records": [dict(row) for row in duplicate_invoices]
        }

        # 6. Detect refunds exceeding the original received payment.
        refund_errors = cursor.execute("""
            SELECT
                p.payment_id,
                p.amount_paise AS payment_amount,
                SUM(r.amount_paise) AS refunded_amount
            FROM payments p
            JOIN refunds r
                ON p.payment_id = r.payment_id
            WHERE p.status = 'RECEIVED'
              AND r.status = 'PROCESSED'
            GROUP BY p.payment_id, p.amount_paise
            HAVING SUM(r.amount_paise) > p.amount_paise
        """).fetchall()

        results["refund_exceeds_net_paid"] = {
            "status": "PASS" if not refund_errors else "FAIL",
            "count": len(refund_errors),
            "records": [dict(row) for row in refund_errors]
        }

        # 7. Detect invoice total and invoice-line mismatches.
        ledger_errors = cursor.execute("""
            SELECT
                i.invoice_id,
                i.total_amount_paise,
                COALESCE(SUM(il.amount_paise), 0) AS line_total
            FROM invoices i
            LEFT JOIN invoice_lines il
                ON i.invoice_id = il.invoice_id
            GROUP BY i.invoice_id, i.total_amount_paise
            HAVING i.total_amount_paise !=
                COALESCE(SUM(il.amount_paise), 0)
        """).fetchall()

        results["invoice_ledger_mismatch"] = {
            "status": "PASS" if not ledger_errors else "FAIL",
            "count": len(ledger_errors),
            "records": [dict(row) for row in ledger_errors]
        }

        # 8. Overall validation summary.
        failed_checks = [
            name for name, result in results.items()
            if result["status"] == "FAIL"
        ]

        summary = {
            "overall_status": "PASS" if not failed_checks else "FAIL",
            "total_checks": len(results),
            "passed_checks": len(results) - len(failed_checks),
            "failed_checks": failed_checks,
            "results": results
        }

        report_path = REPORT_DIR / "validation_report.json"

        with open(report_path, "w", encoding="utf-8") as file:
            json.dump(summary, file, indent=4)

        print("\nVALIDATION SUMMARY")
        print("------------------")

        for name, result in results.items():
            print(f"{name}: {result['status']}")

        print("\nOverall status:", summary["overall_status"])
        print("Report saved to:", report_path)

        return summary

    finally:
        connection.close()


if __name__ == "__main__":
    run_validations()
