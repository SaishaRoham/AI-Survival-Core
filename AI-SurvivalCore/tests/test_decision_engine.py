
from core.facility import create_facility
from core.decision_engine import allocate_resources, choose_operating_mode


def test_normal_mode():
    resources, _ = create_facility()
    assert choose_operating_mode(resources) == "NORMAL"


def test_critical_survival_mode():
    resources, _ = create_facility()
    resources.battery_percent = 10

    assert choose_operating_mode(resources) == "CRITICAL_SURVIVAL"


def test_network_failure_changes_mode():
    resources, _ = create_facility()
    resources.network_status = "offline"

    assert choose_operating_mode(resources) == "SURVIVAL"


def test_allocation_respects_power_budget():
    resources, functions = create_facility()
    resources.available_power_w = 45

    result = allocate_resources(resources, functions)

    total_allocated = sum(
        decision.allocated_power_w
        for decision in result["decisions"]
    )

    assert total_allocated <= resources.available_power_w


def test_dependencies_are_respected():
    resources, functions = create_facility()

    # Environmental monitoring cannot operate at its minimum.
    resources.available_power_w = 5

    result = allocate_resources(resources, functions)

    decisions = {
        decision.name: decision.status
        for decision in result["decisions"]
    }

    assert decisions["Environmental Monitoring"] == "STANDBY"
    assert decisions["Emergency Communications"] == "STANDBY"


if __name__ == "__main__":
    print("Running decision engine tests...")
    test_normal_mode()
    test_critical_survival_mode()
    test_network_failure_changes_mode()
    test_allocation_respects_power_budget()
    test_dependencies_are_respected()
    print("PASS: All decision engine tests completed.")
