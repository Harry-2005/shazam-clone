import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import DatabaseManager
from sqlalchemy import text

db = DatabaseManager()
session = db.get_session()

# Get table sizes
result = session.execute(text("""
    SELECT 
        pg_size_pretty(pg_relation_size('fingerprints')) as fingerprints_table,
        pg_size_pretty(pg_relation_size('songs')) as songs_table,
        pg_size_pretty(pg_indexes_size('fingerprints')) as fingerprints_indexes,
        pg_size_pretty(pg_total_relation_size('fingerprints') - pg_relation_size('fingerprints')) as fingerprints_overhead
""")).first()

print(f"\nDatabase Size Breakdown:")
print(f"=" * 60)
print(f"Fingerprints table (data):    {result[0]}")
print(f"Songs table:                  {result[1]}")
print(f"Fingerprints indexes:         {result[2]}")
print(f"Fingerprints overhead (TOAST):{result[3]}")
print(f"=" * 60)

# Calculate per-fingerprint cost
total_fps = session.execute(text("SELECT COUNT(*) FROM fingerprints")).scalar()
print(f"\nTotal fingerprints: {total_fps:,}")
print(f"Average per fingerprint: ~{54 * 1024 / (total_fps / 1000000):.2f} KB")

session.close()
