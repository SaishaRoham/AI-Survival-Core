
from core.facility import create_facility


def test_facility_initial_state():
    resources, functions = create_facility()

    assert resources.available_power_w == 120.0
    assert resources.available_cpu_percent == 100.0
    assert resources.network_status == "online"
    assert len(functions) == 5


def test_essential_functions_exist():
    _, functions = create_facility()

    essential_names = {
        function.name
        for function in functions
        if function.essential
    }

    assert "Environmental Monitoring" in essential_names
    assert "Emergency Communications" in essential_names
    assert "Local Decision Engine" in essential_names


if __name__ == "__main__":
    test_facility_initial_state()
    test_essential_functions_exist()
    print("PASS: Facility model tests completed.")
