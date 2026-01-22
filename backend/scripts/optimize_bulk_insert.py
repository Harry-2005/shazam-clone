"""
Optimize database for bulk insert by temporarily dropping indexes.
Run BEFORE bulk insert, then rebuild after.

WARNING: Database will be slow for queries while indexes are dropped!
"""

import sys
import os
from pathlib import Path

script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.database import DatabaseManager
from sqlalchemy import text


def drop_indexes():
    """Drop fingerprint table indexes for faster bulk insert."""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        print("Dropping indexes for bulk insert optimization...")
        
        # Drop the main hash index (this is the HUGE bottleneck)
        session.execute(text("""
            DROP INDEX IF EXISTS idx_fingerprints_hash;
        """))
        
        # Drop time offset index
        session.execute(text("""
            DROP INDEX IF EXISTS idx_fingerprints_time_offset;
        """))
        
        # Drop song_id index (foreign key index)
        session.execute(text("""
            DROP INDEX IF EXISTS idx_fingerprints_song_id;
        """))
        
        session.commit()
        print("✓ Indexes dropped successfully!")
        print("  Database writes will be MUCH faster now")
        print("  Run rebuild_indexes.py after bulk insert completes")
        
    except Exception as e:
        session.rollback()
        print(f"Error dropping indexes: {e}")
        raise
    finally:
        session.close()


def rebuild_indexes():
    """Rebuild indexes after bulk insert completes."""
    db = DatabaseManager()
    
    # Use raw connection for CONCURRENTLY (cannot run in transaction)
    connection = db.engine.raw_connection()
    connection.set_isolation_level(0)  # AUTOCOMMIT mode
    cursor = connection.cursor()
    
    try:
        print("\nRebuilding indexes (this may take 30+ minutes with large datasets)...")
        print("  Starting index creation (fingerprint count check skipped for speed)...")
        
        # Rebuild hash index - CRITICAL for song matching
        print("\n[1/3] Creating hash index... (this is the slowest)")
        print("      This may take 15-30 minutes or more...")
        try:
            cursor.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fingerprints_hash 
                ON fingerprints(hash_value);
            """)
            print("      ✓ Hash index created successfully!")
        except Exception as e:
            print(f"      ✗ Failed to create hash index: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Rebuild time offset index
        print("\n[2/3] Creating time offset index...")
        try:
            cursor.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fingerprints_time_offset 
                ON fingerprints(time_offset);
            """)
            print("      ✓ Time offset index created successfully!")
        except Exception as e:
            print(f"      ✗ Failed to create time offset index: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Rebuild song_id index
        print("\n[3/3] Creating song_id index...")
        try:
            cursor.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fingerprints_song_id 
                ON fingerprints(song_id);
            """)
            print("      ✓ Song_id index created successfully!")
        except Exception as e:
            print(f"      ✗ Failed to create song_id index: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        print("\n✓ All indexes rebuilt successfully!")
        print("  Database is now optimized for queries")
        
    except Exception as e:
        print(f"\n✗ Error rebuilding indexes: {e}")
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Optimize database for bulk operations")
    parser.add_argument("--drop", action="store_true", help="Drop indexes before bulk insert")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild indexes after bulk insert")
    
    args = parser.parse_args()
    
    if args.drop:
        drop_indexes()
    elif args.rebuild:
        rebuild_indexes()
    else:
        print("Usage:")
        print("  Before bulk insert:  python optimize_bulk_insert.py --drop")
        print("  After bulk insert:   python optimize_bulk_insert.py --rebuild")
