
from datetime import datetime
from math import ceil
from typing import Literal

import pandas as pd
import streamlit as st

from core.evaluator import evaluate_all_scenarios
from core.operational_insights import build_operational_insights
from core.readiness_advisor import assess_readiness
from core.survival_controller import SurvivalController


SCENARIOS = {
    "Power surge": "power_surge",
    "Network blackout": "network_blackout",
    "Sensor corruption": "sensor_corruption",
    "CPU degradation": "cpu_degradation",
    "Combined disaster": "combined_disaster",
}

SCENARIO_BRIEFINGS = {
    "Power surge": "Generation drops sharply and the battery absorbs the impact.",
    "Network blackout": "Remote communications are lost; local control remains available.",
    "Sensor corruption": "Telemetry confidence drops and readings need cross-checking.",
    "CPU degradation": "Compute capacity is constrained, so lower-priority work is deferred.",
    "Combined disaster": "A compound failure pressures power, compute, telemetry, and communications.",
}

NOMINAL_POWER_W = 120.0
BadgeColor = Literal[
    "red", "orange", "yellow", "blue", "green", "violet", "gray", "grey", "primary"
]


def record_telemetry(event_name: str) -> None:
    current_result = st.session_state.result
    resources = current_result["resources"]
    snapshots = st.session_state.telemetry
    snapshots.append(
        {
            "Step": len(snapshots),
            "Time": datetime.now().astimezone().strftime("%H:%M:%S"),
            "Event": event_name,
            "Mode": current_result["mode"].replace("_", " ").title(),
            "Available power": round(
                resources["available_power_w"] / NOMINAL_POWER_W * 100, 1
            ),
            "Battery": round(resources["battery_percent"], 1),
            "CPU": round(resources["available_cpu_percent"], 1),
            "Sensor confidence": round(
                resources["sensor_confidence"] * 100, 1
            ),
        }
    )
    st.session_state.telemetry = snapshots[-30:]


def resources_need_recovery(resources: dict) -> bool:
    return any(
        (
            resources["available_power_w"] < NOMINAL_POWER_W,
            resources["battery_percent"] < 100.0,
            resources["available_cpu_percent"] < 100.0,
            resources["sensor_confidence"] < 1.0,
            resources["network_status"] != "online",
        )
    )


def trigger_selected_storm() -> None:
    label = st.session_state.scenario_choice
    st.session_state.result = st.session_state.controller.trigger_storm(
        SCENARIOS[label]
    )
    record_telemetry(label)


def advance_recovery() -> None:
    st.session_state.result = st.session_state.controller.recover()
    record_telemetry("Recovery step")


def estimate_recovery_cycles(resources: dict) -> int:
    """Return the simulated recovery cycles needed to restore nominal capacity."""

    network_cycles = {
        "online": 0,
        "degraded": 1,
        "offline": 2,
    }.get(resources["network_status"], 2)
    required_cycles = (
        ceil(max(0.0, NOMINAL_POWER_W - resources["available_power_w"]) / 15.0),
        ceil(max(0.0, 100.0 - resources["battery_percent"]) / 10.0),
        ceil(max(0.0, 100.0 - resources["available_cpu_percent"]) / 10.0),
        ceil(max(0.0, 1.0 - resources["sensor_confidence"]) / 0.2),
        network_cycles,
    )
    return max(required_cycles)


def run_recovery_protocol() -> None:
    """Apply the simulated recovery cycle until the facility is nominal again."""

    completed_steps = 0
    while (
        resources_need_recovery(st.session_state.result["resources"])
        and completed_steps < 12
    ):
        st.session_state.result = st.session_state.controller.recover()
        completed_steps += 1
        record_telemetry(f"Guided recovery {completed_steps}")

    st.session_state.recovery_protocol = {
        "steps": completed_steps,
        "complete": not resources_need_recovery(
            st.session_state.result["resources"]
        ),
    }


