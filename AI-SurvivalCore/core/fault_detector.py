
from dataclasses import dataclass
from typing import Optional


@dataclass
class SensorResult:
    value: Optional[float]
    trusted: bool
    confidence: float
    reason: str


class FaultDetector:
    """Validate sensor readings before they influence decisions."""

    def __init__(self):
        self.previous_values = {}

    def validate(
        self,
        sensor_name: str,
        value: Optional[float],
        minimum: float,
        maximum: float,
        timestamp: float,
        max_age_seconds: float = 10.0,
        current_time: Optional[float] = None,
    ) -> SensorResult:

        import time

        now = time.time() if current_time is None else current_time

        if value is None:
            return SensorResult(
                None, False, 0.0, "Missing sensor reading."
            )

        if not minimum <= value <= maximum:
            return SensorResult(
                value, False, 0.0, "Reading outside valid range."
            )

        age = now - timestamp

        if age < 0 or age > max_age_seconds:
            return SensorResult(
                value, False, 0.0, "Reading is stale or timestamp is invalid."
            )

        previous = self.previous_values.get(sensor_name)

        if previous is not None:
            previous_value, previous_timestamp = previous
            elapsed = timestamp - previous_timestamp

            if elapsed > 0:
                rate = abs(value - previous_value) / elapsed

                # Generic configurable jump detector.
                # Tune per sensor in a later phase.
                if rate > (maximum - minimum) * 0.5:
                    return SensorResult(
                        value,
                        False,
                        0.2,
                        "Suspiciously rapid change detected.",
                    )

        self.previous_values[sensor_name] = (value, timestamp)

        return SensorResult(
            value, True, 1.0, "Reading passed validation."
        )
