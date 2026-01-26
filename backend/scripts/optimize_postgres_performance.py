"""
Script to automatically update PostgreSQL performance settings.
Optimized for 16GB RAM system with SSD.
Run this with administrator privileges.
"""

import os
import shutil
from pathlib import Path


def update_postgresql_performance():
    """Update PostgreSQL performance configuration."""
    
    # PostgreSQL config file path
    config_path = Path("C:/Program Files/PostgreSQL/18/data/postgresql.conf")
    
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        print("Please verify your PostgreSQL installation path.")
        return False
    
    # Create backup
    backup_path = config_path.with_suffix('.conf.performance_backup')
    print(f"📁 Creating backup: {backup_path}")
    
    try:
        shutil.copy2(config_path, backup_path)
        print("✓ Backup created successfully")
    except PermissionError:
        print("\n❌ PERMISSION DENIED!")
        print("Please run this script as Administrator:")
        print("1. Right-click PowerShell")
        print("2. Select 'Run as Administrator'")
        print(f"3. Navigate to: {Path.cwd()}")
        print("4. Run: python scripts\\optimize_postgres_performance.py")
        return False
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return False
    
    # Read current config
    print(f"\n📖 Reading config file...")
    with open(config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Settings to update (optimized for 16GB RAM + SSD)
    settings = {
        # Memory settings
        'shared_buffers': '512MB',
        'effective_cache_size': '8GB',
        'work_mem': '16MB',
        
        # SSD optimization (CRITICAL)
        'random_page_cost': '1.1',
        'effective_io_concurrency': '200',
        
        # Maintenance
        'maintenance_work_mem': '256MB',
    }
    
    # Track which settings were found
    found_settings = set()
    new_lines = []
    
    print(f"\n🔧 Updating performance settings...")
    
    for line in lines:
        updated = False
        
        for setting_name, new_value in settings.items():
            # Check if this line contains the setting (commented or not)
            stripped = line.strip()
            if stripped.startswith('#'):
                stripped = stripped[1:].strip()
            
            if stripped.startswith(setting_name):
                found_settings.add(setting_name)
                # Replace the line
                new_line = f"{setting_name} = {new_value}\n"
                new_lines.append(new_line)
                print(f"  ✓ Updated: {setting_name} = {new_value}")
                updated = True
                break
        
        if not updated:
            new_lines.append(line)
    
    # Add any settings that weren't found
    if len(found_settings) < len(settings):
        print(f"\n➕ Adding missing settings...")
        new_lines.append("\n# Performance optimizations for 16GB RAM + SSD\n")
        
        for setting_name, new_value in settings.items():
            if setting_name not in found_settings:
                new_line = f"{setting_name} = {new_value}\n"
                new_lines.append(new_line)
                print(f"  ✓ Added: {setting_name} = {new_value}")
    
    # Write updated config
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"\n✅ Configuration file updated successfully!")
    except Exception as e:
        print(f"\n❌ Error writing config: {e}")
        # Restore backup
        print("Restoring backup...")
        shutil.copy2(backup_path, config_path)
        return False
    
    print("\n" + "=" * 70)
    print("⚠️  IMPORTANT: RESTART POSTGRESQL SERVICE")
    print("=" * 70)
    print("\nPerformance settings applied:")
    print("  • shared_buffers = 512MB (cache size)")
    print("  • effective_cache_size = 8GB (available RAM hint)")
    print("  • work_mem = 16MB (per-operation memory)")
    print("  • random_page_cost = 1.1 (SSD optimization)")
    print("  • effective_io_concurrency = 200 (SSD parallelism)")
    print("  • maintenance_work_mem = 256MB (index operations)")
    
    print("\n📊 Expected improvements:")
    print("  • 50-70% faster hash lookups")
    print("  • 2-3x faster for repeated queries (cached)")
    print("  • Better SSD utilization")
    print("  • Faster index operations")
    
    print("\nRestart PostgreSQL to apply changes:")
    print("  Option 1: Run restart_postgres.bat as Administrator")
    print("  Option 2: services.msc → postgresql-x64-18 → Restart")
    
    print("\n💡 After restarting, verify performance with a test query")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    print("=" * 70)
    print("POSTGRESQL PERFORMANCE OPTIMIZER")
    print("=" * 70)
    print("\nOptimizing for:")
    print("  • System: 16GB RAM")
    print("  • Storage: SSD")
    print("  • Use case: Audio fingerprint matching (418M records)")
    print("\nA backup will be created before making changes.")
    
    input("\nPress Enter to continue or Ctrl+C to cancel...")
    
    success = update_postgresql_performance()
    
    if not success:
        print("\n❌ Configuration update failed!")
        print("You can manually edit the file:")
        print("  C:/Program Files/PostgreSQL/18/data/postgresql.conf")
    else:
        print("\n✅ All done! Restart PostgreSQL to apply changes.")
