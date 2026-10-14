
from dataclasses import dataclass, field
from typing import List


@dataclass
class ResourceState:
    """Current resource availability in the remote facility."""

    available_power_w: float = 120.0
    available_cpu_percent: float = 100.0
    network_status: str = "online"
    sensor_confidence: float = 1.0
    battery_percent: float = 100.0


@dataclass
class SystemFunction:
    """A function that the facility needs to keep operating."""

    name: str
    priority: int
    power_required_w: float
    power_minimum_w: float
    cpu_required_percent: float
    dependencies: List[str] = field(default_factory=list)
    essential: bool = False


def create_facility():
    """Create the initial remote-facility simulation."""

    resources = ResourceState(
        available_power_w=120.0,
        available_cpu_percent=100.0,
        network_status="online",
        sensor_confidence=1.0,
        battery_percent=100.0,
    )

    functions = [
        SystemFunction(
            name="Environmental Monitoring",
            priority=10,
            power_required_w=20.0,
            power_minimum_w=10.0,
            cpu_required_percent=10.0,
            essential=True,
        ),
        SystemFunction(
            name="Emergency Communications",
            priority=9,
            power_required_w=25.0,
            power_minimum_w=10.0,
            cpu_required_percent=15.0,
            dependencies=["Environmental Monitoring"],
            essential=True,
        ),
        SystemFunction(
            name="Local Decision Engine",
            priority=10,
            power_required_w=20.0,
            power_minimum_w=12.0,
            cpu_required_percent=25.0,
            essential=True,
        ),
        SystemFunction(
            name="Scientific Analytics",
            priority=4,
            power_required_w=30.0,
            power_minimum_w=10.0,
            cpu_required_percent=30.0,
        ),
        SystemFunction(
            name="Entertainment Display",
            priority=1,
            power_required_w=15.0,
            power_minimum_w=5.0,
            cpu_required_percent=10.0,
        ),
    ]

    return resources, functions
