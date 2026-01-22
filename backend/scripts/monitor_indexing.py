"""
Monitor index creation progress in real-time.
Run this in a separate terminal while indexing is happening.
"""

import sys
import os
import time
from pathlib import Path

script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.database import DatabaseManager
from sqlalchemy import text


def monitor_indexing():
    """Monitor index creation progress."""
    db = DatabaseManager()
    
    print("Monitoring index creation progress...")
    print("Press Ctrl+C to stop monitoring\n")
    
    last_progress = {}
    
    try:
        while True:
            session = db.get_session()
            try:
                # Check for active index creation
                result = session.execute(text("""
                    SELECT 
                        p.pid,
                        p.datname,
                        p.relid::regclass AS table_name,
                        p.index_relid::regclass AS index_name,
                        p.command,
                        p.phase,
                        p.tuples_total,
                        p.tuples_done,
                        ROUND(100.0 * p.tuples_done / NULLIF(p.tuples_total, 0), 2) AS progress_pct,
                        p.partitions_total,
                        p.partitions_done,
                        now() - a.query_start AS duration
                    FROM pg_stat_progress_create_index p
                    JOIN pg_stat_activity a ON p.pid = a.pid;
                """))
                
                rows = result.fetchall()
                
                if rows:
                    for row in rows:
                        pid = row[0]
                        index_name = row[3]
                        phase = row[5]
                        tuples_total = row[6]
                        tuples_done = row[7]
                        progress_pct = row[8] or 0
                        duration = row[11]
                        
                        # Clear line and print progress
                        print(f"\r\033[K", end="")
                        
                        if tuples_total and tuples_total > 0:
                            bar_length = 40
                            filled = int(bar_length * tuples_done / tuples_total)
                            bar = "█" * filled + "░" * (bar_length - filled)
                            
                            print(f"[{bar}] {progress_pct:.1f}% | {index_name}", end="")
                            print(f" | Phase: {phase} | {tuples_done:,}/{tuples_total:,} tuples", end="")
                            print(f" | Duration: {str(duration).split('.')[0]}", end="", flush=True)
                        else:
                            print(f"Building {index_name} | Phase: {phase} | Duration: {str(duration).split('.')[0]}", end="", flush=True)
                        
                        last_progress[pid] = (index_name, phase, progress_pct)
                else:
                    # No active indexing
                    if last_progress:
                        print("\r\033[K✓ Indexing completed!", flush=True)
                        last_progress.clear()
                    else:
                        print("\r\033[KWaiting for index creation to start...", end="", flush=True)
                
            except Exception as e:
                print(f"\nError querying progress: {e}")
            finally:
                session.close()
            
            time.sleep(2)  # Update every 2 seconds
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")


if __name__ == "__main__":
    monitor_indexing()
