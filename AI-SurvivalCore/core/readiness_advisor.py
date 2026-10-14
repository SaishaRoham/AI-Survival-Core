"""Explainable operational readiness scoring for the facility simulation."""


NOMINAL_POWER_W = 120.0


def assess_readiness(result: dict) -> dict:
    """Score facility readiness and return prioritized operator actions."""

    resources = result["resources"]

    power_ratio = min(
        1.0,
        max(0.0, resources["available_power_w"] / NOMINAL_POWER_W),
    )
    battery_ratio = min(
        1.0,
        max(0.0, resources["battery_percent"] / 100.0),
    )
    cpu_ratio = min(
        1.0,
        max(0.0, resources["available_cpu_percent"] / 100.0),
    )
    sensor_ratio = min(
        1.0,
        max(0.0, resources["sensor_confidence"]),
    )
    network_ratio = {
        "online": 1.0,
        "degraded": 0.5,
        "offline": 0.0,
    }.get(resources["network_status"], 0.0)
    allocation_ratio = 1.0 if result.get("allocation_feasible", True) else 0.0

    components = [
        {
            "component": "Power availability",
            "score": round(power_ratio * 25, 1),
            "weight": 25,
        },
        {
            "component": "Battery reserve",
            "score": round(battery_ratio * 25, 1),
            "weight": 25,
        },
        {
            "component": "CPU capacity",
            "score": round(cpu_ratio * 15, 1),
            "weight": 15,
        },
        {
            "component": "Sensor confidence",
            "score": round(sensor_ratio * 15, 1),
            "weight": 15,
        },
        {
            "component": "Communications",
            "score": round(network_ratio * 10, 1),
            "weight": 10,
        },
        {
            "component": "Essential allocation",
            "score": round(allocation_ratio * 10, 1),
            "weight": 10,
        },
    ]

    score = round(sum(component["score"] for component in components))
    critical_condition = (
        resources["available_power_w"] < 30
        or resources["battery_percent"] <= 15
        or not result.get("allocation_feasible", True)
    )
    if critical_condition:
        status = "Critical"
    elif score >= 85:
        status = "Mission ready"
    elif score >= 65:
        status = "Strained"
    elif score >= 40:
        status = "At risk"
    else:
        status = "Critical"

    recommendations = []
    power_w = resources["available_power_w"]
    battery_percent = resources["battery_percent"]
    cpu_percent = resources["available_cpu_percent"]
    sensor_confidence = resources["sensor_confidence"]
    network_status = resources["network_status"]

    if not result.get("allocation_feasible", True):
        unavailable = result.get("essential_unavailable", [])
        names = ", ".join(unavailable) or "essential functions"
        recommendations.append({
            "priority": "Critical",
            "action": "Restore essential service",
            "detail": f"No minimum allocation for: {names}.",
        })

    if power_w < 30:
        recommendations.append({
            "priority": "Critical",
            "action": "Recover generation capacity",
            "detail": f"Available power is critically low at {power_w:.1f} W.",
        })
    elif power_w < 80:
        recommendations.append({
            "priority": "High",
            "action": "Conserve electrical load",
            "detail": f"Only {power_w:.1f} W is available; defer nonessential loads.",
        })

    if battery_percent <= 15:
        recommendations.append({
            "priority": "Critical",
            "action": "Protect battery reserve",
            "detail": f"Battery reserve is critically low at {battery_percent:.0f}%.",
        })
    elif battery_percent < 50:
        recommendations.append({
            "priority": "High",
            "action": "Prioritize battery recharge",
            "detail": f"Battery reserve is {battery_percent:.0f}%.",
        })

    if cpu_percent < 30:
        recommendations.append({
            "priority": "High",
            "action": "Defer nonessential computation",
            "detail": f"Only {cpu_percent:.0f}% CPU capacity remains.",
        })
    elif cpu_percent < 60:
        recommendations.append({
            "priority": "Medium",
            "action": "Limit background analysis",
            "detail": f"CPU capacity is constrained at {cpu_percent:.0f}%.",
        })

    if network_status == "offline":
        recommendations.append({
            "priority": "High",
            "action": "Use local control procedures",
            "detail": "Remote communications are offline; verify local telemetry.",
        })
    elif network_status == "degraded":
        recommendations.append({
            "priority": "Medium",
            "action": "Verify communication links",
            "detail": "Network service is degraded.",
        })

    if sensor_confidence < 0.5:
        recommendations.append({
            "priority": "High",
            "action": "Cross-check sensor readings",
            "detail": f"Sensor confidence is low at {sensor_confidence:.2f}.",
        })
    elif sensor_confidence < 0.8:
        recommendations.append({
            "priority": "Medium",
            "action": "Confirm readings before load changes",
            "detail": f"Sensor confidence is reduced at {sensor_confidence:.2f}.",
        })

    if not recommendations:
        recommendations.append({
            "priority": "Routine",
            "action": "Maintain monitoring",
            "detail": "Resources and essential allocations are within nominal limits.",
        })

    priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Routine": 3}
    recommendations.sort(key=lambda item: priority_order[item["priority"]])

    return {
        "score": score,
        "status": status,
        "components": components,
        "recommendations": recommendations,
    }