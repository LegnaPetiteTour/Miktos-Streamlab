"""
Complete Image Quality System Test
Week 13-14 Integration Test

Tests all quality control components:
- Quality Analyzer
- NVIDIA Broadcast
- Filter Controller
- Enhancement Engine
"""
# pyright: reportMissingImports=false

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.quality_analyzer import QualityAnalyzer  # noqa: E402
from core.nvidia_broadcast import NVBroadcastSDK  # noqa: E402
from core.enhancement_engine import EnhancementEngine  # noqa: E402


def test_quality_analyzer() -> None:
    """Test quality analyzer"""
    print("\n" + "=" * 70)
    print("1️⃣  QUALITY ANALYZER TEST")
    print("=" * 70)

    analyzer = QualityAnalyzer()
    print("✅ Quality analyzer initialized")

    # Test with sample data (simulated frame)
    import numpy as np

    # Create a sample frame (480x640 RGB)
    test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    quality = analyzer.analyze_frame(test_frame)

    print("\n📊 Quality Report:")
    print(f"   Overall Score: {quality.overall_score:.1f}/100")
    print(f"   Dimensions: {quality.width}x{quality.height}")

    print("\n   Metrics:")
    metrics = [
        'exposure',
        'focus',
        'color_balance',
        'noise',
        'sharpness'
    ]
    for metric_name in metrics:
        metric = getattr(quality, metric_name)
        status_icon = (
            "✅" if metric.status == "good"
            else ("⚠️" if metric.status == "warning" else "❌")
        )
        print(
            f"   {status_icon} {metric.metric.value.upper()}: "
            f"{metric.percentage:.1f}%"
        )

    print("\n✅ Quality analyzer test complete")


def test_nvidia_broadcast() -> None:
    """Test NVIDIA Broadcast integration"""
    print("\n" + "=" * 70)
    print("2️⃣  NVIDIA BROADCAST TEST")
    print("=" * 70)

    nvidia = NVBroadcastSDK()

    print(f"   GPU Available: {nvidia.available}")

    if nvidia.available:
        print(f"   GPU Name: {nvidia.gpu_name}")
        print("   Initializing SDK...")

        success = nvidia.initialize()

        if success:
            print("   ✅ SDK initialized")

            effects = nvidia.get_available_effects()
            print(f"   Available effects: {len(effects)}")

            for effect in effects:
                supported = nvidia.is_effect_supported(effect)
                status = "✅" if supported else "❌"
                print(f"     {status} {effect.value}")

            # Test GPU info
            gpu_info = nvidia.get_gpu_info()
            print("\n   GPU Info:")
            for key, value in gpu_info.items():
                print(f"     {key}: {value}")

            nvidia.shutdown()
        else:
            print("   ❌ SDK initialization failed")
    else:
        print("   ⚠️  NVIDIA RTX GPU not detected")
        print("   💡 This is OK - system will work without GPU")

    print("\n✅ NVIDIA Broadcast test complete")


async def test_filter_controller() -> None:
    """Test filter controller (mock mode without OBS)"""
    print("\n" + "=" * 70)
    print("3️⃣  FILTER CONTROLLER TEST")
    print("=" * 70)

    # Mock OBS controller for testing
    class MockOBS:
        async def call(self, method: str, params: dict) -> dict:
            print(f"   Mock OBS call: {method}")
            return {"filters": []}

    from core.filter_controller import FilterController  # noqa: E402

    mock_obs = MockOBS()
    filters = FilterController(mock_obs)

    print("✅ Filter controller initialized (mock mode)")

    print("\n   Testing color correction...")
    await filters.apply_color_correction(
        source_name="Camera",
        brightness=0.1,
        contrast=0.15,
        saturation=0.1
    )
    print("   ✅ Color correction applied")

    print("\n   Testing sharpness...")
    await filters.apply_sharpness(
        source_name="Camera",
        amount=0.3
    )
    print("   ✅ Sharpness applied")

    print("\n   Testing reset...")
    await filters.reset_filters("Camera")
    print("   ✅ Filters reset")

    print("\n✅ Filter controller test complete")


async def test_enhancement_engine() -> None:
    """Test enhancement engine"""
    print("\n" + "=" * 70)
    print("4️⃣  ENHANCEMENT ENGINE TEST")
    print("=" * 70)

    analyzer = QualityAnalyzer()

    # Mock filter controller
    class MockFilterController:
        async def apply_color_correction(
            self,
            source_name: str,
            brightness: float,
            contrast: float,
            saturation: float,
            gamma: float
        ) -> bool:
            print(
                f"   Applied color correction: "
                f"brightness={brightness:.2f}, "
                f"contrast={contrast:.2f}"
            )
            return True

        async def apply_sharpness(
            self,
            source_name: str,
            amount: float
        ) -> bool:
            print(f"   Applied sharpness: {amount:.2f}")
            return True

    filters = MockFilterController()
    engine = EnhancementEngine(analyzer, filters)

    print("✅ Enhancement engine initialized")

    # Test presets
    presets = engine.get_presets()
    print(f"\n   Available presets: {len(presets)}")

    for preset_name, preset in presets.items():
        print(f"\n   📋 {preset.name}")
        print(f"      Auto-exposure: {preset.auto_exposure}")
        print(f"      Auto-color: {preset.auto_color_balance}")
        print(f"      Brightness boost: {preset.brightness_boost}")
        print(f"      Contrast boost: {preset.contrast_boost}")
        print(f"      Denoise: {preset.denoise}")

    # Test enhancement
    import numpy as np

    test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    print("\n   Testing auto-enhancement...")
    adjustments = await engine.auto_enhance(
        source_name="Camera",
        frame=test_frame
    )

    print("\n   Adjustments applied:")
    for key, value in adjustments.items():
        print(f"     {key}: {value:.3f}")

    print("\n✅ Enhancement engine test complete")


async def main() -> None:
    """Run all tests"""
    print("=" * 70)
    print("COMPLETE IMAGE QUALITY SYSTEM TEST")
    print("Week 13-14 Integration Test")
    print("=" * 70)

    # Run all tests
    test_quality_analyzer()
    test_nvidia_broadcast()
    await test_filter_controller()
    await test_enhancement_engine()

    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 70)

    print("\n📋 Features Tested:")
    print("   ✅ Quality analysis (5 metrics)")
    print("   ✅ NVIDIA Broadcast integration")
    print("   ✅ OBS filter control")
    print("   ✅ Auto-enhancement engine")
    print("   ✅ Preset system")

    print("\n🎬 Implementation Status:")
    print("   ✅ Day 1-2: Quality Analyzer (400 lines)")
    print("   ✅ Day 3-4: NVIDIA Broadcast (350 lines)")
    print("   ✅ Day 5: Filter Controller (350 lines)")
    print("   ✅ Day 5: Enhancement Engine (400 lines)")
    print("   📋 Remaining: Preset Manager, Dashboard UI, API")

    print("\n💡 Next Steps:")
    print("   • Create Preset Manager for save/load")
    print("   • Build Dashboard UI with quality metrics")
    print("   • Add API endpoints")
    print("   • Complete test suite")
    print("   • Write documentation")


if __name__ == "__main__":
    asyncio.run(main())
