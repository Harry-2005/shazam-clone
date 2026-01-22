"""
Check current database status: indexes, songs, fingerprints.
"""

import sys
import os
from pathlib import Path

script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.database import DatabaseManager
from sqlalchemy import text


def check_status():
    """Check database status and indexes."""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        print("=" * 60)
        print("DATABASE STATUS")
        print("=" * 60)
        
        # Check songs count
        result = session.execute(text("SELECT COUNT(*) FROM songs;"))
        songs_count = result.scalar()
        print(f"\n📊 Songs in database: {songs_count:,}")
        
        # Check fingerprints count
        result = session.execute(text("SELECT COUNT(*) FROM fingerprints;"))
        fingerprints_count = result.scalar()
        print(f"📊 Fingerprints in database: {fingerprints_count:,}")
        
        if songs_count > 0:
            avg_fingerprints = fingerprints_count / songs_count
            print(f"📊 Average fingerprints per song: {avg_fingerprints:,.0f}")
        
        # Check indexes on fingerprints table
        print("\n" + "=" * 60)
        print("INDEXES ON FINGERPRINTS TABLE")
        print("=" * 60)
        
        result = session.execute(text("""
            SELECT 
                indexname, 
                indexdef,
                pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
            FROM pg_indexes
            WHERE tablename = 'fingerprints'
            ORDER BY indexname;
        """))
        
        indexes = result.fetchall()
        
        if not indexes:
            print("\n⚠️  NO INDEXES FOUND!")
            print("    This is normal during bulk insert.")
            print("    Run: python scripts\\optimize_bulk_insert.py --rebuild")
        else:
            print(f"\n✓ Found {len(indexes)} index(es):")
            for idx in indexes:
                print(f"\n  📌 {idx[0]}")
                print(f"     Size: {idx[2]}")
                print(f"     Definition: {idx[1]}")
        
        # Check for critical indexes
        print("\n" + "=" * 60)
        print("CRITICAL INDEXES STATUS")
        print("=" * 60)
        
        critical_indexes = [
            'idx_fingerprints_hash',
            'idx_fingerprints_time_offset', 
            'idx_fingerprints_song_id'
        ]
        
        existing_index_names = [idx[0] for idx in indexes]
        
        for idx_name in critical_indexes:
            if idx_name in existing_index_names:
                print(f"  ✓ {idx_name} - EXISTS")
            else:
                print(f"  ✗ {idx_name} - MISSING")
        
        # Check if any index operations are running
        print("\n" + "=" * 60)
        print("ACTIVE OPERATIONS")
        print("=" * 60)
        
        result = session.execute(text("""
            SELECT pid, query, state, now() - query_start as duration
            FROM pg_stat_activity
            WHERE query LIKE '%CREATE INDEX%'
            OR query LIKE '%fingerprints%'
            AND state = 'active'
            AND pid != pg_backend_pid();
        """))
        
        active = result.fetchall()
        
        if not active:
            print("\n✓ No active index operations")
        else:
            print(f"\n⚠️  {len(active)} active operation(s):")
            for row in active:
                print(f"\n  PID {row[0]} ({row[2]})")
                print(f"  Duration: {row[3]}")
                print(f"  Query: {row[1][:80]}...")
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        if len(existing_index_names) >= 3:
            print("\n✅ Database is FULLY INDEXED - queries will be fast")
        elif len(existing_index_names) == 0:
            print("\n⚠️  Database has NO INDEXES - inserts are fast, queries are slow")
            print("   To rebuild: python scripts\\optimize_bulk_insert.py --rebuild")
        else:
            print("\n⚠️  Database is PARTIALLY INDEXED - inconsistent state")
            print("   You may want to drop and rebuild all indexes")
        
        print()
        
    except Exception as e:
        print(f"Error checking status: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    check_status()
