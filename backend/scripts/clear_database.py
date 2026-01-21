#!/usr/bin/env python3
"""
Clear all songs and fingerprints from the database.
"""

import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import DatabaseManager
from app.models import Base

def clear_database():
    """Drop all tables and recreate them (removes all data)."""
    
    db_manager = DatabaseManager()
    
    print("=" * 60)
    print("WARNING: This will DELETE ALL songs and fingerprints!")
    print("=" * 60)
    
    # Drop all tables
    print("\n🗑️  Dropping all tables...")
    Base.metadata.drop_all(bind=db_manager.engine)
    print("✓ All tables dropped")
    
    # Recreate tables
    print("\n🔨 Recreating tables...")
    Base.metadata.create_all(bind=db_manager.engine)
    print("✓ Tables recreated")
    
    # Verify
    stats = db_manager.get_database_stats()
    print("\n" + "=" * 60)
    print("DATABASE CLEARED SUCCESSFULLY")
    print("=" * 60)
    print(f"Total songs: {stats['total_songs']}")
    print(f"Total fingerprints: {stats['total_fingerprints']}")
    print()

if __name__ == "__main__":
    clear_database()
