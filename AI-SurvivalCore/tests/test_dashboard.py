from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_dashboard_renders_operations_and_views():
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()

    assert not app.exception
    assert len(app.tabs) == 4
    assert {tab.label for tab in app.tabs} >= {"AI insights"}
    assert {button.key for button in app.button} >= {
        "trigger_storm",
        "recover_facility",
        "reset_facility",
        "run_benchmarks",
    }


def test_dashboard_storm_and_recovery_controls():
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()

    app.button(key="trigger_storm").click().run()
    assert app.session_state["result"]["resources"]["available_power_w"] == 42.0

    app.button(key="recover_facility").click().run()
    assert app.session_state["result"]["resources"]["available_power_w"] == 57.0
    assert app.session_state["result"]["history"][-1]["event"] == "recovery_step"
    assert not app.exception


def test_dashboard_benchmark_persists_results():
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()

    app.button(key="run_benchmarks").click().run()

    assert len(app.session_state["benchmark_results"]) == 5
    assert not app.exception


def test_dashboard_full_lifecycle_demo_recovers_facility():
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()

    app.button(key="run_lifecycle_demo").click().run()

    demo = app.session_state["lifecycle_demo"]
    assert demo["complete"]
    assert demo["impact"]["available_power_w"] == 24.0
    assert demo["final"]["available_power_w"] == 120.0
    assert demo["recovery_steps"] > 0
    assert app.session_state["telemetry"][1]["Event"] == "Combined disaster"
    assert not app.exception


def test_dashboard_guided_recovery_restores_current_facility():
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()

    app.button(key="trigger_storm").click().run()
    app.button(key="run_recovery_protocol").click().run()

    protocol = app.session_state["recovery_protocol"]
    resources = app.session_state["result"]["resources"]
    assert protocol["complete"]
    assert protocol["steps"] > 0
    assert resources["available_power_w"] == 120.0
    assert resources["battery_percent"] == 100.0
    assert not app.exception
