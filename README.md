# YottaFlex AI Challenge – Student Fee Management System

## Overview
A Python and SQLite project for generating and validating synthetic student fee-management data. It includes students, programs, fee schedules, enrollments, invoices, scholarships, payments, payment allocations, refunds, event history, and late-fee assessments.

## Technology
- Python
- SQLite
- Pandas
- Pytest

## Project Structure
- src/schema.sql – Database schema
- src/database.py – Database initialization
- src/data_generator.py – Synthetic data generation
- src/validators.py – Data validation
- src/anomaly_detector.py – Intentional anomaly injection
- src/export_data.py – CSV, JSON, and manifest exports
- src/main.py – Pipeline runner
- tests/ – Automated tests
- data/generated/ – Generated CSV and JSON files
- data/reports/ – Validation and anomaly reports
- docs/ – Project documentation

## Setup
Create and activate a virtual environment, then install dependencies:

    python -m venv venv
    .\venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt

## Run
Generate the full-scale dataset:

    python src/main.py --scale 1 --seed 20261022

For a smaller test dataset:

    python src/main.py --scale 0.01 --seed 20261022

## Tests
Run the automated tests:

    python -m pytest -v

## Reproducibility
The data generator uses seed 20261022. Using the same seed and scale reproduces the synthetic dataset.

## Outputs
CSV and JSON exports are stored in data/generated/.
Validation reports are stored in data/reports/.

## Anomaly Testing
The anomaly detector intentionally injects invalid records for testing. Regenerate the baseline dataset before running normal validation and tests.

## Data Notes
All generated records are synthetic. Monetary values are stored as integer paise.

The baseline currently generates no refund, event-history, or late-fee-assessment records. These tables are included in the database schema and exports.
