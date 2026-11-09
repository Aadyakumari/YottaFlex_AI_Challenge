
import sqlite3
from pathlib import Path

# Project directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Database location
DB_PATH = DATA_DIR / "student_fees.db"

# SQL schema location
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_connection():
    """Create and return a database connection."""
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    """Create database tables using schema.sql."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = get_connection()

    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
            schema = file.read()

        connection.executescript(schema)
        connection.commit()

        print("Database initialized successfully!")
        print(f"Database location: {DB_PATH}")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
