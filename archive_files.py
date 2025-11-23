#!/usr/bin/env python3
"""
Systematic file archival script for Miktos Streamlab cleanup
Moves outdated files to OLD Files/ with proper organization
"""

import os
import shutil
from pathlib import Path

# Base paths
BASE_DIR = Path("/Users/atorrella/Desktop/Miktos Streamlab")
OLD_FILES_DIR = BASE_DIR / "OLD Files"

# File categories to archive
TEST_RESULTS = [
    "BACKEND_TEST_RESULTS_Nov16_2025.md",
    "FEATURE_TESTING_RESULTS_Nov18_2025.md",
    "FIELD_TEST_RESULTS_Nov16_2025.md",
    "HARDWARE_TEST_RESULTS_Nov20_2025.md",
    "TEST1_30MIN_RESULTS.md",
    "TEST1_30MIN_RESULTS_SUCCESS.md",
    "TEST1_STUDIO_MODE_RESULTS.md",
    "TEST3_60MIN_LOCK_SUCCESS.md",
    "TESTING_STATUS_REPORT.md",
    "TEST_SUITE_VALIDATION_RESULTS.md",
]

TEST_PROCEDURES = [
    "FIELD_TEST_MANUAL_PROCEDURE.md",
    "HARDWARE_TESTING_GUIDE.md",
    "NETWORK_MONITORING_TEST_PROCEDURE.md",
    "REMOTE_CONTROL_TEST_PROCEDURE.md",
    "TEST1_30MIN_PROCEDURE.md",
    "WEEK1_TEST_PROCEDURE.md",
    "WIFI_DISCONNECT_TEST_PROCEDURE.md",
]

COMPLETED_DOCS = [
    "ADVANCED_DISCONNECT_DETECTION_COMPLETE.md",
    "CONTROL_PANEL_COMPLETE.md",
    "DAY1_SYSTEMATIC_VALIDATION_BREAKTHROUGH.md",
    "DEPLOYMENT_COMPLETE.md",
    "DOCUMENTATION_CREDIBILITY_AUDIT.md",
    "HARDWARE_INTEGRATION_TEST.md",
    "MIGRATION_COMPLETE.md",
    "MULTI_CAMERA_DIRECTOR_GUIDE.md",
    "PAUSE_RESUME_FEATURE.md",
    "PHASE2_COMPLETE_SUCCESS.md",
    "PHASE2_SRT_COMPLETION.md",
    "PRIORITY_IMPLEMENTATION_COMPLETE.md",
    "PRODUCTION_READY_IMPLEMENTATION.md",
    "PROJECT_VALIDATION_STATUS.md",
    "SRT_IMPLEMENTATION_GUIDE.md",
    "SYSTEMATIC_VALIDATION_ROADMAP.md",
    "VALIDATION_STATUS_UPDATE.md",
    "WEEK1_MVP_COMPLETE.md",
    "WEEK1_STUDIO_MODE_COMPLETE.md",
]

DEMO_SCRIPTS = [
    "demo_srt_implementation.py",
    "demo_srt_standalone.py",
    "test_30min_log.txt",
    "test_api_complete.py",
    "test_camera_discovery.py",
    "test_dual_path_egress.py",
    "test_obs_connection.py",
    "test_obs_simple.py",
    "test_remote_control.py",
    "tcp_h264_receiver.py",
    "tcp_h264_receiver_with_preview.py",
    "multi_camera_receiver.py",
    "remote_control.py",
]

SHELL_SCRIPTS = [
    "check_android_warnings.sh",
    "fix_android_warnings.sh",
    "start_multi_camera.sh",
    "start_testing.sh",
    "test_disconnect_detection_timing.sh",
    "test_quick_disconnect_validation.sh",
    "test_unlock_after_60min_field.sh",
]

LOG_FILES = [
    "extended_device_monitor.log",
    "extended_lock_test.log",
    "extended_network_monitor.log",
    "receiver_log.txt",
]

BACKUP_FILES = [
    "android_warnings_fixed_report.md.backup.20251114_075848",
    "connection_monitoring_fix_deployed.md.backup.20251114_024006",
    "markdown_fixes_summary.md.backup.20251114_075454",
    "android_warnings_fixed_report.md",
    "connection_monitoring_fix_deployed.md",
    "markdown_fixes_summary.md",
]

def move_files(file_list, target_subdir):
    """Move files to target subdirectory in OLD Files"""
    moved_count = 0
    errors = []
    
    for filename in file_list:
        source = BASE_DIR / filename
        target = OLD_FILES_DIR / target_subdir / filename
        
        if source.exists():
            try:
                shutil.move(str(source), str(target))
                moved_count += 1
                print(f"✓ Moved: {filename} → OLD Files/{target_subdir}/")
            except Exception as e:
                errors.append(f"✗ Error moving {filename}: {e}")
                print(f"✗ Error moving {filename}: {e}")
        else:
            print(f"⚠ Skipped (not found): {filename}")
    
    return moved_count, errors

def main():
    print("=" * 70)
    print("MIKTOS STREAMLAB FILE ARCHIVAL")
    print("=" * 70)
    print()
    
    total_moved = 0
    all_errors = []
    
    print("📦 Moving Test Results...")
    count, errors = move_files(TEST_RESULTS, "test_results")
    total_moved += count
    all_errors.extend(errors)
    print()
    
    print("📋 Moving Test Procedures...")
    count, errors = move_files(TEST_PROCEDURES, "test_procedures")
    total_moved += count
    all_errors.extend(errors)
    print()
    
    print("📄 Moving Completed Documentation...")
    count, errors = move_files(COMPLETED_DOCS, "test_results")  # These are also historical
    total_moved += count
    all_errors.extend(errors)
    print()
    
    print("🐍 Moving Demo Scripts...")
    count, errors = move_files(DEMO_SCRIPTS, "demo_scripts")
    total_moved += count
    all_errors.extend(errors)
    print()
    
    print("🔧 Moving Shell Scripts...")
    count, errors = move_files(SHELL_SCRIPTS, "shell_scripts")
    total_moved += count
    all_errors.extend(errors)
    print()
    
    print("📝 Moving Log Files...")
    count, errors = move_files(LOG_FILES, "logs")
    total_moved += count
    all_errors.extend(errors)
    print()
    
    print("💾 Moving Backup Files...")
    count, errors = move_files(BACKUP_FILES, "backups")
    total_moved += count
    all_errors.extend(errors)
    print()
    
    # Move old archive
    old_archive = BASE_DIR / "StreamLab_Test_Archive_20251114"
    if old_archive.exists():
        try:
            target = OLD_FILES_DIR / "archives" / "StreamLab_Test_Archive_20251114"
            shutil.move(str(old_archive), str(target))
            print("✓ Moved: StreamLab_Test_Archive_20251114 → OLD Files/archives/")
            total_moved += 1
        except Exception as e:
            print(f"✗ Error moving archive: {e}")
            all_errors.append(f"✗ Error moving archive: {e}")
    print()
    
    # Summary
    print("=" * 70)
    print(f"ARCHIVAL COMPLETE")
    print(f"Total files moved: {total_moved}")
    if all_errors:
        print(f"Errors encountered: {len(all_errors)}")
        for error in all_errors:
            print(f"  {error}")
    else:
        print("No errors encountered ✓")
    print("=" * 70)
    
    return total_moved, all_errors

if __name__ == "__main__":
    main()
