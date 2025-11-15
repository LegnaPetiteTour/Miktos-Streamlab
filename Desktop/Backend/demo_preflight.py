#!/usr/bin/env python3
"""
Demo script for the preflight validation system.

This demonstrates how to use the PreflightValidator to check
if the system is ready for streaming.
"""

import asyncio

from core.preflight import PreflightValidator


async def main() -> None:
    """Run preflight validation demo."""
    print("🎬 Miktos StreamLab - Preflight Validation Demo\n")
    print("=" * 60)

    # Create validator
    print("\n1. Creating preflight validator...")
    validator = PreflightValidator()

    # Run all checks
    print("\n2. Running all preflight checks...")
    result = await validator.run_all_checks()

    # Display results
    print("\n3. Results:")
    print(f"   Overall Status: {result.overall_status.value.upper()}")
    print(f"   Can Stream: {'✅ YES' if result.can_stream else '❌ NO'}")
    print(f"   Duration: {result.duration:.2f}s")

    # Show summary
    summary = result.get_summary()
    print("\n4. Summary:")
    print(f"   Total Checks: {summary['total_checks']}")
    print(f"   ✅ Passed: {summary['passed']}")
    print(f"   ⚠️  Warnings: {summary['warnings']}")
    print(f"   ❌ Failed: {summary['failed']}")

    # Show individual checks
    print("\n5. Individual Checks:")
    for check in result.checks:
        status_icon = {
            "passed": "✅",
            "warning": "⚠️",
            "failed": "❌",
            "skipped": "⏭️",
        }.get(check.status.value, "❓")

        print(f"   {status_icon} {check.check.value}: {check.message}")

        # Show recommendation for failed/warning checks
        if check.status.value in ["failed", "warning"] and check.recommendation:
            print(f"      → {check.recommendation}")

    # Show warnings and errors
    if result.warnings:
        print("\n⚠️  Warnings:")
        for warning in result.warnings:
            print(f"   - {warning}")

    if result.errors:
        print("\n❌ Errors:")
        for error in result.errors:
            print(f"   - {error}")

    # Show overall recommendation
    if not result.can_stream:
        print("\n💡 Recommendations:")
        if "OBS controller not available" in result.errors:
            print("   - Start OBS Studio and enable WebSocket server")
            print("   - Configure connection in Settings → WebSocket Server")
        print("   - Address critical issues above before streaming")

    print("\n" + "=" * 60)
    print("✨ Preflight validation complete!")


if __name__ == "__main__":
    asyncio.run(main())
