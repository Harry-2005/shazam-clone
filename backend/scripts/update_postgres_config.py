"""
Script to automatically update PostgreSQL configuration file.
Run this with administrator privileges.
"""

import os
import shutil
from pathlib import Path


def update_postgresql_conf():
    """Update PostgreSQL configuration file."""
    
    # PostgreSQL config file path
    config_path = Path("C:/Program Files/PostgreSQL/18/data/postgresql.conf")
    
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        print("Please verify your PostgreSQL installation path.")
        return False
    
    # Create backup
    backup_path = config_path.with_suffix('.conf.backup')
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
        print("4. Run: python scripts\\update_postgres_config.py")
        return False
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return False
    
    # Read current config
    print(f"\n📖 Reading config file...")
    with open(config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Settings to update
    settings = {
        'max_parallel_workers_per_gather': '4',
        'parallel_setup_cost': '100',
        'parallel_tuple_cost': '0.001',
    }
    
    # Track which settings were found
    found_settings = set()
    new_lines = []
    
    print(f"\n🔧 Updating settings...")
    
    for line in lines:
        updated = False
        
        for setting_name, new_value in settings.items():
            # Check if this line contains the setting
            if line.strip().startswith(setting_name):
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
        new_lines.append("\n# Performance optimizations added by configure script\n")
        
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
    print("\nOption 1: Using services.msc")
    print("  1. Press Win + R")
    print("  2. Type: services.msc")
    print("  3. Find 'postgresql-x64-18' or 'PostgreSQL'")
    print("  4. Right-click → Restart")
    
    print("\nOption 2: Using PowerShell (as Administrator)")
    print("  Restart-Service postgresql-x64-18")
    
    print("\nOption 3: Using command prompt (as Administrator)")
    print('  net stop postgresql-x64-18 && net start postgresql-x64-18')
    
    print("\n💡 After restarting, verify settings:")
    print("  python scripts\\configure_parallel_workers.py --check")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    print("=" * 70)
    print("POSTGRESQL CONFIGURATION UPDATER")
    print("=" * 70)
    print("\nThis script will update your PostgreSQL configuration to:")
    print("  • max_parallel_workers_per_gather = 4")
    print("  • parallel_setup_cost = 100")
    print("  • parallel_tuple_cost = 0.001")
    print("\nA backup will be created before making changes.")
    
    input("\nPress Enter to continue or Ctrl+C to cancel...")
    
    success = update_postgresql_conf()
    
    if not success:
        print("\n❌ Configuration update failed!")
        print("You can manually edit the file:")
        print("  C:/Program Files/PostgreSQL/18/data/postgresql.conf")
    else:
        print("\n✅ All done! Don't forget to restart PostgreSQL service.")
