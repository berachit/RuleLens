# Intentional Contradictions — RuleLens Demo

## C01 — Merit Scholarship GPA
- Main regulation: `academic_regulations.md`, Section 9.2 — 8.00/10.00 minimum GPA.
- Scholarship notice: `scholarship_notice.md`, Section 2 — 8.50/10.00 minimum GPA.
- Expected state: `CONFLICT`.

## C02 — Semester Tuition Deadline
- Main regulation: `academic_regulations.md`, Section 10 — 15 August 2026.
- Fee notice: `fee_deadlines.md` — 20 August 2026.
- Expected state: `CONFLICT`.

## C03 — Regular Examination Attendance
- Main regulation: `academic_regulations.md`, Section 5.1 — 75%.
- Attendance circular: `attendance_circular.md`, Section 1 — 80%.
- Expected state: `CONFLICT`.

These are the only intentionally planted contradictions in the demo corpus.
