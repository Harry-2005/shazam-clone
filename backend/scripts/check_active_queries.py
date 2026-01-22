"""
Quick check of what's happening in the database right now.
"""

import sys
import os
from pathlib import Path

script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.database import DatabaseManager
from sqlalchemy import text


def check_now():
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Check all active queries
        result = session.execute(text("""
            SELECT 
                pid,
                usename,
                application_name,
                state,
                query,
                now() - query_start AS duration
            FROM pg_stat_activity
            WHERE state = 'active'
            AND pid != pg_backend_pid()
            ORDER BY query_start;
        """))
        
        queries = result.fetchall()
        
        if queries:
            print(f"Found {len(queries)} active queries:\n")
            for q in queries:
                print(f"PID: {q[0]}")
                print(f"User: {q[1]}")
                print(f"App: {q[2]}")
                print(f"State: {q[3]}")
                print(f"Duration: {q[5]}")
                print(f"Query: {q[4][:200]}")
                print("-" * 60)
        else:
            print("No active queries found (besides this one)")
        
        # Check specifically for index creation
        result = session.execute(text("""
            SELECT * FROM pg_stat_progress_create_index;
        """))
        
        index_progress = result.fetchall()
        if index_progress:
            print(f"\nActive index creation: {len(index_progress)}")
            for idx in index_progress:
                print(idx)
        else:
            print("\nNo active index creation detected")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    check_now()