def run_lifecycle_demo() -> None:
    controller = SurvivalController()
    st.session_state.controller = controller
    st.session_state.telemetry = []

    initial_result = controller.evaluate()
    st.session_state.result = initial_result
    record_telemetry("Normal operation")

    impact_result = controller.trigger_storm("combined_disaster")
    st.session_state.result = impact_result
    record_telemetry("Combined disaster")

    recovery_steps = 0
    while (
        resources_need_recovery(st.session_state.result["resources"])
        and recovery_steps < 12
    ):
        st.session_state.result = controller.recover()
        recovery_steps += 1
        record_telemetry(f"Recovery {recovery_steps}")

    st.session_state.lifecycle_demo = {
        "initial": initial_result["resources"],
        "impact": impact_result["resources"],
        "final": st.session_state.result["resources"],
        "recovery_steps": recovery_steps,
        "complete": not resources_need_recovery(
            st.session_state.result["resources"]
        ),
    }
    st.session_state.recovery_protocol = None


def reset_facility() -> None:
    st.session_state.controller = SurvivalController()
    st.session_state.result = st.session_state.controller.evaluate()
    st.session_state.telemetry = []
    st.session_state.benchmark_results = None
    st.session_state.lifecycle_demo = None
    st.session_state.recovery_protocol = None
    record_telemetry("Facility reset")


st.set_page_config(
    page_title="AI Survival Core | Operations",
    page_icon=":material/radar:",
    layout="wide",
)

if "controller" not in st.session_state:
    st.session_state.controller = SurvivalController()
if "result" not in st.session_state:
    st.session_state.result = st.session_state.controller.evaluate()
if "telemetry" not in st.session_state:
    st.session_state.telemetry = []
if not st.session_state.telemetry:
    record_telemetry("Initial state")
if "benchmark_results" not in st.session_state:
    st.session_state.benchmark_results = None
if "lifecycle_demo" not in st.session_state:
    st.session_state.lifecycle_demo = None
if "recovery_protocol" not in st.session_state:
    st.session_state.recovery_protocol = None

result = st.session_state.result
resources = result["resources"]
decisions = result["decisions"]
decision_df = pd.DataFrame(decisions)
mode = result["mode"]
readiness = assess_readiness(result)
operational_insights = build_operational_insights(result, readiness)

mode_colors: dict[str, BadgeColor] = {
    "NORMAL": "green",
    "CONSERVATION": "blue",
    "SURVIVAL": "orange",
    "CRITICAL_SURVIVAL": "red",
}
priority_colors: dict[str, BadgeColor] = {
    "Critical": "red",
    "High": "orange",
    "Medium": "blue",
    "Routine": "green",
}
mode_color = mode_colors.get(mode, "gray")
network_status = resources["network_status"].upper()
network_color: BadgeColor = "green" if network_status == "ONLINE" else "orange"
recovery_needed = resources_need_recovery(resources)
recovery_cycles = estimate_recovery_cycles(resources)
telemetry_rows = st.session_state.telemetry
sparkline_options = {
    "chart_data": (
        [row["Available power"] for row in telemetry_rows]
        if len(telemetry_rows) > 1
        else None
    ),
    "chart_type": "area",
}


with st.sidebar:
    st.title("Mission control", icon=":material/radar:")
    st.caption("AI SURVIVAL CORE / CONTROL PLANE")
    st.badge("SIMULATION LIVE", icon=":material/sensors:", color="blue")

    with st.container(border=True):
        st.subheader("Scenario injection", icon=":material/bolt:")
        st.selectbox(
            "Select a simulated event",
            options=list(SCENARIOS),
            key="scenario_choice",
        )
        st.caption(SCENARIO_BRIEFINGS[st.session_state.scenario_choice])
        st.button(
            "Inject scenario",
            key="trigger_storm",
            type="primary",
            icon=":material/bolt:",
            width="stretch",
            on_click=trigger_selected_storm,
        )

    with st.container(border=True):
        st.subheader("Recovery protocol", icon=":material/settings_backup_restore:")
        st.caption(
            "Nominal capacity is "
            + ("restored." if not recovery_needed else f"about {recovery_cycles} cycle(s) away.")
        )
        st.button(
            "Run one recovery cycle",
            key="recover_facility",
            icon=":material/refresh:",
            width="stretch",
            disabled=not recovery_needed,
            on_click=advance_recovery,
        )
        st.button(
            "Run guided recovery",
            key="run_recovery_protocol",
            type="primary",
            icon=":material/healing:",
            width="stretch",
            disabled=not recovery_needed,
            on_click=run_recovery_protocol,
        )

    st.button(
        "Play full lifecycle demo",
        key="run_lifecycle_demo",
        icon=":material/play_circle:",
        width="stretch",
        on_click=run_lifecycle_demo,
    )

    st.button(
        "Reset facility",
        key="reset_facility",
        icon=":material/restart_alt:",
        width="stretch",
        on_click=reset_facility,
    )
    st.caption("This console changes a simulated facility only.")


