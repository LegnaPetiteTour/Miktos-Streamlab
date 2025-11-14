"""Test quality analyzer with webcam or image"""

import sys
from pathlib import Path

# Add src to path before imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import cv2  # type: ignore[import-not-found]  # noqa: E402
from core.quality_analyzer import (  # noqa: E402
    QualityAnalyzer
)


def test_with_webcam() -> None:
    """Test quality analyzer with webcam"""

    print("=" * 70)
    print("QUALITY ANALYZER TEST - Week 13-14")
    print("=" * 70)

    # Initialize analyzer
    print("\n1️⃣  Initializing quality analyzer...")
    analyzer = QualityAnalyzer()
    print("✅ Analyzer ready")

    # Open webcam
    print("\n2️⃣  Opening webcam...")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Could not open webcam")
        print("\n💡 Tip: Try running with an image file:")
        print("   python test_quality_analyzer.py path/to/image.jpg")
        return

    print("✅ Webcam opened")
    print("\n📹 Analyzing video quality...")
    print("   Press 'q' to quit, 's' for detailed screenshot analysis\n")

    frame_count = 0
    quality = None

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        frame_count += 1

        # Analyze every 30 frames (1 second at 30fps)
        if frame_count % 30 == 0:
            quality = analyzer.analyze_frame(frame)

            print(f"\n📊 Frame {frame_count}:")
            print(
                f"   Overall Score: {quality.overall_score:.1f}/100"
            )
            print(
                f"   Exposure: {quality.exposure.percentage:.1f}% - "
                f"{quality.exposure.status}"
            )
            print(
                f"   Focus: {quality.focus.percentage:.1f}% - "
                f"{quality.focus.status}"
            )
            print(
                f"   Color: {quality.color_balance.percentage:.1f}% - "
                f"{quality.color_balance.status}"
            )
            print(
                f"   Noise: {quality.noise.percentage:.1f}% - "
                f"{quality.noise.status}"
            )

            # Show recommendations for issues
            if quality.exposure.status != "good":
                print(f"   💡 {quality.exposure.recommendation}")
            if quality.focus.status != "good":
                print(f"   💡 {quality.focus.recommendation}")

        # Display frame with score overlay
        if quality:
            score_text = f"Quality: {quality.overall_score:.0f}/100"
        else:
            score_text = "Analyzing..."

        cv2.putText(
            frame,
            score_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        cv2.imshow('Quality Analysis', frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('s') and quality:
            # Screenshot analysis
            print("\n📸 Screenshot Analysis:")

            print(f"   Overall Score: {quality.overall_score:.1f}/100")
            print("\n   Detailed Metrics:")
            for metric_name in [
                'exposure',
                'focus',
                'color_balance',
                'noise',
                'sharpness'
            ]:
                metric = getattr(quality, metric_name)
                print(f"   {metric.metric.value.upper()}:")
                print(f"     Score: {metric.percentage:.1f}%")
                print(f"     Status: {metric.status}")
                print(f"     Raw: {metric.raw_value:.2f}")
                print(f"     Tip: {metric.recommendation}")

    cap.release()
    cv2.destroyAllWindows()

    print("\n✅ Test complete")


def test_with_image(image_path: str) -> None:
    """Test with a static image"""

    print(f"\n📷 Analyzing image: {image_path}")

    # Load image
    frame = cv2.imread(image_path)

    if frame is None:
        print("❌ Could not load image")
        return

    # Analyze
    analyzer = QualityAnalyzer()
    quality = analyzer.analyze_frame(frame)

    # Print results
    print("\n📊 Quality Report:")
    print(f"   Overall Score: {quality.overall_score:.1f}/100")
    print(f"   Dimensions: {quality.width}x{quality.height}")
    print("\n   Metrics:")

    for metric_name in [
        'exposure',
        'focus',
        'color_balance',
        'noise',
        'sharpness'
    ]:
        metric = getattr(quality, metric_name)
        status_icon = (
            "✅" if metric.status == "good"
            else ("⚠️" if metric.status == "warning" else "❌")
        )
        print(
            f"   {status_icon} {metric.metric.value.upper()}: "
            f"{metric.percentage:.1f}%"
        )
        print(f"      {metric.recommendation}")

    print("\n✅ Analysis complete")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test with image file
        test_with_image(sys.argv[1])
    else:
        # Test with webcam
        test_with_webcam()
