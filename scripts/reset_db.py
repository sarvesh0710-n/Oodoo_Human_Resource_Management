#!/usr/bin/env python3
"""
Dayflow HRMS — Database Reset & Re-initialization Script
Usage:
    python -m scripts.reset_db
"""
import sys
from app.core.database import SessionLocal, engine, Base
from scripts.seed_db import seed_database


def reset_database():
    print("[!] WARNING: Re-creating all database tables in Dayflow HRMS...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("[✓] Database schema re-created successfully.")

    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


def main():
    confirm = input("Are you sure you want to RESET the entire database? (y/N): ").strip().lower()
    if confirm not in ("y", "yes"):
        print("Database reset cancelled.")
        sys.exit(0)
    reset_database()


if __name__ == "__main__":
    main()
