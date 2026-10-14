
from core.fault_detector import FaultDetector


def test_valid_reading():
    detector = FaultDetector()

    result = detector.validate(
        "temperature", 30.0, 0.0, 100.0,
        timestamp=100.0, current_time=105.0
    )

    assert result.trusted is True
    assert result.confidence == 1.0


def test_missing_reading():
    detector = FaultDetector()

    result = detector.validate(
        "temperature", None, 0.0, 100.0,
        timestamp=100.0, current_time=105.0
    )

    assert result.trusted is False
    assert result.confidence == 0.0


def test_out_of_range_reading():
    detector = FaultDetector()

    result = detector.validate(
        "temperature", 150.0, 0.0, 100.0,
        timestamp=100.0, current_time=105.0
    )

    assert result.trusted is False


def test_stale_reading():
    detector = FaultDetector()

    result = detector.validate(
        "temperature", 30.0, 0.0, 100.0,
        timestamp=80.0, current_time=105.0
    )

    assert result.trusted is False


def test_suspicious_jump():
    detector = FaultDetector()

    detector.validate(
        "temperature", 20.0, 0.0, 100.0,
        timestamp=100.0, current_time=100.0
    )

    result = detector.validate(
        "temperature", 90.0, 0.0, 100.0,
        timestamp=101.0, current_time=101.0
    )

    assert result.trusted is False
    assert "rapid change" in result.reason


if __name__ == "__main__":
    test_valid_reading()
    test_missing_reading()
    test_out_of_range_reading()
    test_stale_reading()
    test_suspicious_jump()

    print("PASS: Fault detector tests completed.")
