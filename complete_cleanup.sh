#!/bin/bash
# Miktos Streamlab Cleanup Script
# Moves remaining outdated files to OLD Files folder
# Generated: $(date)

set -e  # Exit on error

BASE_DIR="/Users/atorrella/Desktop/Miktos Streamlab"
OLD_FILES="$BASE_DIR/OLD Files"

echo "========================================================================"
echo "MIKTOS STREAMLAB FILE ARCHIVAL - REMAINING FILES"
echo "========================================================================"
echo ""

# Function to move file if it exists
move_if_exists() {
    local source="$1"
    local target="$2"
    if [ -f "$source" ]; then
        mv "$source" "$target"
        echo "✓ Moved: $(basename "$source")"
    else
        echo "⚠ Skipped (not found): $(basename "$source")"
    fi
}

# Test Results (remaining)
echo "📦 Moving remaining test results..."
move_if_exists "$BASE_DIR/TEST1_30MIN_RESULTS.md" "$OLD_FILES/test_results/TEST1_30MIN_RESULTS.md"
move_if_exists "$BASE_DIR/TEST1_STUDIO_MODE_RESULTS.md" "$OLD_FILES/test_results/TEST1_STUDIO_MODE_RESULTS.md"
move_if_exists "$BASE_DIR/TESTING_STATUS_REPORT.md" "$OLD_FILES/test_results/TESTING_STATUS_REPORT.md"
move_if_exists "$BASE_DIR/TEST_SUITE_VALIDATION_RESULTS.md" "$OLD_FILES/test_results/TEST_SUITE_VALIDATION_RESULTS.md"
echo ""

# Test Procedures
echo "📋 Moving test procedures..."
move_if_exists "$BASE_DIR/FIELD_TEST_MANUAL_PROCEDURE.md" "$OLD_FILES/test_procedures/FIELD_TEST_MANUAL_PROCEDURE.md"
move_if_exists "$BASE_DIR/HARDWARE_TESTING_GUIDE.md" "$OLD_FILES/test_procedures/HARDWARE_TESTING_GUIDE.md"
move_if_exists "$BASE_DIR/NETWORK_MONITORING_TEST_PROCEDURE.md" "$OLD_FILES/test_procedures/NETWORK_MONITORING_TEST_PROCEDURE.md"
move_if_exists "$BASE_DIR/REMOTE_CONTROL_TEST_PROCEDURE.md" "$OLD_FILES/test_procedures/REMOTE_CONTROL_TEST_PROCEDURE.md"
move_if_exists "$BASE_DIR/TEST1_30MIN_PROCEDURE.md" "$OLD_FILES/test_procedures/TEST1_30MIN_PROCEDURE.md"
move_if_exists "$BASE_DIR/WEEK1_TEST_PROCEDURE.md" "$OLD_FILES/test_procedures/WEEK1_TEST_PROCEDURE.md"
move_if_exists "$BASE_DIR/WIFI_DISCONNECT_TEST_PROCEDURE.md" "$OLD_FILES/test_procedures/WIFI_DISCONNECT_TEST_PROCEDURE.md"
echo ""

