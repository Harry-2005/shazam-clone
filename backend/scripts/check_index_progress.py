"""
Detailed index progress checker - shows if tuples are actually increasing.
Run this multiple times to see if the numbers are going up.
"""

import sys
import os
from pathlib import Path
import time

script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.database import DatabaseManager
from sqlalchemy import text


def check_index_status():
    """Check which indexes exist and their status."""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Check if indexes exist
        result = session.execute(text("""
            SELECT 
                indexname,
                tablename,
                pg_size_pretty(pg_relation_size(indexname::regclass)) as size
            FROM pg_indexes
            WHERE tablename = 'fingerprints'
            ORDER BY indexname;
        """))
        
        indexes = result.fetchall()
        
        print("=" * 70)
        print("CURRENT INDEXES ON fingerprints TABLE:")
        print("=" * 70)
        if indexes:
            for idx in indexes:
                print(f"  • {idx[0]:<40} Size: {idx[2]}")
        else:
            print("  No indexes found on fingerprints table")
        print()
        
        # Check for active index creation
        result = session.execute(text("""
            SELECT 
                pid,
                state,
                wait_event_type,
                wait_event,
                query,
                NOW() - query_start as duration
            FROM pg_stat_activity
            WHERE query LIKE '%CREATE INDEX%'
                AND state != 'idle'
            ORDER BY query_start;
        """))
        
        active_ops = result.fetchall()
        
        print("ACTIVE INDEX OPERATIONS:")
        print("=" * 70)
        if active_ops:
            for op in active_ops:
                print(f"  PID: {op[0]}")
                print(f"  State: {op[1]}")
                print(f"  Wait Event: {op[2]} / {op[3]}")
                print(f"  Duration: {op[5]}")
                print(f"  Query: {op[4][:100]}...")
                print()
        else:
            print("  No active index creation operations")
        print()
        
        # Check table stats
        result = session.execute(text("""
            SELECT 
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes,
                n_live_tup as live_rows,
                n_dead_tup as dead_rows,
                pg_size_pretty(pg_total_relation_size('fingerprints')) as total_size
            FROM pg_stat_user_tables
            WHERE relname = 'fingerprints';
        """))
        
        stats = result.fetchone()
        
        print("TABLE STATISTICS:")
        print("=" * 70)
        if stats:
            print(f"  Live rows: {stats[3]:,}")
            print(f"  Dead rows: {stats[4]:,}")
            print(f"  Total size: {stats[5]}")
            print(f"  Total inserts: {stats[0]:,}")
            print(f"  Total updates: {stats[1]:,}")
            print(f"  Total deletes: {stats[2]:,}")
        print()
        
        # Check for locks
        result = session.execute(text("""
            SELECT 
                l.pid,
                l.mode,
                l.granted,
                a.query,
                NOW() - a.query_start as duration
            FROM pg_locks l
            JOIN pg_stat_activity a ON l.pid = a.pid
            WHERE l.relation = 'fingerprints'::regclass
            ORDER BY a.query_start;
        """))
        
        locks = result.fetchall()
        
        print("ACTIVE LOCKS ON fingerprints TABLE:")
        print("=" * 70)
        if locks:
            for lock in locks:
                print(f"  PID: {lock[0]} | Mode: {lock[1]} | Granted: {lock[2]}")
                print(f"  Duration: {lock[4]}")
                print(f"  Query: {lock[3][:80]}...")
                print()
        else:
            print("  No locks found")
        
    except Exception as e:
        print(f"Error checking status: {e}")
    finally:
        session.close()


def monitor_progress(interval=5, iterations=None):
    """Monitor progress continuously."""
    iteration = 0
    
    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"Index Rebuild Monitor - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Refreshing every {interval} seconds... (Ctrl+C to stop)")
            print()
            
            check_index_status()
            
            iteration += 1
            if iterations and iteration >= iterations:
                break
                
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor index rebuild progress")
    parser.add_argument("--watch", action="store_true", help="Continuously monitor (refresh every 5s)")
    parser.add_argument("--interval", type=int, default=5, help="Refresh interval in seconds (default: 5)")
    
    args = parser.parse_args()
    
    if args.watch:
        monitor_progress(interval=args.interval)
    else:
        check_index_status()