st.title("AI Survival Core", icon=":material/radar:")
st.caption("AI resiliency workspace / remote facility simulation")


with st.container(horizontal=True, vertical_alignment="center"):
    st.badge(
        f"{mode.replace('_', ' ')} MODE",
        icon=":material/shield:" if mode == "NORMAL" else ":material/warning:",
        color=mode_color,
    )
    st.badge(
        f"COMMUNICATION {network_status}",
        icon=":material/wifi:",
        color=network_color,
    )
    st.badge(
        "ALLOCATION FEASIBLE"
        if result.get("allocation_feasible", True)
        else "ESSENTIAL LOADS AT RISK",
        icon=(
            ":material/check_circle:"
            if result.get("allocation_feasible", True)
            else ":material/error:"
        ),
        color="green" if result.get("allocation_feasible", True) else "red",
    )

with st.container(border=True):
    posture_column, response_column = st.columns([1.35, 1], vertical_alignment="center")
    with posture_column:
        st.markdown(":material/radar: **Current mission posture**")
        st.write(operational_insights["summary"])
        if recovery_needed:
            st.caption(
                f"Projected simulated return to nominal: {recovery_cycles} recovery cycle(s)."
            )
        else:
            st.caption("Every tracked resource is at nominal simulated capacity.")
    with response_column:
        recommendation = operational_insights["recommendation"]
        st.markdown(":material/priority_high: **Priority response**")
        st.badge(
            recommendation["priority"],
            color=priority_colors[recommendation["priority"]],
        )
        st.write(recommendation["action"])
        st.caption(recommendation["detail"])

with st.container(horizontal=True):
    st.metric(
        "Available power",
        f'{resources["available_power_w"]:.1f} W',
        icon=":material/bolt:",
        border=True,
        **sparkline_options,
    )
    st.metric(
        "Battery reserve",
        f'{resources["battery_percent"]:.0f}%',
        icon=":material/battery_charging_full:",
        border=True,
        chart_data=(
            [row["Battery"] for row in telemetry_rows]
            if len(telemetry_rows) > 1
            else None
        ),
        chart_type="line",
    )
    st.metric(
        "CPU capacity",
        f'{resources["available_cpu_percent"]:.0f}%',
        icon=":material/memory:",
        border=True,
        chart_data=(
            [row["CPU"] for row in telemetry_rows]
            if len(telemetry_rows) > 1
            else None
        ),
        chart_type="line",
    )
    st.metric(
        "Sensor confidence",
        f'{resources["sensor_confidence"]:.2f}',
        icon=":material/sensors:",
        border=True,
        chart_data=(
            [row["Sensor confidence"] for row in telemetry_rows]
            if len(telemetry_rows) > 1
            else None
        ),
        chart_type="line",
    )

operations_tab, insights_tab, timeline_tab, scenario_tab = st.tabs(
    ["Operations", "AI insights", "Recovery timeline", "Scenario lab"]
)