# Completed Documentation (remaining)
echo "📄 Moving completed documentation..."
move_if_exists "$BASE_DIR/DAY1_SYSTEMATIC_VALIDATION_BREAKTHROUGH.md" "$OLD_FILES/test_results/DAY1_SYSTEMATIC_VALIDATION_BREAKTHROUGH.md"
move_if_exists "$BASE_DIR/DEPLOYMENT_COMPLETE.md" "$OLD_FILES/test_results/DEPLOYMENT_COMPLETE.md"
move_if_exists "$BASE_DIR/DOCUMENTATION_CREDIBILITY_AUDIT.md" "$OLD_FILES/test_results/DOCUMENTATION_CREDIBILITY_AUDIT.md"
move_if_exists "$BASE_DIR/HARDWARE_INTEGRATION_TEST.md" "$OLD_FILES/test_results/HARDWARE_INTEGRATION_TEST.md"
move_if_exists "$BASE_DIR/MIGRATION_COMPLETE.md" "$OLD_FILES/test_results/MIGRATION_COMPLETE.md"
move_if_exists "$BASE_DIR/MULTI_CAMERA_DIRECTOR_GUIDE.md" "$OLD_FILES/test_results/MULTI_CAMERA_DIRECTOR_GUIDE.md"
move_if_exists "$BASE_DIR/PAUSE_RESUME_FEATURE.md" "$OLD_FILES/test_results/PAUSE_RESUME_FEATURE.md"
move_if_exists "$BASE_DIR/PHASE2_COMPLETE_SUCCESS.md" "$OLD_FILES/test_results/PHASE2_COMPLETE_SUCCESS.md"
move_if_exists "$BASE_DIR/PHASE2_SRT_COMPLETION.md" "$OLD_FILES/test_results/PHASE2_SRT_COMPLETION.md"
move_if_exists "$BASE_DIR/PRIORITY_IMPLEMENTATION_COMPLETE.md" "$OLD_FILES/test_results/PRIORITY_IMPLEMENTATION_COMPLETE.md"
move_if_exists "$BASE_DIR/PRODUCTION_READY_IMPLEMENTATION.md" "$OLD_FILES/test_results/PRODUCTION_READY_IMPLEMENTATION.md"
move_if_exists "$BASE_DIR/PROJECT_VALIDATION_STATUS.md" "$OLD_FILES/test_results/PROJECT_VALIDATION_STATUS.md"
move_if_exists "$BASE_DIR/SRT_IMPLEMENTATION_GUIDE.md" "$OLD_FILES/test_results/SRT_IMPLEMENTATION_GUIDE.md"
move_if_exists "$BASE_DIR/SYSTEMATIC_VALIDATION_ROADMAP.md" "$OLD_FILES/test_results/SYSTEMATIC_VALIDATION_ROADMAP.md"
move_if_exists "$BASE_DIR/VALIDATION_STATUS_UPDATE.md" "$OLD_FILES/test_results/VALIDATION_STATUS_UPDATE.md"
move_if_exists "$BASE_DIR/WEEK1_MVP_COMPLETE.md" "$OLD_FILES/test_results/WEEK1_MVP_COMPLETE.md"
move_if_exists "$BASE_DIR/WEEK1_STUDIO_MODE_COMPLETE.md" "$OLD_FILES/test_results/WEEK1_STUDIO_MODE_COMPLETE.md"
echo ""

# Demo Scripts (remaining)
echo "🐍 Moving demo scripts..."
move_if_exists "$BASE_DIR/test_30min_log.txt" "$OLD_FILES/demo_scripts/test_30min_log.txt"
move_if_exists "$BASE_DIR/test_api_complete.py" "$OLD_FILES/demo_scripts/test_api_complete.py"
move_if_exists "$BASE_DIR/test_camera_discovery.py" "$OLD_FILES/demo_scripts/test_camera_discovery.py"
move_if_exists "$BASE_DIR/test_dual_path_egress.py" "$OLD_FILES/demo_scripts/test_dual_path_egress.py"
move_if_exists "$BASE_DIR/test_obs_connection.py" "$OLD_FILES/demo_scripts/test_obs_connection.py"
move_if_exists "$BASE_DIR/test_obs_simple.py" "$OLD_FILES/demo_scripts/test_obs_simple.py"
move_if_exists "$BASE_DIR/test_remote_control.py" "$OLD_FILES/demo_scripts/test_remote_control.py"
move_if_exists "$BASE_DIR/tcp_h264_receiver.py" "$OLD_FILES/demo_scripts/tcp_h264_receiver.py"
move_if_exists "$BASE_DIR/tcp_h264_receiver_with_preview.py" "$OLD_FILES/demo_scripts/tcp_h264_receiver_with_preview.py"
move_if_exists "$BASE_DIR/remote_control.py" "$OLD_FILES/demo_scripts/remote_control.py"
echo ""

