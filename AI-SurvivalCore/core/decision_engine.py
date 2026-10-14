
from dataclasses import dataclass
from typing import Dict, List

from core.facility import ResourceState, SystemFunction


@dataclass
class FunctionDecision:
    name: str
    status: str
    allocated_power_w: float
    allocated_cpu_percent: float
    reason: str


def choose_operating_mode(resources: ResourceState) -> str:
    """Choose the facility's operating mode from all resource constraints."""

    if (
        resources.battery_percent <= 15
        or resources.available_power_w < 30
    ):
        return "CRITICAL_SURVIVAL"

    if (
        resources.battery_percent <= 30
        or resources.network_status == "offline"
        or resources.sensor_confidence < 0.5
        or resources.available_cpu_percent < 30
    ):
        return "SURVIVAL"

    if (
        resources.battery_percent <= 60
        or resources.available_power_w < 80
        or resources.network_status == "degraded"
        or resources.sensor_confidence < 0.8
        or resources.available_cpu_percent < 60
    ):
        return "CONSERVATION"

    return "NORMAL"


def allocate_resources(
    resources: ResourceState,
    functions: List[SystemFunction],
) -> Dict:
    """
    Allocate power and CPU to facility functions.

    Essential functions are considered first. Remaining functions
    are ordered by priority. Minimum resource requirements and
    dependencies are respected.
    """

    decisions: List[FunctionDecision] = []
    remaining_power = max(0.0, resources.available_power_w)
    remaining_cpu = max(0.0, resources.available_cpu_percent)

    mode = choose_operating_mode(resources)

    ordered = sorted(
        functions,
        key=lambda item: (not item.essential, -item.priority),
    )

    decisions_by_name: Dict[str, FunctionDecision] = {}

    for function in ordered:
        dependency_failure = any(
            dependency not in decisions_by_name
            or decisions_by_name[dependency].status == "STANDBY"
            for dependency in function.dependencies
        )

        if dependency_failure:
            decision = FunctionDecision(
                name=function.name,
                status="STANDBY",
                allocated_power_w=0.0,
                allocated_cpu_percent=0.0,
                reason="A required dependency is unavailable.",
            )
            decisions.append(decision)
            decisions_by_name[function.name] = decision
            continue

        if (
            remaining_power < function.power_minimum_w
            or remaining_cpu <= 0
        ):
            decision = FunctionDecision(
                name=function.name,
                status="STANDBY",
                allocated_power_w=0.0,
                allocated_cpu_percent=0.0,
                reason="Insufficient resources for minimum operation.",
            )
            decisions.append(decision)
            decisions_by_name[function.name] = decision
            continue

        power = min(function.power_required_w, remaining_power)
        cpu = min(function.cpu_required_percent, remaining_cpu)

        # Never run below the minimum power requirement.
        if power < function.power_minimum_w:
            decision = FunctionDecision(
                name=function.name,
                status="STANDBY",
                allocated_power_w=0.0,
                allocated_cpu_percent=0.0,
                reason="Minimum power requirement cannot be met.",
            )
            decisions.append(decision)
            decisions_by_name[function.name] = decision
            continue

        status = (
            "ACTIVE"
            if power >= function.power_required_w
            and cpu >= function.cpu_required_percent
            else "DEGRADED"
        )

        remaining_power -= power
        remaining_cpu -= cpu

        decision = FunctionDecision(
            name=function.name,
            status=status,
            allocated_power_w=power,
            allocated_cpu_percent=cpu,
            reason=(
                "Full resource requirements satisfied."
                if status == "ACTIVE"
                else "Operating with reduced resource allocation."
            ),
        )

        decisions.append(decision)
        decisions_by_name[function.name] = decision

    essential_unavailable = [
        function.name
        for function in functions
        if function.essential
        and decisions_by_name[function.name].status == "STANDBY"
    ]
    total_allocated_power_w = sum(
        decision.allocated_power_w for decision in decisions
    )
    total_allocated_cpu_percent = sum(
        decision.allocated_cpu_percent for decision in decisions
    )

    return {
        "mode": mode,
        "decisions": decisions,
        "remaining_power_w": remaining_power,
        "remaining_cpu_percent": remaining_cpu,
        "essential_unavailable": essential_unavailable,
        "allocation_feasible": not essential_unavailable,
        "total_allocated_power_w": total_allocated_power_w,
        "total_allocated_cpu_percent": total_allocated_cpu_percent,
    }
