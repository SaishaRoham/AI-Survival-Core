
from core.facility import create_facility
from core.storm_simulator import (
    StormEvent,
    apply_storm,
    restore_facility,
)


def test_power_surge():
    resources, _ = create_facility()

    apply_storm(
        resources,
        StormEvent("power_surge", "Power disruption", "high"),
    )

    assert resources.available_power_w == 42.0
    assert resources.battery_percent == 75.0


def test_network_blackout():
    resources, _ = create_facility()

    apply_storm(
        resources,
        StormEvent("network_blackout", "Network failure", "high"),
    )

    assert resources.network_status == "offline"


def test_sensor_corruption():
    resources, _ = create_facility()

    apply_storm(
        resources,
        StormEvent("sensor_corruption", "Bad sensor data", "medium"),
    )

    assert 0.1 <= resources.sensor_confidence <= 0.4


def test_combined_disaster():
    resources, _ = create_facility()

    apply_storm(
        resources,
        StormEvent("combined_disaster", "Multiple failures", "critical"),
    )

    assert resources.available_power_w == 24.0
    assert resources.battery_percent == 55.0
    assert resources.network_status == "offline"
    assert resources.available_cpu_percent == 25.0
    assert 0.1 <= resources.sensor_confidence <= 0.3


def test_recovery_increases_resources():
    resources, _ = create_facility()
    resources.available_power_w = 30.0
    resources.battery_percent = 20.0

    restore_facility(resources)

    assert resources.available_power_w == 45.0
    assert resources.battery_percent == 30.0


if __name__ == "__main__":
    print("Running storm simulator tests...")

    test_power_surge()
    test_network_blackout()
    test_sensor_corruption()
    test_combined_disaster()
    test_recovery_increases_resources()

    print("PASS: All storm simulator tests completed.")
