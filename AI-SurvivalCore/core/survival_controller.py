
from dataclasses import asdict
import time

from core.facility import create_facility
from core.decision_engine import allocate_resources
from core.storm_simulator import StormEvent, apply_storm
from core.fault_detector import FaultDetector


class SurvivalController:
    """Coordinates simulation, sensor validation, and survival decisions."""

    def __init__(self):
        self.resources, self.functions = create_facility()
        self.fault_detector = FaultDetector()
        self.event_history = []
        self.sensor_results = {}
        self.last_evaluation = None
        # Advance this clock with the model, not with UI render duration. That
        # keeps sensor-rate checks meaningful during a multi-step recovery.
        self.simulation_time = time.time()

    def trigger_storm(self, event_name: str):
        event_descriptions = {
            "power_surge": "Power supply degradation",
            "network_blackout": "Communication blackout",
            "sensor_corruption": "Unreliable sensor data",
            "cpu_degradation": "Computing resource degradation",
            "combined_disaster": "Multiple simultaneous failures",
        }

        if event_name not in event_descriptions:
            raise ValueError(f"Unknown event: {event_name}")

        event = StormEvent(
            name=event_name,
            description=event_descriptions[event_name],
            severity=(
                "critical"
                if event_name == "combined_disaster"
                else "high"
            ),
        )

        apply_storm(self.resources, event)
        self.simulation_time += 60.0

        self.event_history.append({
            "event": event.name,
            "description": event.description,
        })

        return self.evaluate()

    def validate_sensor(self, name, value, minimum, maximum):
        result = self.fault_detector.validate(
            sensor_name=name,
            value=value,
            minimum=minimum,
            maximum=maximum,
            timestamp=self.simulation_time,
            current_time=self.simulation_time,
        )

        self.sensor_results[name] = asdict(result)
        return result

    def recover(self):
        """Simulate one gradual recovery step after a storm."""

        from core.storm_simulator import restore_facility

        restore_facility(self.resources)
        self.simulation_time += 60.0

        self.event_history.append({
            "event": "recovery_step",
            "description": "Facility resources partially recovered",
        })

        return self.evaluate()

    def evaluate(self):
        # Validate the facility's simulated battery reading.
        battery_result = self.validate_sensor(
            "battery",
            self.resources.battery_percent,
            0.0,
            100.0,
        )

        # Never silently treat an untrusted reading as fully reliable.
        if battery_result.trusted:
            effective_confidence = min(
                self.resources.sensor_confidence,
                battery_result.confidence,
            )
        else:
            effective_confidence = 0.0

        self.resources.sensor_confidence = effective_confidence

        allocation = allocate_resources(
            self.resources,
            self.functions,
        )

        result = {
            "resources": asdict(self.resources),
            "mode": allocation["mode"],
            "decisions": [
                asdict(decision)
                for decision in allocation["decisions"]
            ],
            "remaining_power_w": allocation["remaining_power_w"],
            "remaining_cpu_percent": allocation["remaining_cpu_percent"],
            "essential_unavailable": allocation["essential_unavailable"],
            "allocation_feasible": allocation["allocation_feasible"],
            "total_allocated_power_w": allocation["total_allocated_power_w"],
            "total_allocated_cpu_percent": allocation[
                "total_allocated_cpu_percent"
            ],
            "sensor_results": dict(self.sensor_results),
            "history": list(self.event_history),
        }

        self.last_evaluation = result
        return result
