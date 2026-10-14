"""Explainable insights derived from the facility simulation result."""


def build_operational_insights(result: dict, readiness: dict) -> dict:
    resources = result["resources"]
    decisions = result.get("decisions", [])
    essential_unavailable = result.get("essential_unavailable", [])
    standby_services = [
        decision["name"]
        for decision in decisions
        if decision["status"] == "STANDBY"
    ]
    degraded_services = [
        decision["name"]
        for decision in decisions
        if decision["status"] == "DEGRADED"
    ]

    if not result.get("allocation_feasible", True) or result["mode"] == "CRITICAL_SURVIVAL":
        risk_level = "Critical"
    elif result["mode"] == "SURVIVAL":
        risk_level = "High"
    elif result["mode"] == "CONSERVATION":
        risk_level = "Elevated"
    else:
        risk_level = "Low"

    if essential_unavailable:
        summary = (
            "The automatic allocator cannot meet minimum power for essential "
            f"functions: {', '.join(essential_unavailable)}."
        )
    elif standby_services:
        summary = (
            "The automatic allocator kept essential functions out of standby "
            f"and shed {len(standby_services)} lower-priority service(s)."
        )
    elif degraded_services:
        summary = (
            "The automatic allocator kept services running with reduced "
            f"capacity for {len(degraded_services)} function(s)."
        )
    else:
        summary = (
            f"The automatic allocator met current requirements for "
            f"{len(decisions)} simulated functions."
        )

    risk_signals = []
    if essential_unavailable:
        risk_signals.append(
            {
                "Signal": "Essential allocation",
                "Severity": "Critical",
                "Finding": ", ".join(essential_unavailable),
            }
        )
    if resources["available_power_w"] < 80:
        risk_signals.append(
            {
                "Signal": "Available power",
                "Severity": "Critical" if resources["available_power_w"] < 30 else "High",
                "Finding": f'{resources["available_power_w"]:.1f} W available',
            }
        )
    if resources["battery_percent"] <= 30:
        risk_signals.append(
            {
                "Signal": "Battery reserve",
                "Severity": "Critical" if resources["battery_percent"] <= 15 else "High",
                "Finding": f'{resources["battery_percent"]:.0f}% remaining',
            }
        )
    if resources["available_cpu_percent"] < 60:
        risk_signals.append(
            {
                "Signal": "CPU capacity",
                "Severity": "High" if resources["available_cpu_percent"] < 30 else "Medium",
                "Finding": f'{resources["available_cpu_percent"]:.0f}% available',
            }
        )
    if resources["network_status"] != "online":
        risk_signals.append(
            {
                "Signal": "Communications",
                "Severity": "High" if resources["network_status"] == "offline" else "Medium",
                "Finding": resources["network_status"].capitalize(),
            }
        )
    if resources["sensor_confidence"] < 0.8:
        risk_signals.append(
            {
                "Signal": "Sensor confidence",
                "Severity": "High" if resources["sensor_confidence"] < 0.5 else "Medium",
                "Finding": f'{resources["sensor_confidence"]:.0%}',
            }
        )

    available_power = resources["available_power_w"]
    allocated_power = result.get("total_allocated_power_w", 0.0)
    power_utilization = (
        allocated_power / available_power * 100 if available_power > 0 else 0.0
    )

    return {
        "risk_level": risk_level,
        "summary": summary,
        "risk_signals": risk_signals,
        "recommendation": readiness["recommendations"][0],
        "essential_unavailable": essential_unavailable,
        "standby_services": standby_services,
        "degraded_services": degraded_services,
        "active_count": sum(decision["status"] == "ACTIVE" for decision in decisions),
        "standby_count": len(standby_services),
        "degraded_count": len(degraded_services),
        "power_utilization_percent": round(power_utilization, 1),
    }