with operations_tab:
    if mode == "CRITICAL_SURVIVAL":
        st.error(
            "Critical survival mode. Nonessential loads may be offline.",
            icon=":material/emergency:",
        )
    elif mode == "SURVIVAL":
        st.warning(
            "Survival mode. Facility resources are constrained.",
            icon=":material/warning:",
        )
    elif mode == "CONSERVATION":
        st.info(
            "Conservation mode. The allocator is protecting reserve capacity.",
            icon=":material/energy_savings_leaf:",
        )
    else:
        st.success(
            "Normal operations. All systems are within nominal limits.",
            icon=":material/check_circle:",
        )

    service_counts = decision_df["status"].value_counts()
    service_columns = st.columns(3)
    service_columns[0].metric(
        "Active services",
        int(service_counts.get("ACTIVE", 0)),
        f"of {len(decision_df)} functions",
        icon=":material/check_circle:",
        border=True,
    )
    service_columns[1].metric(
        "Degraded services",
        int(service_counts.get("DEGRADED", 0)),
        "Reduced capacity",
        icon=":material/trending_down:",
        delta_color="inverse",
        border=True,
    )
    service_columns[2].metric(
        "Standby services",
        int(service_counts.get("STANDBY", 0)),
        "Shed or unavailable",
        icon=":material/pause_circle:",
        delta_color="inverse",
        border=True,
    )

    with st.container(border=True):
        readiness_column, actions_column = st.columns([1, 2])
        with readiness_column:
            st.subheader("Readiness assessment", icon=":material/verified:")
            st.metric(
                "Facility readiness",
                f'{readiness["score"]}/100',
                readiness["status"],
                border=True,
            )
            st.progress(readiness["score"], text=readiness["status"])
            with st.expander("Score components"):
                st.dataframe(
                    pd.DataFrame(readiness["components"]),
                    hide_index=True,
                    column_config={
                        "component": st.column_config.TextColumn("Component"),
                        "score": st.column_config.NumberColumn("Points", format="%.1f"),
                        "weight": st.column_config.NumberColumn("Weight", format="%d"),
                    },
                    alt="Weighted components contributing to the facility readiness score",
                )
        with actions_column:
            st.subheader("Recommended next actions", icon=":material/checklist:")
            for recommendation in readiness["recommendations"]:
                priority_color = priority_colors[recommendation["priority"]]
                st.badge(
                    recommendation["priority"],
                    color=priority_color,
                )
                st.markdown(f'**{recommendation["action"]}**')
                st.caption(recommendation["detail"])

    metric_columns = st.columns(3)
    metric_columns[0].metric(
        "Power allocated",
        f'{result["total_allocated_power_w"]:.1f} W',
        border=True,
    )
    metric_columns[1].metric(
        "Power remaining",
        f'{result["remaining_power_w"]:.1f} W',
        border=True,
    )
    metric_columns[2].metric(
        "CPU remaining",
        f'{result["remaining_cpu_percent"]:.1f}%',
        border=True,
    )

    if not result.get("allocation_feasible", True):
        unavailable = result.get("essential_unavailable", [])
        st.error(
            "Essential functions without an allocation: "
            f'{", ".join(unavailable)}'
        )

    with st.container(border=True):
        st.subheader("Function allocation", icon=":material/account_tree:")
        st.dataframe(
            decision_df.drop(columns=["reason"]),
            hide_index=True,
            column_config={
                "name": st.column_config.TextColumn("Function", width="medium"),
                "status": st.column_config.TextColumn("State", width="small"),
                "allocated_power_w": st.column_config.NumberColumn(
                    "Power", format="%.1f W", width="small"
                ),
                "allocated_cpu_percent": st.column_config.NumberColumn(
                    "CPU", format="%.1f%%", width="small"
                ),
            },
            alt="Current AI resource allocation by facility function",
        )

    chart_column, reliability_column = st.columns([1.5, 1])
    with chart_column:
        with st.container(border=True):
            st.subheader("Power by function", icon=":material/bar_chart:")
            st.bar_chart(
                decision_df,
                x="name",
                y="allocated_power_w",
                x_label="Facility function",
                y_label="Allocated power (W)",
                alt="Power allocation for each facility function",
            )
    with reliability_column:
        with st.container(border=True):
            st.subheader("Sensor reliability", icon=":material/sensors:")
            sensor_results = result.get("sensor_results", {})
            if not sensor_results:
                st.caption("No sensor checks recorded.")
            else:
                for sensor_name, sensor in sensor_results.items():
                    color = "green" if sensor["trusted"] else "red"
                    icon = ":material/check_circle:" if sensor["trusted"] else ":material/error:"
                    st.badge(
                        f'{sensor_name}: {"trusted" if sensor["trusted"] else "untrusted"}',
                        color=color,
                        icon=icon,
                    )
                    st.caption(sensor["reason"])

    with st.expander("Decision rationale", icon=":material/psychology:"):
        for decision in decisions:
            st.markdown(
                f'**{decision["name"]} · {decision["status"]}**  '
                f'\n{decision["reason"]}'
            )

