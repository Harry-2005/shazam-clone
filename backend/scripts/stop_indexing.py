"""
Stop any running index creation operations.
"""

import sys
import os
from pathlib import Path

script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.database import DatabaseManager
from sqlalchemy import text


def stop_indexing():
    """Cancel any running index creation operations."""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        print("Checking for active index operations...")
        
        # Find all active queries related to index creation
        result = session.execute(text("""
            SELECT pid, query, state, now() - query_start as duration
            FROM pg_stat_activity
            WHERE query LIKE '%CREATE INDEX%'
            AND state = 'active';
        """))
        
        active_queries = result.fetchall()
        
        if not active_queries:
            print("No active index creation operations found.")
            return
        
        print(f"Found {len(active_queries)} active index operations:")
        for row in active_queries:
            print(f"  PID {row[0]}: {row[1][:80]}... (running for {row[3]})")
        
        # Terminate these processes
        for row in active_queries:
            pid = row[0]
            print(f"\nTerminating process {pid}...")
            session.execute(text(f"SELECT pg_terminate_backend({pid});"))
            session.commit()
            print(f"✓ Process {pid} terminated")
        
        print("\n✓ All index operations stopped")
        print("Note: Partially created indexes have been cancelled.")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    stop_indexing()
