"""
Check and configure PostgreSQL parallel worker settings for better query performance.
"""

import sys
import os
from pathlib import Path

script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.database import DatabaseManager
from sqlalchemy import text


def check_current_settings():
    """Check current PostgreSQL parallel worker settings."""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        print("=" * 70)
        print("CURRENT POSTGRESQL PARALLEL SETTINGS")
        print("=" * 70)
        
        settings = [
            ('max_parallel_workers_per_gather', 'Max workers per query'),
            ('max_worker_processes', 'Total worker processes'),
            ('max_parallel_workers', 'Max parallel workers'),
            ('parallel_setup_cost', 'Setup cost threshold'),
            ('parallel_tuple_cost', 'Per-tuple cost'),
            ('min_parallel_table_scan_size', 'Min table size for parallel'),
            ('min_parallel_index_scan_size', 'Min index size for parallel'),
        ]
        
        for setting_name, description in settings:
            result = session.execute(text(f"SHOW {setting_name};"))
            value = result.scalar()
            print(f"\n{description}:")
            print(f"  {setting_name} = {value}")
        
        print("\n" + "=" * 70)
        print("RECOMMENDATIONS FOR YOUR DATABASE")
        print("=" * 70)
        print("\n✅ Optimal settings for 418M+ fingerprints:")
        print("   max_parallel_workers_per_gather = 4")
        print("   max_worker_processes = 8")
        print("   max_parallel_workers = 8")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


def get_postgresql_conf_location():
    """Find PostgreSQL configuration file location."""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        result = session.execute(text("SHOW config_file;"))
        config_file = result.scalar()
        return config_file
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        session.close()


def apply_settings_session():
    """Apply settings for current session only (temporary)."""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        print("\n" + "=" * 70)
        print("APPLYING SETTINGS (SESSION ONLY - NOT PERMANENT)")
        print("=" * 70)
        
        commands = [
            "SET max_parallel_workers_per_gather = 4;",
            "SET parallel_setup_cost = 100;",
            "SET parallel_tuple_cost = 0.001;",
        ]
        
        for cmd in commands:
            print(f"\n{cmd}")
            session.execute(text(cmd))
            session.commit()
            print("  ✓ Applied")
        
        print("\n✅ Settings applied for this session!")
        print("⚠️  These will reset when you restart PostgreSQL")
        print("⚠️  To make permanent, edit postgresql.conf (see instructions below)")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


def show_instructions():
    """Show instructions for permanent configuration."""
    config_file = get_postgresql_conf_location()
    
    print("\n" + "=" * 70)
    print("HOW TO MAKE CHANGES PERMANENT")
    print("=" * 70)
    
    if config_file:
        print(f"\n1. Open PostgreSQL config file:")
        print(f"   {config_file}")
    else:
        print("\n1. Find your postgresql.conf file (usually in PostgreSQL data directory)")
    
    print("\n2. Add/update these lines:")
    print("   " + "-" * 60)
    print("   max_parallel_workers_per_gather = 4")
    print("   max_worker_processes = 8")
    print("   max_parallel_workers = 8")
    print("   parallel_setup_cost = 100")
    print("   parallel_tuple_cost = 0.001")
    print("   " + "-" * 60)
    
    print("\n3. Restart PostgreSQL service:")
    print("   Windows: services.msc → PostgreSQL → Restart")
    print("   Linux: sudo systemctl restart postgresql")
    
    print("\n4. Verify settings:")
    print("   python scripts\\configure_parallel_workers.py --check")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Configure PostgreSQL parallel workers")
    parser.add_argument("--check", action="store_true", help="Check current settings")
    parser.add_argument("--apply-session", action="store_true", help="Apply for current session (temporary)")
    parser.add_argument("--instructions", action="store_true", help="Show permanent configuration instructions")
    
    args = parser.parse_args()
    
    if args.check or not any([args.apply_session, args.instructions]):
        check_current_settings()
        print("\n💡 Run with --instructions to see how to configure permanently")
    
    if args.apply_session:
        apply_settings_session()
    
    if args.instructions:
        show_instructions()
