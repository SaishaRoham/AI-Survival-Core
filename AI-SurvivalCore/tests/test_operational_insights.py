from core.operational_insights import build_operational_insights
from core.readiness_advisor import assess_readiness
from core.survival_controller import SurvivalController


def test_normal_operations_have_no_risk_signals():
    result = SurvivalController().evaluate()
    readiness = assess_readiness(result)

    insights = build_operational_insights(result, readiness)

    assert insights["risk_level"] == "Low"
    assert insights["risk_signals"] == []
    assert insights["active_count"] == len(result["decisions"])
    assert insights["standby_count"] == 0


def test_combined_disaster_explains_essential_allocation_risk():
    controller = SurvivalController()
    result = controller.trigger_storm("combined_disaster")
    readiness = assess_readiness(result)

    insights = build_operational_insights(result, readiness)

    assert insights["risk_level"] == "Critical"
    assert insights["essential_unavailable"] == result["essential_unavailable"]
    assert insights["standby_count"] > 0
    assert insights["risk_signals"][0]["Signal"] == "Essential allocation"
    assert insights["recommendation"]["priority"] == "Critical"