with insights_tab:
    st.subheader("AI operational insights", icon=":material/psychology:")
    st.caption(
        "Transparent, rule-based analysis of this simulation. It is not connected "
        "to real equipment or an external AI service."
    )

    risk_colors: dict[str, BadgeColor] = {
        "Low": "green",
        "Elevated": "blue",
        "High": "orange",
        "Critical": "red",
    }
    with st.container(horizontal=True, vertical_alignment="center"):
        st.badge(
            f'{operational_insights["risk_level"].upper()} RISK',
            color=risk_colors[operational_insights["risk_level"]],
        )
        st.write(operational_insights["summary"])

    with st.container(horizontal=True):
        st.metric(
            "Readiness",
            f'{readiness["score"]}/100',
            readiness["status"],
            border=True,
        )
        st.metric(
            "Active functions",
            operational_insights["active_count"],
            border=True,
        )
        st.metric(
            "Degraded / standby",
            f'{operational_insights["degraded_count"]} / '
            f'{operational_insights["standby_count"]}',
            border=True,
        )
        st.metric(
            "Power allocated",
            f'{result["total_allocated_power_w"]:.1f} W',
            f'{operational_insights["power_utilization_percent"]:.1f}% of available',
            border=True,
        )

    signal_column, recommendation_column = st.columns(2)
    with signal_column:
        st.subheader("Risk signals", icon=":material/notification_important:")
        if operational_insights["risk_signals"]:
            st.dataframe(
                pd.DataFrame(operational_insights["risk_signals"]),
                hide_index=True,
                alt="Resource and service conditions driving the operational risk assessment",
            )
        else:
            st.success(
                "No configured risk thresholds are currently breached.",
                icon=":material/check_circle:",
            )
    with recommendation_column:
        st.subheader("Recommended next action", icon=":material/assistant:")
        recommendation = operational_insights["recommendation"]
        st.badge(
            recommendation["priority"],
            color=priority_colors[recommendation["priority"]],
        )
        st.markdown(f'**{recommendation["action"]}**')
        st.write(recommendation["detail"])

    st.subheader("Automatic simulated power allocation", icon=":material/auto_awesome:")
    st.caption(
        "Each storm event runs the essential-first allocator automatically. "
        "These are simulated allocations, not commands to emergency equipment."
    )
    st.dataframe(
        decision_df[
            ["name", "status", "allocated_power_w", "allocated_cpu_percent", "reason"]
        ],
        hide_index=True,
        column_config={
            "name": st.column_config.TextColumn("Function"),
            "status": st.column_config.TextColumn("State"),
            "allocated_power_w": st.column_config.NumberColumn("Power", format="%.1f W"),
            "allocated_cpu_percent": st.column_config.NumberColumn("CPU", format="%.1f%%"),
            "reason": st.column_config.TextColumn("Allocation rationale"),
        },
        alt="Automatic simulated power and CPU allocation with rationale by function",
    )

