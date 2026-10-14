
import random
from dataclasses import dataclass

from core.facility import ResourceState


@dataclass
class StormEvent:
    name: str
    description: str
    severity: str


def apply_storm(
    resources: ResourceState,
    event: StormEvent,
) -> ResourceState:
    """Simulate a solar-storm event affecting facility resources."""

    if event.name == "power_surge":
        resources.available_power_w = max(
            0.0, resources.available_power_w * 0.35
        )
        resources.battery_percent = max(
            0.0, resources.battery_percent - 25
        )

    elif event.name == "network_blackout":
        resources.network_status = "offline"

    elif event.name == "sensor_corruption":
        resources.sensor_confidence = random.uniform(0.1, 0.4)

    elif event.name == "cpu_degradation":
        resources.available_cpu_percent = max(
            0.0, resources.available_cpu_percent * 0.30
        )

    elif event.name == "combined_disaster":
        resources.available_power_w = max(
            0.0, resources.available_power_w * 0.20
        )
        resources.battery_percent = max(
            0.0, resources.battery_percent - 45
        )
        resources.network_status = "offline"
        resources.sensor_confidence = random.uniform(0.1, 0.3)
        resources.available_cpu_percent = max(
            0.0, resources.available_cpu_percent * 0.25
        )

    else:
        raise ValueError(f"Unknown storm event: {event.name}")

    return resources


def restore_facility(resources: ResourceState) -> ResourceState:
    """Simulate gradual recovery after the storm."""

    resources.available_power_w = min(
        120.0, resources.available_power_w + 15.0
    )
    resources.battery_percent = min(
        100.0, resources.battery_percent + 10.0
    )
    resources.available_cpu_percent = min(
        100.0, resources.available_cpu_percent + 10.0
    )

    # Recovery of communication and sensor trust is simulated.
    if resources.network_status == "offline":
        resources.network_status = "degraded"
    elif resources.network_status == "degraded":
        resources.network_status = "online"

    resources.sensor_confidence = min(
        1.0, resources.sensor_confidence + 0.2
    )

    return resources
