from core.facility import ResourceState
from core.readiness_advisor import assess_readiness


def make_result(resources=None, allocation_feasible=True, essential_unavailable=None):
    return {
        "resources": (resources or ResourceState()).__dict__.copy(),
        "allocation_feasible": allocation_feasible,
        "essential_unavailable": essential_unavailable or [],
    }


def test_nominal_facility_is_mission_ready():
    report = assess_readiness(make_result())

    assert report["score"] == 100
    assert report["status"] == "Mission ready"
    assert report["recommendations"][0]["priority"] == "Routine"


def test_readiness_score_is_explainable_and_bounded():
    resources = ResourceState(
        available_power_w=60.0,
        battery_percent=50.0,
        available_cpu_percent=40.0,
        sensor_confidence=0.6,
        network_status="degraded",
    )

    report = assess_readiness(make_result(resources))

    assert 0 <= report["score"] <= 100
    assert sum(item["weight"] for item in report["components"]) == 100
    assert sum(item["score"] for item in report["components"]) == report["score"]
    assert report["status"] == "At risk"


def test_low_power_produces_critical_generation_action():
    resources = ResourceState(available_power_w=20.0)

    report = assess_readiness(make_result(resources))

    assert report["status"] == "Critical"
    assert report["recommendations"][0]["priority"] == "Critical"
    assert report["recommendations"][0]["action"] == "Recover generation capacity"


def test_offline_network_produces_local_control_action():
    resources = ResourceState(network_status="offline")

    report = assess_readiness(make_result(resources))
    actions = [item["action"] for item in report["recommendations"]]

    assert "Use local control procedures" in actions


def test_infeasible_essential_allocation_is_highest_priority():
    report = assess_readiness(
        make_result(
            allocation_feasible=False,
            essential_unavailable=["Emergency Communications"],
        )
    )

    assert report["recommendations"][0]["action"] == "Restore essential service"
    assert "Emergency Communications" in report["recommendations"][0]["detail"]