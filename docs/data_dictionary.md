# Data Dictionary

All monetary values are stored as integer paise.

| Table | Description |
|---|---|
| students | Student information |
| programs | Academic program details |
| fee_schedules | Program fee structures |
| enrollments | Student enrollment records |
| invoices | Student fee invoices |
| invoice_lines | Individual invoice charges |
| scholarships | Scholarship rules |
| eligibility | Scholarship eligibility decisions |
| payments | Student payment records |
| payment_allocations | Payments allocated to invoice lines |
| refunds | Refund records |
| event_history | Entity event records |
| late_fee_assessments | Late fee assessment records |

## Monetary values
Amounts ending in `_paise` are stored in paise. ₹100 is represented as 10000.
