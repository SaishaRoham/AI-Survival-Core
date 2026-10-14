
from core.survival_controller import SurvivalController


def test_controller_starts_in_normal_mode():
    controller = SurvivalController()
    result = controller.evaluate()

    assert result["mode"] == "NORMAL"
    assert len(result["decisions"]) == 5


def test_controller_handles_power_surge():
    controller = SurvivalController()
    result = controller.trigger_storm("power_surge")

    assert result["resources"]["available_power_w"] == 42.0
    assert result["mode"] == "CONSERVATION"


def test_controller_handles_network_blackout():
    controller = SurvivalController()
    result = controller.trigger_storm("network_blackout")

    assert result["resources"]["network_status"] == "offline"
    assert result["mode"] == "SURVIVAL"


def test_controller_handles_combined_disaster():
    controller = SurvivalController()
    result = controller.trigger_storm("combined_disaster")

    assert result["mode"] == "CRITICAL_SURVIVAL"
    assert result["resources"]["network_status"] == "offline"
    assert len(result["history"]) == 1


def test_controller_recovers_gradually_after_storm():
    controller = SurvivalController()
    controller.trigger_storm("power_surge")

    result = controller.recover()

    assert result["resources"]["available_power_w"] == 57.0
    assert result["resources"]["battery_percent"] == 85.0
    assert result["history"][-1]["event"] == "recovery_step"


def test_unknown_event_is_rejected():
    controller = SurvivalController()

    try:
        controller.trigger_storm("unknown_event")
    except ValueError:
        pass
    else:
        raise AssertionError("Unknown event should raise ValueError")


if __name__ == "__main__":
    test_controller_starts_in_normal_mode()
    test_controller_handles_power_surge()
    test_controller_handles_network_blackout()
    test_controller_handles_combined_disaster()
    test_controller_recovers_gradually_after_storm()
    test_unknown_event_is_rejected()

    print("PASS: Survival controller tests completed.")
