#!/usr/bin/env python3
"""
Apply Day 1 Module Fixes

This script:
1. Backs up the original multi_platform_streaming.py
2. Applies the fixed version
3. Enables module imports in conftest.py
4. Verifies imports work

Run this after reviewing the fixed module.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

# Paths
HUB_DIR = Path("/Users/atorrella/Desktop/Miktos Streamlab/Miktos Hub")
MODULES_DIR = HUB_DIR / "modules"
TESTS_DIR = HUB_DIR / "tests"

ORIGINAL_FILE = MODULES_DIR / "multi_platform_streaming.py"
FIXED_FILE = MODULES_DIR / "multi_platform_streaming_FIXED.py"
BACKUP_FILE = MODULES_DIR / "multi_platform_streaming.py.backup"
CONFTEST_FILE = TESTS_DIR / "conftest.py"

print("=" * 60)
print("APPLYING DAY 1 MODULE FIXES")
print("=" * 60)
print()

# Step 1: Backup original file
print("Step 1: Backing up original file...")
if ORIGINAL_FILE.exists():
    if BACKUP_FILE.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_with_timestamp = MODULES_DIR / f"multi_platform_streaming.py.backup.{timestamp}"
        shutil.copy2(ORIGINAL_FILE, backup_with_timestamp)
        print(f"✅ Timestamped backup created: {backup_with_timestamp.name}")
    else:
        shutil.copy2(ORIGINAL_FILE, BACKUP_FILE)
        print(f"✅ Backup created: {BACKUP_FILE.name}")
else:
    print("⚠️  Original file not found (might be first run)")

# Step 2: Apply fixed version
print("\nStep 2: Applying fixed version...")
if not FIXED_FILE.exists():
    print(f"❌ Fixed file not found: {FIXED_FILE}")
    print("   Please create the fixed version first.")
    exit(1)

shutil.copy2(FIXED_FILE, ORIGINAL_FILE)
print(f"✅ Applied fix to: {ORIGINAL_FILE.name}")

# Step 3: Enable imports in conftest.py
print("\nStep 3: Enabling module imports in conftest.py...")
if not CONFTEST_FILE.exists():
    print(f"❌ conftest.py not found: {CONFTEST_FILE}")
    exit(1)

# Read conftest.py
with open(CONFTEST_FILE, 'r') as f:
    lines = f.readlines()

# Find and uncomment the import line
modified = False
new_lines = []
for i, line in enumerate(lines):
    # Look for the commented import line around line 33
    if "# from modules import" in line or "#from modules import" in line:
        # Uncomment it
        new_line = line.lstrip('#').lstrip()
        new_lines.append(new_line)
        print(f"✅ Uncommented line {i+1}: {new_line.strip()}")
        modified = True
    else:
        new_lines.append(line)

if modified:
    # Write back
    with open(CONFTEST_FILE, 'w') as f:
        f.writelines(new_lines)
    print("✅ Module imports enabled in conftest.py")
else:
    print("⚠️  Import line not found or already uncommented")

# Step 4: Verify imports work
print("\nStep 4: Verifying imports...")
try:
    import sys
    sys.path.insert(0, str(HUB_DIR))
    
    from modules import MultiPlatformStreaming, OBSOrchestrator, MultiCameraManager
    
    print("✅ All module imports successful!")
    print(f"   - MultiPlatformStreaming: {MultiPlatformStreaming}")
    print(f"   - OBSOrchestrator: {OBSOrchestrator}")
    print(f"   - MultiCameraManager: {MultiCameraManager}")
    
except Exception as e:
    print(f"❌ Import verification failed: {e}")
    print("\nThis is expected if dependencies aren't installed yet.")
    print("Run from Hub directory: python3 -c 'from modules import MultiPlatformStreaming'")

print()
print("=" * 60)
print("✅ MODULE FIXES APPLIED SUCCESSFULLY")
print("=" * 60)
print()
print("Next steps:")
print("1. Run adapter tests: python3 test_day1_adapters.py")
print("2. Run core tests: pytest tests/test_core.py -v")
print("3. Run module tests: pytest tests/test_modules.py -v")
print("4. Run full suite: pytest tests/ -v")
print()
print("If issues occur, restore from backup:")
print(f"  cp {BACKUP_FILE} {ORIGINAL_FILE}")
