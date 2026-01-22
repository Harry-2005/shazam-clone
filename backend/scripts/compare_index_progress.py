"""
Snapshot the current progress and compare with previous run.
This saves progress metrics to detect if indexing is actually moving.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.database import DatabaseManager
from sqlalchemy import text

SNAPSHOT_FILE = script_dir / "index_progress_snapshot.json"


def get_progress():
    """Get current progress metrics."""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        result = session.execute(text("""
            SELECT 
                p.pid,
                p.index_relid::regclass AS index_name,
                p.phase,
                p.tuples_total,
                p.tuples_done,
                p.blocks_total,
                p.blocks_done,
                p.partitions_total,
                p.partitions_done,
                now() - a.query_start AS duration
            FROM pg_stat_progress_create_index p
            JOIN pg_stat_activity a ON p.pid = a.pid;
        """))
        
        rows = result.fetchall()
        
        if not rows:
            return None
        
        # Return first active index creation
        row = rows[0]
        return {
            "pid": row[0],
            "index_name": str(row[1]),
            "phase": row[2],
            "tuples_total": row[3],
            "tuples_done": row[4],
            "blocks_total": row[5],
            "blocks_done": row[6],
            "partitions_total": row[7],
            "partitions_done": row[8],
            "duration": str(row[9]),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        session.close()


def load_previous():
    """Load previous snapshot."""
    if SNAPSHOT_FILE.exists():
        with open(SNAPSHOT_FILE, 'r') as f:
            return json.load(f)
    return None


def save_snapshot(data):
    """Save current snapshot."""
    with open(SNAPSHOT_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def compare_progress():
    """Compare current progress with previous snapshot."""
    current = get_progress()
    
    if not current:
        print("❌ No index creation in progress!")
        if SNAPSHOT_FILE.exists():
            SNAPSHOT_FILE.unlink()
            print("   Cleared old snapshot file.")
        return
    
    previous = load_previous()
    
    print("=" * 70)
    print(f"Index: {current['index_name']}")
    print(f"Phase: {current['phase']}")
    print(f"Duration: {current['duration']}")
    print("=" * 70)
    
    if previous and previous.get('pid') == current['pid']:
        # Same process, compare progress
        print("\n📊 PROGRESS COMPARISON:")
        print("-" * 70)
        
        # Check tuples
        if current['tuples_done'] is not None and previous['tuples_done'] is not None:
            tuples_diff = current['tuples_done'] - previous['tuples_done']
            print(f"Tuples processed: {current['tuples_done']:,} (was {previous['tuples_done']:,})")
            if tuples_diff > 0:
                print(f"  ✅ PROGRESSING: +{tuples_diff:,} tuples since last check")
            else:
                print(f"  ⚠️  STUCK: No tuples processed since last check")
        
        # Check blocks
        if current['blocks_done'] is not None and previous['blocks_done'] is not None:
            blocks_diff = current['blocks_done'] - previous['blocks_done']
            print(f"\nBlocks processed: {current['blocks_done']:,} (was {previous['blocks_done']:,})")
            if blocks_diff > 0:
                print(f"  ✅ PROGRESSING: +{blocks_diff:,} blocks since last check")
            else:
                print(f"  ⚠️  STUCK: No blocks processed since last check")
        
        # Check partitions
        if current['partitions_done'] is not None and previous['partitions_done'] is not None:
            parts_diff = current['partitions_done'] - previous['partitions_done']
            if parts_diff > 0:
                print(f"\nPartitions: +{parts_diff} since last check ✅")
        
        # Check phase change
        if current['phase'] != previous['phase']:
            print(f"\n🔄 Phase changed: {previous['phase']} → {current['phase']}")
        
        # Time between checks
        prev_time = datetime.fromisoformat(previous['timestamp'])
        curr_time = datetime.fromisoformat(current['timestamp'])
        time_diff = (curr_time - prev_time).total_seconds()
        print(f"\n⏱️  Time between checks: {time_diff:.1f} seconds")
        
        # Overall verdict
        print("\n" + "=" * 70)
        if (current['tuples_done'] or 0) > (previous['tuples_done'] or 0) or \
           (current['blocks_done'] or 0) > (previous['blocks_done'] or 0) or \
           current['phase'] != previous['phase']:
            print("✅ VERDICT: Index is ACTIVELY PROGRESSING")
        else:
            print("⚠️  VERDICT: Index appears STUCK (no progress detected)")
        print("=" * 70)
        
    else:
        # First run or new process
        print("\n📝 First snapshot or new process - saving baseline...")
        print(f"   Tuples done: {current['tuples_done'] or 'N/A'}")
        print(f"   Blocks done: {current['blocks_done'] or 'N/A'}")
        print(f"   Phase: {current['phase']}")
        print("\n   Run this script again in 30-60 seconds to compare progress!")
    
    # Save current snapshot for next comparison
    save_snapshot(current)


if __name__ == "__main__":
    compare_progress()
