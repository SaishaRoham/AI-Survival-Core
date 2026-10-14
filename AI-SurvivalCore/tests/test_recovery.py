from core.survival_controller import SurvivalController


def test_recovery_increases_power():
    controller = SurvivalController()
    controller.resources.available_power_w = 30.0

    result = controller.recover()

    assert result["resources"]["available_power_w"] == 45.0


def test_recovery_increases_battery():
    controller = SurvivalController()
    controller.resources.battery_percent = 20.0

    result = controller.recover()

    assert result["resources"]["battery_percent"] == 30.0


def test_recovery_records_event():
    controller = SurvivalController()

    result = controller.recover()

    assert result["history"][-1]["event"] == "recovery_step"


def test_recovery_never_exceeds_limits():
    controller = SurvivalController()
    controller.resources.available_power_w = 120.0
    controller.resources.battery_percent = 100.0

    result = controller.recover()

    assert result["resources"]["available_power_w"] <= 120.0
    assert result["resources"]["battery_percent"] <= 100.0
