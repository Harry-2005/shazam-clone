import sys
sys.path.append('..')

from app.database import DatabaseManager
from sqlalchemy import inspect, text

def check_indexes():
    """Check what indexes exist in the database."""
    db = DatabaseManager()
    
    print("\n" + "="*60)
    print("Database Index Report")
    print("="*60)
    
    # Check fingerprints table indexes
    with db.engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = 'fingerprints'
            ORDER BY indexname;
        """))
        
        print("\nFingerprints Table Indexes:")
        print("-"*60)
        for row in result:
            print(f"Index: {row[0]}")
            print(f"  Definition: {row[1]}")
            print()
        
        # Check table sizes
        result = conn.execute(text("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                pg_total_relation_size(schemaname||'.'||tablename) AS bytes
            FROM pg_tables
            WHERE tablename IN ('songs', 'fingerprints')
            ORDER BY bytes DESC;
        """))
        
        print("\nTable Sizes:")
        print("-"*60)
        for row in result:
            print(f"{row[1]}: {row[2]}")
    
    # Count records
    session = db.get_session()
    from app.models import Song, Fingerprint
    
    song_count = session.query(Song).count()
    fp_count = session.query(Fingerprint).count()
    
    print("\nRecord Counts:")
    print("-"*60)
    print(f"Songs: {song_count:,}")
    print(f"Fingerprints: {fp_count:,}")
    print(f"Avg fingerprints per song: {fp_count/song_count if song_count > 0 else 0:.0f}")
    
    session.close()
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    check_indexes()
