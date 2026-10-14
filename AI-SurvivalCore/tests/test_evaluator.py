
from core.evaluator import evaluate_scenario, evaluate_all_scenarios


def test_power_budget_is_respected():
    result = evaluate_scenario("power_surge")

    assert result["allocated_power_w"] <= result["available_power_w"]


def test_cpu_budget_is_respected():
    result = evaluate_scenario("combined_disaster")

    assert 0 <= result["cpu_used_percent"] <= 25.0


def test_scenario_count():
    results = evaluate_all_scenarios()

    assert len(results) == 5
    assert all(0 <= result["readiness_score"] <= 100 for result in results)


def test_essential_function_count():
    result = evaluate_scenario("power_surge")

    assert result["essential_functions_total"] == 3
    assert (
        0 <= result["essential_functions_running"]
        <= result["essential_functions_total"]
    )


def test_invalid_scenario_is_rejected():
    try:
        evaluate_scenario("unknown_scenario")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


if __name__ == "__main__":
    test_power_budget_is_respected()
    test_cpu_budget_is_respected()
    test_scenario_count()
    test_essential_function_count()
    test_invalid_scenario_is_rejected()

    print("PASS: All evaluator tests completed.")
