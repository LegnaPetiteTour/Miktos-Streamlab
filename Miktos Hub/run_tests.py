#!/usr/bin/env python3
"""
Test Runner for Miktos Hub

Provides convenient commands for running different test suites.

Usage:
    python run_tests.py                # Run all tests
    python run_tests.py unit           # Run only unit tests
    python run_tests.py integration    # Run only integration tests
    python run_tests.py api            # Run only API tests
    python run_tests.py fast           # Run only fast tests (exclude slow)
    python run_tests.py coverage       # Run tests with coverage report
    python run_tests.py verbose        # Run with verbose output
"""
import sys
import subprocess
from pathlib import Path


def run_command(cmd: list[str]) -> int:
    """Run a command and return exit code"""
    print(f"Running: {' '.join(cmd)}")
    print("=" * 60)
    result = subprocess.run(cmd)
    return result.returncode


def main():
    """Main test runner"""
    if len(sys.argv) < 2:
        # Run all tests by default
        cmd = ["pytest"]
    else:
        test_type = sys.argv[1].lower()

        if test_type == "unit":
            # Run only unit tests
            cmd = ["pytest", "-m", "unit", "-v"]

        elif test_type == "integration":
            # Run only integration tests
            cmd = ["pytest", "-m", "integration", "-v"]

        elif test_type == "api":
            # Run only API tests
            cmd = ["pytest", "-m", "api", "-v"]

        elif test_type == "fast":
            # Run only fast tests (exclude slow)
            cmd = ["pytest", "-m", "not slow", "-v"]

        elif test_type == "slow":
            # Run only slow tests
            cmd = ["pytest", "-m", "slow", "-v"]

        elif test_type == "coverage":
            # Run with coverage report
            cmd = ["pytest", "--cov=.", "--cov-report=html", "--cov-report=term"]

        elif test_type == "verbose":
            # Run with maximum verbosity
            cmd = ["pytest", "-vv", "-s"]

        elif test_type == "failed":
            # Re-run only failed tests
            cmd = ["pytest", "--lf", "-v"]

        elif test_type == "debug":
            # Run with debugging
            cmd = ["pytest", "-vv", "-s", "--pdb"]

        elif test_type == "parallel":
            # Run tests in parallel (requires pytest-xdist)
            cmd = ["pytest", "-n", "auto", "-v"]

        elif test_type == "quick":
            # Quick smoke test (fast tests only)
            cmd = ["pytest", "-m", "not slow", "-x", "--tb=short"]

        elif test_type == "help":
            print(__doc__)
            return 0

        else:
            print(f"Unknown test type: {test_type}")
            print("\nAvailable commands:")
            print("  unit         - Run unit tests")
            print("  integration  - Run integration tests")
            print("  api          - Run API tests")
            print("  fast         - Run fast tests only")
            print("  slow         - Run slow tests only")
            print("  coverage     - Run with coverage report")
            print("  verbose      - Run with verbose output")
            print("  failed       - Re-run failed tests")
            print("  debug        - Run with debugger")
            print("  parallel     - Run tests in parallel")
            print("  quick        - Quick smoke test")
            print("  help         - Show this help")
            return 1

    # Run the command
    exit_code = run_command(cmd)

    if exit_code == 0:
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ SOME TESTS FAILED")
        print("=" * 60)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