# Shell Scripts
echo "🔧 Moving shell scripts..."
move_if_exists "$BASE_DIR/check_android_warnings.sh" "$OLD_FILES/shell_scripts/check_android_warnings.sh"
move_if_exists "$BASE_DIR/fix_android_warnings.sh" "$OLD_FILES/shell_scripts/fix_android_warnings.sh"
move_if_exists "$BASE_DIR/start_multi_camera.sh" "$OLD_FILES/shell_scripts/start_multi_camera.sh"
move_if_exists "$BASE_DIR/start_testing.sh" "$OLD_FILES/shell_scripts/start_testing.sh"
move_if_exists "$BASE_DIR/test_disconnect_detection_timing.sh" "$OLD_FILES/shell_scripts/test_disconnect_detection_timing.sh"
move_if_exists "$BASE_DIR/test_quick_disconnect_validation.sh" "$OLD_FILES/shell_scripts/test_quick_disconnect_validation.sh"
move_if_exists "$BASE_DIR/test_unlock_after_60min_field.sh" "$OLD_FILES/shell_scripts/test_unlock_after_60min_field.sh"
echo ""

# Log Files
echo "📝 Moving log files..."
move_if_exists "$BASE_DIR/extended_device_monitor.log" "$OLD_FILES/logs/extended_device_monitor.log"
move_if_exists "$BASE_DIR/extended_lock_test.log" "$OLD_FILES/logs/extended_lock_test.log"
move_if_exists "$BASE_DIR/extended_network_monitor.log" "$OLD_FILES/logs/extended_network_monitor.log"
move_if_exists "$BASE_DIR/receiver_log.txt" "$OLD_FILES/logs/receiver_log.txt"
echo ""

# Backup Files
echo "💾 Moving backup files..."
move_if_exists "$BASE_DIR/android_warnings_fixed_report.md.backup.20251114_075848" "$OLD_FILES/backups/android_warnings_fixed_report.md.backup.20251114_075848"
move_if_exists "$BASE_DIR/connection_monitoring_fix_deployed.md.backup.20251114_024006" "$OLD_FILES/backups/connection_monitoring_fix_deployed.md.backup.20251114_024006"
move_if_exists "$BASE_DIR/markdown_fixes_summary.md.backup.20251114_075454" "$OLD_FILES/backups/markdown_fixes_summary.md.backup.20251114_075454"
move_if_exists "$BASE_DIR/android_warnings_fixed_report.md" "$OLD_FILES/backups/android_warnings_fixed_report.md"
move_if_exists "$BASE_DIR/connection_monitoring_fix_deployed.md" "$OLD_FILES/backups/connection_monitoring_fix_deployed.md"
move_if_exists "$BASE_DIR/markdown_fixes_summary.md" "$OLD_FILES/backups/markdown_fixes_summary.md"
echo ""

# Build Artifacts
echo "🔨 Moving build artifacts..."
if [ -d "$BASE_DIR/__pycache__" ]; then
    mv "$BASE_DIR/__pycache__" "$OLD_FILES/build_artifacts/__pycache__"
    echo "✓ Moved: __pycache__"
fi
if [ -d "$BASE_DIR/.mypy_cache" ]; then
    mv "$BASE_DIR/.mypy_cache" "$OLD_FILES/build_artifacts/.mypy_cache"
    echo "✓ Moved: .mypy_cache"
fi
if [ -f "$BASE_DIR/.DS_Store" ]; then
    mv "$BASE_DIR/.DS_Store" "$OLD_FILES/build_artifacts/.DS_Store"
    echo "✓ Moved: .DS_Store"
fi
echo ""

echo "========================================================================"
echo "CLEANUP COMPLETE!"
echo "All outdated files have been archived to OLD Files/"
echo "========================================================================"
