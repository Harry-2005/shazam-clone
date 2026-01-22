"""
Check the status of database indexes to see if they exist and their progress.
"""

import sys
from pathlib import Path

script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.database import DatabaseManager
from sqlalchemy import text


def check_indexes():
    """Check current index status in the database."""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        print("Checking fingerprints table indexes...\n")
        
        # Get all indexes on the fingerprints table
        result = session.execute(text("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE tablename = 'fingerprints'
            ORDER BY indexname;
        """))
        
        indexes = result.fetchall()
        
        if indexes:
            print(f"Found {len(indexes)} indexes on fingerprints table:\n")
            for idx in indexes:
                print(f"  ✓ {idx[0]}")
                print(f"    {idx[1]}\n")
        else:
            print("⚠ No indexes found on fingerprints table!")
            print("  This means indexes are either dropped or being rebuilt.\n")
        
        # Check for ongoing index creation
        print("\nChecking for active index creation processes...")
        result = session.execute(text("""
            SELECT 
                pid,
                query,
                state,
                EXTRACT(EPOCH FROM (NOW() - query_start)) as duration_seconds
            FROM pg_stat_activity 
            WHERE query LIKE '%CREATE INDEX%' 
              AND query NOT LIKE '%pg_stat_activity%'
              AND state != 'idle';
        """))
        
        active = result.fetchall()
        
        if active:
            print(f"Found {len(active)} active index creation process(es):\n")
            for proc in active:
                pid, query, state, duration = proc
                minutes = int(duration / 60)
                seconds = int(duration % 60)
                print(f"  Process ID: {pid}")
                print(f"  State: {state}")
                print(f"  Duration: {minutes}m {seconds}s")
                print(f"  Query: {query[:100]}...")
                print()
        else:
            print("  No active index creation processes found.")
            print("  Either indexes are already built, or the process hasn't started.\n")
        
        # Get row count to understand scale
        print("Checking fingerprints table size...")
        result = session.execute(text("""
            SELECT COUNT(*) FROM fingerprints;
        """))
        count = result.scalar()
        print(f"  Total fingerprints: {count:,}")
        
        # Get table size
        result = session.execute(text("""
            SELECT pg_size_pretty(pg_total_relation_size('fingerprints')) as size;
        """))
        size = result.scalar()
        print(f"  Table size: {size}\n")
        
    except Exception as e:
        print(f"Error checking indexes: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    check_indexes()
