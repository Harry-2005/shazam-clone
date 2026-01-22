"""
Kill the hanging rebuild process.
"""

import sys
import os
from pathlib import Path

script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.database import DatabaseManager
from sqlalchemy import text


def kill_rebuild():
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Find the hanging query
        result = session.execute(text("""
            SELECT pid, query
            FROM pg_stat_activity
            WHERE query LIKE '%SELECT COUNT%FROM fingerprints%'
            AND state = 'active'
            AND pid != pg_backend_pid();
        """))
        
        pids = result.fetchall()
        
        if pids:
            for pid_row in pids:
                pid = pid_row[0]
                print(f"Terminating PID {pid}: {pid_row[1][:80]}")
                session.execute(text(f"SELECT pg_terminate_backend({pid});"))
                session.commit()
                print(f"✓ Killed PID {pid}")
        else:
            print("No hanging queries found")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    kill_rebuild()
