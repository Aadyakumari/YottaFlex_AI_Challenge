
PRAGMA foreign_keys = ON;

-- 1. STUDENTS
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    date_of_birth TEXT NOT NULL,
    family_income_paise INTEGER NOT NULL
        CHECK (family_income_paise >= 0),
    academic_score REAL NOT NULL
        CHECK (academic_score BETWEEN 0 AND 100),
    created_at TEXT NOT NULL
);

-- 2. PROGRAMS
CREATE TABLE IF NOT EXISTS programs (
    program_id TEXT PRIMARY KEY,
    program_code TEXT NOT NULL UNIQUE,
    program_name TEXT NOT NULL,
    department TEXT NOT NULL,
    duration_years INTEGER NOT NULL
        CHECK (duration_years > 0)
);

-- 3. FEE SCHEDULES
CREATE TABLE IF NOT EXISTS fee_schedules (
    fee_schedule_id TEXT PRIMARY KEY,
    program_id TEXT NOT NULL,
    term_id TEXT NOT NULL,
    fee_code TEXT NOT NULL,
    fee_name TEXT NOT NULL,
    amount_paise INTEGER NOT NULL
        CHECK (amount_paise >= 0),
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),
    FOREIGN KEY (program_id)
        REFERENCES programs(program_id),
    CHECK (
        effective_to IS NULL
        OR effective_to >= effective_from
    ),
    UNIQUE (
        program_id, term_id, fee_code, effective_from
    )
);

-- 4. ENROLLMENTS
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    program_id TEXT NOT NULL,
    term_id TEXT NOT NULL,
    enrollment_date TEXT NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN (
            'ACTIVE', 'WITHDRAWN', 'CANCELLED', 'COMPLETED'
        )),
    FOREIGN KEY (student_id)
        REFERENCES students(student_id),
    FOREIGN KEY (program_id)
        REFERENCES programs(program_id),
    UNIQUE (student_id, program_id, term_id)
);

-- 5. INVOICES
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id TEXT PRIMARY KEY,
    enrollment_id TEXT NOT NULL,
    invoice_number TEXT NOT NULL UNIQUE,
    issue_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    total_amount_paise INTEGER NOT NULL
        CHECK (total_amount_paise >= 0),
    status TEXT NOT NULL
        CHECK (status IN (
            'DRAFT', 'ISSUED', 'PARTIAL',
            'PAID', 'OVERDUE', 'CANCELLED'
        )),
    created_at TEXT NOT NULL,
    FOREIGN KEY (enrollment_id)
        REFERENCES enrollments(enrollment_id),
    CHECK (due_date >= issue_date)
);

-- 6. INVOICE LINES
CREATE TABLE IF NOT EXISTS invoice_lines (
    invoice_line_id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL,
    fee_schedule_id TEXT NOT NULL,
    description TEXT NOT NULL,
    amount_paise INTEGER NOT NULL
        CHECK (amount_paise >= 0),
    FOREIGN KEY (invoice_id)
        REFERENCES invoices(invoice_id),
    FOREIGN KEY (fee_schedule_id)
        REFERENCES fee_schedules(fee_schedule_id)
);

-- 7. SCHOLARSHIPS
CREATE TABLE IF NOT EXISTS scholarships (
    scholarship_id TEXT PRIMARY KEY,
    scholarship_name TEXT NOT NULL,
    min_academic_score REAL NOT NULL
        CHECK (min_academic_score BETWEEN 0 AND 100),
    max_family_income_paise INTEGER NOT NULL
        CHECK (max_family_income_paise >= 0),
    award_percentage REAL NOT NULL
        CHECK (award_percentage BETWEEN 0 AND 100),
    max_award_paise INTEGER NOT NULL
        CHECK (max_award_paise >= 0),
    eligible_fee_code TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT
);

