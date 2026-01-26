import sys
sys.path.append('..')

from app.database import DatabaseManager
from sqlalchemy import text
import time

def add_composite_index():
    """Add composite covering index for optimal query performance."""
    db = DatabaseManager()
    
    print("\n" + "="*70)
    print("Adding Composite Covering Index")
    print("="*70)
    
    print("\nThis will create: idx_hash_song_time (hash_value, song_id, time_offset)")
    print("Expected time: 10-30 minutes for 418M rows")
    print("\nStarting index creation...")
    print("-"*70)
    
    start_time = time.time()
    
    # CONCURRENTLY requires autocommit mode (no transaction)
    conn = db.engine.connect()
    conn.execution_options(isolation_level="AUTOCOMMIT")
    
    try:
        # Create the composite index
        # CONCURRENTLY allows reads/writes during index creation
        sql = text("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_hash_song_time 
            ON fingerprints (hash_value, song_id, time_offset);
        """)
        
        conn.execute(sql)
        
        elapsed = time.time() - start_time
        minutes = int(elapsed / 60)
        seconds = int(elapsed % 60)
        
        print(f"\n✅ Index created successfully!")
        print(f"Time taken: {minutes}m {seconds}s")
        
        # Get index size
        result = conn.execute(text("""
            SELECT pg_size_pretty(pg_relation_size('idx_hash_song_time')) as size;
        """))
        size = result.fetchone()[0]
        print(f"Index size: {size}")
        
    except Exception as e:
        print(f"\n❌ Error creating index: {e}")
        return
    finally:
        conn.close()
    
    print("\n" + "="*70)
    print("Checking if old indexes can be removed...")
    print("="*70)
    
    print("\nNow that we have the composite index, these may be redundant:")
    print("  - idx_fingerprints_hash (covered by composite)")
    print("  - idx_fingerprints_time_offset (not used in queries)")
    print("\nKeeping idx_fingerprints_song_id (used for foreign key)")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    add_composite_index()
