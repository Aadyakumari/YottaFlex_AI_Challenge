
import json
import sqlite3
from pathlib import Path

from database import DB_PATH

BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "data" / "reports"


def inject_anomalies():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    anomaly_manifest = []

    try:
        cursor = connection.cursor()

        # Confirm that the expected baseline records exist.
        required_records = [
            ("payments", "payment_id", "PAY000001"),
            ("invoice_lines", "invoice_line_id", "LINE000001"),
            ("eligibility", "eligibility_id", "ELG000001"),
            ("invoices", "invoice_id", "INV000001"),
            ("invoices", "invoice_id", "INV000002"),
        ]

        for table, column, record_id in required_records:
            record = cursor.execute(
                f"SELECT 1 FROM {table} WHERE {column} = ?",
                (record_id,)
            ).fetchone()

            if record is None:
                raise ValueError(
                    f"Required baseline record missing: {record_id}"
                )

        # CASE 1: Payment over-allocation.
        cursor.execute("""
            INSERT OR IGNORE INTO payment_allocations
            (allocation_id, payment_id, invoice_line_id,
             allocated_amount_paise, allocated_at)
            VALUES (
                'ANOM-ALLOC-001',
                'PAY000001',
                'LINE000001',
                1,
                '2026-01-01'
            )
        """)

        anomaly_manifest.append({
            "case_id": "ANOMALY_001",
            "type": "PAYMENT_OVER_ALLOCATION",
            "description": "An extra allocation causes the invoice line to be over-allocated.",
            "record_id": "LINE000001"
        })

        # CASE 2: Scholarship award exceeds eligible fees.
        cursor.execute("""
            UPDATE eligibility
            SET award_amount_paise = 99000000
            WHERE eligibility_id = 'ELG000001'
        """)

        anomaly_manifest.append({
            "case_id": "ANOMALY_002",
            "type": "SCHOLARSHIP_EXCEEDS_ELIGIBLE_FEES",
            "description": "Scholarship award is deliberately higher than the eligible invoice fees.",
            "record_id": "ELG000001"
        })

        # CASE 3: Duplicate invoice for the same enrollment.
        original = cursor.execute("""
            SELECT enrollment_id, issue_date, due_date,
                   total_amount_paise, status, created_at
            FROM invoices
            WHERE invoice_id = 'INV000001'
        """).fetchone()

        fee_line = cursor.execute("""
            SELECT fee_schedule_id, description, amount_paise
            FROM invoice_lines
            WHERE invoice_id = 'INV000001'
            LIMIT 1
        """).fetchone()

        if original is None or fee_line is None:
            raise ValueError("Cannot create duplicate invoice.")

        cursor.execute("""
            INSERT OR IGNORE INTO invoices
            (invoice_id, enrollment_id, invoice_number, issue_date,
             due_date, total_amount_paise, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "ANOM-DUP-INV",
            original[0],
            "ANOM-DUP-NUMBER",
            original[1],
            original[2],
            original[3],
            original[4],
            original[5]
        ))

        cursor.execute("""
            INSERT OR IGNORE INTO invoice_lines
            (invoice_line_id, invoice_id, fee_schedule_id,
             description, amount_paise)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "ANOM-DUP-LINE",
            "ANOM-DUP-INV",
            fee_line[0],
            fee_line[1],
            fee_line[2]
        ))

        anomaly_manifest.append({
            "case_id": "ANOMALY_003",
            "type": "DUPLICATE_INVOICE",
            "description": "A second invoice is created for an existing enrollment.",
            "record_id": "ANOM-DUP-INV"
        })

        # CASE 4: Refund exceeds original payment.
        payment = cursor.execute("""
            SELECT student_id, amount_paise
            FROM payments
            WHERE payment_id = 'PAY000001'
        """).fetchone()

        if payment is None:
            raise ValueError("Payment required for refund anomaly is missing.")

        cursor.execute("""
            INSERT OR IGNORE INTO refunds
            (refund_id, payment_id, invoice_id, refund_date,
             amount_paise, reason, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "ANOM-REFUND-001",
            "PAY000001",
            "INV000001",
            "2026-01-02",
            payment[1] + 1,
            "Deliberate test anomaly: refund exceeds payment",
            "PROCESSED"
        ))

        anomaly_manifest.append({
            "case_id": "ANOMALY_004",
            "type": "REFUND_EXCEEDS_NET_PAID",
            "description": "Processed refund is one paisa greater than the original received payment.",
            "record_id": "ANOM-REFUND-001"
        })

        # CASE 5: Invoice ledger mismatch.
        cursor.execute("""
            UPDATE invoices
            SET total_amount_paise = total_amount_paise + 1
            WHERE invoice_id = 'INV000002'
        """)

        anomaly_manifest.append({
            "case_id": "ANOMALY_005",
            "type": "INVOICE_LEDGER_MISMATCH",
            "description": "Invoice total differs from the sum of its invoice lines by one paisa.",
            "record_id": "INV000002"
        })

        connection.commit()

        manifest_path = REPORT_DIR / "anomaly_manifest.json"

        with open(manifest_path, "w", encoding="utf-8") as file:
            json.dump(anomaly_manifest, file, indent=4)

        print("\nANOMALIES INJECTED SUCCESSFULLY")
        for anomaly in anomaly_manifest:
            print(
                anomaly["case_id"],
                "-",
                anomaly["type"]
            )

        print("\nManifest saved to:", manifest_path)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    inject_anomalies()