with timeline_tab:
    st.subheader("Resource recovery", icon=":material/settings_backup_restore:")
    st.caption(
        "Every simulated intervention is captured below so operators can review the facility's recovery path."
    )
    lifecycle_demo = st.session_state.lifecycle_demo
    if lifecycle_demo:
        phase_columns = st.columns(3)
        phase_columns[0].metric(
            "Before storm",
            f'{lifecycle_demo["initial"]["available_power_w"]:.0f} W',
            delta=f'{lifecycle_demo["initial"]["battery_percent"]:.0f}% battery',
            border=True,
        )
        phase_columns[1].metric(
            "Storm impact",
            f'{lifecycle_demo["impact"]["available_power_w"]:.0f} W',
            delta=f'{lifecycle_demo["impact"]["battery_percent"]:.0f}% battery',
            delta_color="inverse",
            border=True,
        )
        phase_columns[2].metric(
            "After recovery",
            f'{lifecycle_demo["final"]["available_power_w"]:.0f} W',
            delta=f'{lifecycle_demo["recovery_steps"]} recovery steps',
            border=True,
        )
        st.badge(
            "LIFECYCLE COMPLETE"
            if lifecycle_demo["complete"]
            else "RECOVERY IN PROGRESS",
            color="green" if lifecycle_demo["complete"] else "orange",
            icon=(
                ":material/check_circle:"
                if lifecycle_demo["complete"]
                else ":material/pending:"
            ),
        )

    recovery_protocol = st.session_state.recovery_protocol
    if recovery_protocol:
        if recovery_protocol["complete"]:
            st.success(
                f'Guided recovery restored nominal capacity in {recovery_protocol["steps"]} cycle(s).',
                icon=":material/check_circle:",
            )
        else:
            st.warning(
                "Guided recovery reached its simulation limit before nominal capacity was restored.",
                icon=":material/pending:",
            )

    telemetry_df = pd.DataFrame(st.session_state.telemetry)
    chart_columns = ["Available power", "Battery", "CPU", "Sensor confidence"]
    if len(telemetry_df) > 1:
        st.line_chart(
            telemetry_df,
            x="Step",
            y=chart_columns,
            y_label="Available capacity (%)",
            alt="Facility power, battery, CPU, and sensor confidence through storm and recovery steps",
        )
    else:
        st.info("Resource trends will appear after the first facility event.")
    st.dataframe(
        telemetry_df.sort_values("Step", ascending=False),
        hide_index=True,
        column_config={
            "Step": st.column_config.NumberColumn("Step", format="%d"),
            "Time": st.column_config.TextColumn("Recorded at"),
            "Event": st.column_config.TextColumn("Event"),
            "Mode": st.column_config.TextColumn("Operating mode"),
            "Available power": st.column_config.NumberColumn(
                "Power available (%)", format="%.1f%%"
            ),
            "Battery": st.column_config.NumberColumn("Battery (%)", format="%.1f%%"),
            "CPU": st.column_config.NumberColumn("CPU (%)", format="%.1f%%"),
            "Sensor confidence": st.column_config.NumberColumn(
                "Sensor confidence (%)", format="%.1f%%"
            ),
        },
        alt="Resource snapshots recorded after each event and recovery step",
    )
    st.download_button(
        "Download recovery timeline",
        data=telemetry_df.to_csv(index=False),
        file_name="ai-survival-core-recovery-timeline.csv",
        mime="text/csv",
        icon=":material/download:",
        key="download_timeline",
    )

    event_history = result.get("history", [])
    if event_history:
        st.subheader("Incident log", icon=":material/history:")
        st.dataframe(
            pd.DataFrame(event_history).iloc[::-1],
            hide_index=True,
            alt="Storm and recovery events for the current facility session",
        )