-- 8. ELIGIBILITY AND SCHOLARSHIP AWARDS
CREATE TABLE IF NOT EXISTS eligibility (
    eligibility_id TEXT PRIMARY KEY,
    scholarship_id TEXT NOT NULL,
    enrollment_id TEXT NOT NULL,
    decision TEXT NOT NULL
        CHECK (decision IN ('ELIGIBLE', 'INELIGIBLE')),
    award_amount_paise INTEGER NOT NULL DEFAULT 0
        CHECK (award_amount_paise >= 0),
    decision_reason TEXT NOT NULL,
    evaluated_at TEXT NOT NULL,
    FOREIGN KEY (scholarship_id)
        REFERENCES scholarships(scholarship_id),
    FOREIGN KEY (enrollment_id)
        REFERENCES enrollments(enrollment_id),
    UNIQUE (scholarship_id, enrollment_id)
);

-- 9. PAYMENTS
CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    payment_date TEXT NOT NULL,
    amount_paise INTEGER NOT NULL
        CHECK (amount_paise > 0),
    payment_method TEXT NOT NULL
        CHECK (payment_method IN (
            'UPI', 'CARD', 'BANK_TRANSFER', 'CASH'
        )),
    status TEXT NOT NULL
        CHECK (status IN (
            'RECEIVED', 'FAILED', 'REVERSED'
        )),
    FOREIGN KEY (student_id)
        REFERENCES students(student_id)
);

-- 10. PAYMENT ALLOCATIONS
CREATE TABLE IF NOT EXISTS payment_allocations (
    allocation_id TEXT PRIMARY KEY,
    payment_id TEXT NOT NULL,
    invoice_line_id TEXT NOT NULL,
    allocated_amount_paise INTEGER NOT NULL
        CHECK (allocated_amount_paise > 0),
    allocated_at TEXT NOT NULL,
    FOREIGN KEY (payment_id)
        REFERENCES payments(payment_id),
    FOREIGN KEY (invoice_line_id)
        REFERENCES invoice_lines(invoice_line_id)
);

-- 11. REFUNDS
CREATE TABLE IF NOT EXISTS refunds (
    refund_id TEXT PRIMARY KEY,
    payment_id TEXT NOT NULL,
    invoice_id TEXT NOT NULL,
    refund_date TEXT NOT NULL,
    amount_paise INTEGER NOT NULL
        CHECK (amount_paise > 0),
    reason TEXT NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN (
            'PENDING', 'PROCESSED', 'REJECTED'
        )),
    FOREIGN KEY (payment_id)
        REFERENCES payments(payment_id),
    FOREIGN KEY (invoice_id)
        REFERENCES invoices(invoice_id)
);

-- INDEXES FOR FASTER QUERIES
CREATE INDEX IF NOT EXISTS idx_enrollment_student
ON enrollments(student_id);

CREATE INDEX IF NOT EXISTS idx_invoice_enrollment
ON invoices(enrollment_id);

CREATE INDEX IF NOT EXISTS idx_invoice_line_invoice
ON invoice_lines(invoice_id);

CREATE INDEX IF NOT EXISTS idx_payment_student
ON payments(student_id);

CREATE INDEX IF NOT EXISTS idx_allocation_payment
ON payment_allocations(payment_id);

CREATE INDEX IF NOT EXISTS idx_allocation_line
ON payment_allocations(invoice_line_id);

CREATE INDEX IF NOT EXISTS idx_refund_payment
ON refunds(payment_id);


-- 12. EVENT HISTORY / AUDIT LOG
CREATE TABLE IF NOT EXISTS event_history (
    event_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_timestamp TEXT NOT NULL,
    actor TEXT NOT NULL DEFAULT 'SYSTEM',
    details_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_event_entity
ON event_history(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_event_timestamp
ON event_history(event_timestamp);


-- 13. LATE FEE ASSESSMENTS
CREATE TABLE IF NOT EXISTS late_fee_assessments (
    late_fee_id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL,
    assessed_date TEXT NOT NULL,
    overdue_days INTEGER NOT NULL CHECK (overdue_days > 0),
    amount_paise INTEGER NOT NULL CHECK (amount_paise >= 0),
    status TEXT NOT NULL
        CHECK (status IN ('ASSESSED', 'WAIVED', 'PAID')),
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
    UNIQUE (invoice_id, assessed_date)
);

CREATE INDEX IF NOT EXISTS idx_late_fee_invoice
ON late_fee_assessments(invoice_id);

