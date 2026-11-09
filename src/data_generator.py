
import argparse
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from database import DB_PATH

SEED = 20261022
BASE_DIR = Path(__file__).resolve().parent.parent


def random_date(rng, start=date(2025, 1, 1), days=600):
    return (start + timedelta(days=rng.randint(0, days))).isoformat()


def generate_data(scale=0.01, seed=SEED):
    if scale <= 0:
        raise ValueError("Scale must be greater than zero.")

    rng = random.Random(seed)

    students_count = max(10, int(10000 * scale))
    programs_count = max(2, int(20 * scale))
    invoices_count = max(10, int(30000 * scale))
    awards_count = max(5, int(15000 * scale))
    payments_count = max(10, int(50000 * scale))

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        cursor = connection.cursor()

        # Clear existing records in dependency order.
        for table in [
            "refunds", "payment_allocations", "payments",
            "eligibility", "scholarships", "invoice_lines",
            "invoices", "enrollments", "fee_schedules",
            "programs", "students"
        ]:
            cursor.execute(f"DELETE FROM {table}")

        # 1. Generate programs.
        programs = []

        for i in range(1, programs_count + 1):
            programs.append((
                f"PRG{i:03}",
                f"PROG{i:03}",
                f"Academic Program {i}",
                rng.choice(["Engineering", "Science", "Management", "Arts"]),
                rng.randint(3, 5)
            ))

        cursor.executemany("""
            INSERT INTO programs
            (program_id, program_code, program_name, department, duration_years)
            VALUES (?, ?, ?, ?, ?)
        """, programs)

        # 2. Generate fee schedules.
        fee_schedules = []

        for i in range(1, programs_count + 1):
            for term in range(1, 4):
                fee_schedules.append((
                    f"FEE{i:03}{term}",
                    f"PRG{i:03}",
                    f"TERM{term}",
                    "TUITION",
                    "Tuition Fee",
                    rng.choice([3000000, 4000000, 5000000]),
                    "2025-01-01",
                    "2027-12-31",
                    1
                ))

        cursor.executemany("""
            INSERT INTO fee_schedules
            (fee_schedule_id, program_id, term_id, fee_code, fee_name,
             amount_paise, effective_from, effective_to, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, fee_schedules)

        fee_amounts = {
            row[0]: row[5] for row in fee_schedules
        }

        # 3. Generate students.
        students = []

        for i in range(1, students_count + 1):
            students.append((
                f"STU{i:06}",
                f"Student {i}",
                f"student{i}@example.com",
                random_date(rng, date(2000, 1, 1), 2500),
                rng.randint(10000000, 100000000),
                round(rng.uniform(50, 100), 2),
                random_date(rng)
            ))

        cursor.executemany("""
            INSERT INTO students
            (student_id, full_name, email, date_of_birth,
             family_income_paise, academic_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, students)

        # 4. Generate enrollments, invoices and invoice lines.
        enrollments = []
        invoices = []
        invoice_lines = []
        invoice_students = []

        for i in range(1, invoices_count + 1):
            student_id = f"STU{((i - 1) % students_count) + 1:06}"

            program_number = ((i - 1) % programs_count) + 1
            program_id = f"PRG{program_number:03}"

            term_number = ((i - 1) % 3) + 1
            term_id = f"TERM{term_number}"

            enrollment_id = f"ENR{i:06}"
            invoice_id = f"INV{i:06}"
            fee_id = f"FEE{program_number:03}{term_number}"

            amount = fee_amounts[fee_id]

            issue_date = random_date(rng)
            due_date = (
                date.fromisoformat(issue_date) + timedelta(days=30)
            ).isoformat()

            enrollments.append((
                enrollment_id,
                student_id,
                program_id,
                term_id,
                issue_date,
                "ACTIVE"
            ))

            invoices.append((
                invoice_id,
                enrollment_id,
                f"INVOICE{i:06}",
                issue_date,
                due_date,
                amount,
                "ISSUED",
                issue_date
            ))

            invoice_lines.append((
                f"LINE{i:06}",
                invoice_id,
                fee_id,
                "Tuition Fee",
                amount
            ))

            invoice_students.append(student_id)

        cursor.executemany("""
            INSERT INTO enrollments
            (enrollment_id, student_id, program_id, term_id,
             enrollment_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, enrollments)

        cursor.executemany("""
            INSERT INTO invoices
            (invoice_id, enrollment_id, invoice_number, issue_date,
             due_date, total_amount_paise, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, invoices)

        cursor.executemany("""
            INSERT INTO invoice_lines
            (invoice_line_id, invoice_id, fee_schedule_id,
             description, amount_paise)
            VALUES (?, ?, ?, ?, ?)
        """, invoice_lines)

        # 5. Generate scholarships and eligibility decisions.
        scholarships = []

        for i in range(1, 6):
            scholarships.append((
                f"SCH{i:03}",
                f"Merit Scholarship {i}",
                70.0 + i,
                50000000,
                10.0 + i * 5,
                1000000 + i * 100000,
                "TUITION",
                "2025-01-01",
                "2027-12-31"
            ))

        cursor.executemany("""
            INSERT INTO scholarships
            (scholarship_id, scholarship_name, min_academic_score,
             max_family_income_paise, award_percentage, max_award_paise,
             eligible_fee_code, effective_from, effective_to)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, scholarships)

        eligibility = []

        for i in range(1, awards_count + 1):
            enrollment_id = f"ENR{((i - 1) % invoices_count) + 1:06}"
            scholarship_id = f"SCH{((i - 1) % 5) + 1:03}"

            eligibility.append((
                f"ELG{i:06}",
                scholarship_id,
                enrollment_id,
                "ELIGIBLE",
                rng.randint(100000, 800000),
                "Meets synthetic eligibility criteria",
                random_date(rng)
            ))

        cursor.executemany("""
            INSERT INTO eligibility
            (eligibility_id, scholarship_id, enrollment_id, decision,
             award_amount_paise, decision_reason, evaluated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, eligibility)

        # 6. Generate payments and balanced allocations.
        payments = []
        allocations = []

        payment_counts = [
            payments_count // invoices_count
            for _ in range(invoices_count)
        ]

        for i in range(payments_count % invoices_count):
            payment_counts[i] += 1

        payment_number = 0

        for invoice_index, count in enumerate(payment_counts):
            if count == 0:
                continue

            student_id = invoice_students[invoice_index]
            line_id = f"LINE{invoice_index + 1:06}"
            invoice_amount = invoice_lines[invoice_index][4]

            base_amount = invoice_amount // count
            remainder = invoice_amount % count

            for part in range(count):
                payment_number += 1
                payment_id = f"PAY{payment_number:06}"

                payment_amount = base_amount + (
                    1 if part < remainder else 0
                )

                payment_date = random_date(rng)

                payments.append((
                    payment_id,
                    student_id,
                    payment_date,
                    payment_amount,
                    rng.choice(["UPI", "CARD", "BANK_TRANSFER", "CASH"]),
                    "RECEIVED"
                ))

                allocations.append((
                    f"ALLOC{payment_number:06}",
                    payment_id,
                    line_id,
                    payment_amount,
                    payment_date
                ))

        cursor.executemany("""
            INSERT INTO payments
            (payment_id, student_id, payment_date, amount_paise,
             payment_method, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, payments)

        cursor.executemany("""
            INSERT INTO payment_allocations
            (allocation_id, payment_id, invoice_line_id,
             allocated_amount_paise, allocated_at)
            VALUES (?, ?, ?, ?, ?)
        """, allocations)

        connection.commit()

        print("\nDATA GENERATION SUCCESSFUL")
        print(f"Seed: {seed}")
        print(f"Scale: {scale}")
        print(f"Students: {students_count}")
        print(f"Programs: {programs_count}")
        print(f"Invoices: {invoices_count}")
        print(f"Scholarship awards: {awards_count}")
        print(f"Payments: {payments_count}")
        print(f"Payment allocations: {len(allocations)}")
        print("\nDatabase:", DB_PATH)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate reproducible synthetic student finance data."
    )

    parser.add_argument("--scale", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=SEED)

    args = parser.parse_args()

    generate_data(scale=args.scale, seed=args.seed)

