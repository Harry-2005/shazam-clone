"""
Check for invalid or partially created indexes.
"""

import sys
import os
from pathlib import Path

script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.database import DatabaseManager
from sqlalchemy import text


def check_invalid_indexes():
    """Check for invalid or in-progress indexes."""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        print("Checking for invalid indexes...")
        
        # Check for invalid indexes
        result = session.execute(text("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = 'fingerprints'
            AND schemaname = 'public';
        """))
        
        all_indexes = result.fetchall()
        print(f"\nAll indexes on fingerprints table: {len(all_indexes)}")
        for idx in all_indexes:
            print(f"  - {idx[2]}")
        
        # Check pg_stat_user_indexes for index validity
        result = session.execute(text("""
            SELECT 
                indexrelname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            WHERE relname = 'fingerprints';
        """))
        
        stats = result.fetchall()
        print(f"\nIndex statistics:")
        for stat in stats:
            print(f"  {stat[0]}: scans={stat[1]}, tuples_read={stat[2]}, tuples_fetch={stat[3]}")
        
        # Check for locks on the fingerprints table
        result = session.execute(text("""
            SELECT 
                locktype,
                relation::regclass,
                mode,
                granted,
                pid
            FROM pg_locks
            WHERE relation = 'fingerprints'::regclass;
        """))
        
        locks = result.fetchall()
        if locks:
            print(f"\nLocks on fingerprints table: {len(locks)}")
            for lock in locks:
                print(f"  Type: {lock[0]}, Mode: {lock[2]}, Granted: {lock[3]}, PID: {lock[4]}")
        else:
            print("\nNo locks on fingerprints table")
        
        # Check for any CREATE INDEX that might have failed
        result = session.execute(text("""
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation
            FROM pg_stats
            WHERE tablename = 'fingerprints'
            AND schemaname = 'public'
            ORDER BY attname;
        """))
        
        stats = result.fetchall()
        print(f"\nColumn statistics for fingerprints:")
        for stat in stats:
            print(f"  {stat[2]}: n_distinct={stat[3]}, correlation={stat[4]}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    check_invalid_indexes()