with scenario_tab:
    st.subheader("Scenario benchmark", icon=":material/science:")
    control_column, note_column = st.columns([1, 2], vertical_alignment="center")
    with control_column:
        run_benchmarks = st.button(
            "Run all scenarios",
            type="primary",
            icon=":material/science:",
            key="run_benchmarks",
            width="stretch",
        )
    with note_column:
        st.caption(
            "Each scenario runs against a fresh facility. Results are simulated, "
            "not real-world performance measurements."
        )

    if run_benchmarks:
        st.session_state.benchmark_results = evaluate_all_scenarios()

    benchmark_results = st.session_state.benchmark_results
    if benchmark_results:
        benchmark_df = pd.DataFrame(benchmark_results)
        available_modes = sorted(benchmark_df["mode"].unique())
        selected_modes = st.pills(
            "Filter operating modes",
            options=available_modes,
            default=available_modes,
            key="benchmark_modes",
            selection_mode="multi",
        )
        visible_results = benchmark_df[
            benchmark_df["mode"].isin(selected_modes)
        ]

        if visible_results.empty:
            st.info("Select at least one operating mode to inspect its simulated scenarios.")
        else:
            lowest_readiness = visible_results.loc[
                visible_results["readiness_score"].idxmin()
            ]
            fully_protected = int(
                visible_results["essential_allocation_feasible"].sum()
            )
            benchmark_metrics = st.columns(3)
            benchmark_metrics[0].metric(
                "Lowest readiness",
                f'{lowest_readiness["readiness_score"]}/100',
                lowest_readiness["scenario"].replace("_", " ").title(),
                delta_color="inverse",
                border=True,
            )
            benchmark_metrics[1].metric(
                "Essential protection",
                f"{fully_protected}/{len(visible_results)}",
                "Scenarios with every essential function allocated",
                border=True,
            )
            benchmark_metrics[2].metric(
                "Average readiness",
                f'{visible_results["readiness_score"].mean():.0f}/100',
                "Across visible simulations",
                border=True,
            )

            left_column, right_column = st.columns([1.3, 1])
            with left_column:
                st.dataframe(
                    visible_results,
                    hide_index=True,
                    column_config={
                        "scenario": st.column_config.TextColumn("Scenario"),
                        "mode": st.column_config.TextColumn("Mode"),
                        "readiness_score": st.column_config.NumberColumn(
                            "Readiness", format="%d/100"
                        ),
                        "available_power_w": st.column_config.NumberColumn(
                            "Available power", format="%.1f W"
                        ),
                        "allocated_power_w": st.column_config.NumberColumn(
                            "Allocated power", format="%.1f W"
                        ),
                        "remaining_power_w": st.column_config.NumberColumn(
                            "Power remaining", format="%.1f W"
                        ),
                        "cpu_used_percent": st.column_config.NumberColumn(
                            "CPU used", format="%.1f%%"
                        ),
                    },
                    alt="Resource allocation results for simulated storm scenarios",
                )
            with right_column:
                st.bar_chart(
                    visible_results,
                    x="scenario",
                    y=["available_power_w", "allocated_power_w"],
                    y_label="Power (W)",
                    alt="Available and allocated power across selected storm scenarios",
                )

            inspected_scenario = st.selectbox(
                "Inspect a scenario",
                options=visible_results["scenario"].tolist(),
                format_func=lambda value: value.replace("_", " ").title(),
                key="inspected_scenario",
            )
            scenario_label = next(
                label for label, code in SCENARIOS.items() if code == inspected_scenario
            )
            scenario_result = visible_results.loc[
                visible_results["scenario"] == inspected_scenario
            ].iloc[0]
            with st.container(border=True):
                st.markdown(f"**{scenario_label} briefing**")
                st.badge(
                    scenario_result["mode"].replace("_", " ") + " MODE",
                    color=mode_colors.get(scenario_result["mode"], "gray"),
                )
                st.write(SCENARIO_BRIEFINGS[scenario_label])
                st.caption(
                    f'{scenario_result["essential_functions_running"]}/'
                    f'{scenario_result["essential_functions_total"]} essential functions '
                    "receive a simulated allocation."
                )

            st.download_button(
                "Download scenario report",
                data=visible_results.to_csv(index=False),
                file_name="ai-survival-core-scenario-report.csv",
                mime="text/csv",
                icon=":material/download:",
                key="download_scenario_report",
            )
    else:
        st.info("Run the benchmark to compare the facility across storm scenarios.")

st.caption(
    "Research simulation only · Not a certified safety-control system · "
    "All facility readings are simulated"
)
