
from dataclasses import asdict

from core.facility import create_facility
from core.decision_engine import allocate_resources
from core.readiness_advisor import assess_readiness
from core.storm_simulator import StormEvent, apply_storm


def evaluate_scenario(event_name: str) -> dict:
    """Measure one storm scenario using a fresh facility."""

    resources, functions = create_facility()

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
        severity="critical" if event_name == "combined_disaster" else "high",
    )

    apply_storm(resources, event)
    result = allocate_resources(resources, functions)

    decisions = result["decisions"]
    readiness = assess_readiness(
        {
            "resources": asdict(resources),
            "allocation_feasible": result["allocation_feasible"],
            "essential_unavailable": result["essential_unavailable"],
        }
    )

    essential_functions = [
        function for function in functions if function.essential
    ]

    essential_running = sum(
        1
        for function in essential_functions
        if next(
            decision
            for decision in decisions
            if decision.name == function.name
        ).status != "STANDBY"
    )

    return {
        "scenario": event_name,
        "mode": result["mode"],
        "readiness_score": readiness["score"],
        "available_power_w": resources.available_power_w,
        "allocated_power_w": result["total_allocated_power_w"],
        "remaining_power_w": result["remaining_power_w"],
        "cpu_used_percent": result["total_allocated_cpu_percent"],
        "essential_functions_running": essential_running,
        "essential_functions_total": len(essential_functions),
        "essential_allocation_feasible": result["allocation_feasible"],
    }


def evaluate_all_scenarios() -> list:
    """Evaluate every supported storm scenario."""

    scenarios = [
        "power_surge",
        "network_blackout",
        "sensor_corruption",
        "cpu_degradation",
        "combined_disaster",
    ]

    return [evaluate_scenario(name) for name in scenarios]
