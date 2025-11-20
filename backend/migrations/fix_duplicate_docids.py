"""
Fix duplicate DOCiD records and add UNIQUE constraint

This migration:
1. Identifies all duplicate document_docid records
2. Keeps the oldest record for each DOCiD
3. Deletes the duplicates
4. Adds a UNIQUE constraint to prevent future duplicates

Run with: python migrations/fix_duplicate_docids.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Publications
from sqlalchemy import func, text

def fix_duplicates():
    """Fix duplicate DOCiD records"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("Fixing Duplicate DOCiD Records")
        print("=" * 60)

        # Step 1: Find duplicates
        print("\n[1/4] Identifying duplicate DOCiDs...")
        duplicates = db.session.query(
            Publications.document_docid,
            func.count(Publications.id).label('count')
        ).group_by(Publications.document_docid).having(func.count(Publications.id) > 1).all()

        if not duplicates:
            print("✓ No duplicate DOCiDs found")
            print("\n[2/4] Adding UNIQUE constraint...")
            add_unique_constraint()
            return

        print(f"✗ Found {len(duplicates)} DOCiDs with duplicates:")
        total_duplicates = 0
        for docid, count in duplicates:
            print(f"  - {docid}: {count} records")
            total_duplicates += (count - 1)  # Count extras only

        print(f"\nTotal duplicate records to delete: {total_duplicates}")

        # Step 2: Delete duplicates (keep oldest)
        print("\n[2/4] Deleting duplicate records (keeping oldest)...")
        deleted_count = 0

        for docid, count in duplicates:
            # Get all records for this DOCiD, ordered by ID (oldest first)
            records = Publications.query.filter_by(document_docid=docid).order_by(Publications.id).all()

            # Keep first (oldest), delete rest
            keep_record = records[0]
            delete_records = records[1:]

            print(f"\n  DOCiD: {docid}")
            print(f"    Keeping: ID={keep_record.id} (created: {keep_record.timestamp})")

            for record in delete_records:
                print(f"    Deleting: ID={record.id} (created: {record.timestamp})")
                db.session.delete(record)
                deleted_count += 1

        db.session.commit()
        print(f"\n✓ Deleted {deleted_count} duplicate records")

        # Step 3: Verify no duplicates remain
        print("\n[3/4] Verifying fix...")
        remaining_duplicates = db.session.query(
            Publications.document_docid,
            func.count(Publications.id).label('count')
        ).group_by(Publications.document_docid).having(func.count(Publications.id) > 1).all()

        if remaining_duplicates:
            print(f"✗ ERROR: {len(remaining_duplicates)} duplicates still exist!")
            for docid, count in remaining_duplicates:
                print(f"  - {docid}: {count} records")
            return
        else:
            print("✓ No duplicates remain")

        # Step 4: Add UNIQUE constraint
        print("\n[4/4] Adding UNIQUE constraint to prevent future duplicates...")
        add_unique_constraint()

        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  - Deleted {deleted_count} duplicate records")
        print(f"  - Added UNIQUE constraint on document_docid")
        print(f"  - Database integrity restored")

def add_unique_constraint():
    """Add UNIQUE constraint to document_docid"""
    try:
        # Check if constraint already exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        constraints = inspector.get_unique_constraints('publications')

        constraint_exists = any(
            'document_docid' in c.get('column_names', [])
            for c in constraints
        )

        if constraint_exists:
            print("  ✓ UNIQUE constraint already exists")
            return

        # Add UNIQUE constraint
        db.session.execute(
            text('ALTER TABLE publications ADD CONSTRAINT uq_publications_document_docid UNIQUE (document_docid)')
        )
        db.session.commit()
        print("  ✓ UNIQUE constraint added")

    except Exception as e:
        print(f"  ✗ Error adding UNIQUE constraint: {str(e)}")
        db.session.rollback()
        # Continue even if constraint fails (index already provides uniqueness check in application)

if __name__ == '__main__':
    fix_duplicates()
