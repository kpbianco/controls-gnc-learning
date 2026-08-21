from __future__ import annotations

import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
QUESTION = (
    "What inputs, observable effects, and failure modes matter when you close "
    "the Loop Through a Hardware-in-the-Loop Plant?"
)
LATENCY_VALUES_SEC = [0.01, 0.02, 0.04, 0.06, 0.08]
PERIOD_VALUES_SEC = [0.02, 0.04, 0.05, 0.1, 0.2]


def reference_run(
    controller_period: float = 0.05,
    latency: float = 0.01,
    watchdog_timeout: float = 0.2,
    drop_every: int = 0,
    cancel_at: float = math.inf,
    mass: float = 1.5,
    time_step: float = 0.01,
    duration: float = 8,
    enforce_response_bound: bool = True,
) -> dict[str, object]:
    duration_ticks = round(duration / time_step)
    controller_ticks = round(controller_period / time_step)
    latency_ticks = round(latency / time_step)
    watchdog_ticks = round(watchdog_timeout / time_step)
    cancellation_tick = math.inf if math.isinf(cancel_at) else round(cancel_at / time_step)
    count = duration_ticks + 1
    time = [index * time_step for index in range(count)]
    reference = [1.0 if index < duration_ticks / 2 else -0.5 for index in range(count)]
    position = [0.0] * count
    velocity = [0.0] * count
    controller_force = [0.0] * count
    applied_force = [0.0] * count
    measured_position = [math.nan] * count
    measured_velocity = [math.nan] * count
    measurement_timestamp = [math.nan] * count
    measurement_age = [math.nan] * count
    command_source_timestamp = [math.nan] * count
    command_source_age = [math.nan] * count
    command_arrival_age = [math.nan] * count
    controller_event = [False] * count
    measurement_delivered = [False] * count
    command_sent = [False] * count
    command_dropped = [False] * count
    command_delivered = [False] * count
    startup_safe = [False] * count
    watchdog_timed_out = [False] * count
    safe_zero = [False] * count
    cancelled = [False] * count

    sensor_queue: list[tuple[float, float, float] | None] = [None] * count
    command_queue: list[tuple[float, float] | None] = [None] * count
    has_measurement = False
    has_command = False
    latest_measured_position = 0.0
    latest_measured_velocity = 0.0
    latest_measurement_timestamp = 0.0
    latest_controller_force = 0.0
    latest_delivered_force = 0.0
    latest_command_delivery_tick = 0
    latest_command_source_timestamp = 0.0
    command_sequence = 0
    sensor_packet_count = 0

    damping = 1.2
    position_gain = 18.0
    velocity_gain = 8.0
    force_limit = 30.0
    decay = math.exp(-damping * time_step / mass)
    velocity_from_force = (1 - decay) / damping
    position_from_velocity = mass / damping * (1 - decay)
    position_from_force = time_step / damping - mass / damping**2 * (1 - decay)

    for index in range(count):
        is_cancelled = index >= cancellation_tick
        cancelled[index] = is_cancelled
        if not is_cancelled:
            if index % controller_ticks == 0:
                controller_event[index] = True
                sensor_packet_count += 1
                due = index + latency_ticks
                if due < count:
                    sensor_queue[due] = (position[index], velocity[index], time[index])

            packet = sensor_queue[index]
            if packet is not None:
                has_measurement = True
                (
                    latest_measured_position,
                    latest_measured_velocity,
                    latest_measurement_timestamp,
                ) = packet
                measurement_delivered[index] = True

            if index % controller_ticks == 0 and has_measurement:
                raw_force = (
                    position_gain * (reference[index] - latest_measured_position)
                    - velocity_gain * latest_measured_velocity
                )
                latest_controller_force = min(max(raw_force, -force_limit), force_limit)
                command_sequence += 1
                command_sent[index] = True
                should_drop = drop_every > 0 and command_sequence % drop_every == 0
                command_dropped[index] = should_drop
                if not should_drop:
                    due = index + latency_ticks
                    if due < count:
                        command_queue[due] = (latest_controller_force, time[index])

            packet = command_queue[index]
            if packet is not None:
                has_command = True
                latest_delivered_force, latest_command_source_timestamp = packet
                latest_command_delivery_tick = index
                command_delivered[index] = True

        controller_force[index] = latest_controller_force
        if has_measurement and not is_cancelled:
            measured_position[index] = latest_measured_position
            measured_velocity[index] = latest_measured_velocity
            measurement_timestamp[index] = latest_measurement_timestamp
            measurement_age[index] = time[index] - latest_measurement_timestamp
        if has_command and not is_cancelled:
            command_source_timestamp[index] = latest_command_source_timestamp
            command_source_age[index] = time[index] - latest_command_source_timestamp
            command_arrival_age[index] = (index - latest_command_delivery_tick) * time_step

        startup_safe[index] = not is_cancelled and not has_command
        watchdog_timed_out[index] = (
            not is_cancelled
            and has_command
            and index - latest_command_delivery_tick >= watchdog_ticks
        )
        safe_zero[index] = is_cancelled or startup_safe[index] or watchdog_timed_out[index]
        applied_force[index] = 0.0 if safe_zero[index] else latest_delivered_force

        if index < count - 1:
            velocity[index + 1] = (
                decay * velocity[index] + velocity_from_force * applied_force[index]
            )
            position[index + 1] = (
                position[index]
                + position_from_velocity * velocity[index]
                + position_from_force * applied_force[index]
            )
            if enforce_response_bound and (
                not math.isfinite(position[index + 1])
                or not math.isfinite(velocity[index + 1])
                or abs(position[index + 1]) > 10
                or abs(velocity[index + 1]) > 30
            ):
                raise ValueError("P24:ResponseBound")

    tracking_error = [target - actual for target, actual in zip(reference, position)]
    finite_measurement_ages = [value for value in measurement_age if math.isfinite(value)]
    return {
        "time": time,
        "reference": reference,
        "position": position,
        "velocity": velocity,
        "controller_force": controller_force,
        "applied_force": applied_force,
        "measured_position": measured_position,
        "measured_velocity": measured_velocity,
        "measurement_timestamp": measurement_timestamp,
        "measurement_age": measurement_age,
        "command_source_timestamp": command_source_timestamp,
        "command_source_age": command_source_age,
        "command_arrival_age": command_arrival_age,
        "controller_event": controller_event,
        "measurement_delivered": measurement_delivered,
        "command_sent": command_sent,
        "command_dropped": command_dropped,
        "command_delivered": command_delivered,
        "startup_safe": startup_safe,
        "watchdog_timed_out": watchdog_timed_out,
        "safe_zero": safe_zero,
        "cancelled": cancelled,
        "tracking_error": tracking_error,
        "tracking_rms": math.sqrt(sum(value**2 for value in tracking_error) / count),
        "integrated_absolute_error": sum(abs(value) for value in tracking_error[:-1])
        * time_step,
        "maximum_measurement_age": (
            max(finite_measurement_ages) if finite_measurement_ages else math.nan
        ),
        "startup_safe_duration": sum(startup_safe[:-1]) * time_step,
        "watchdog_duration": sum(watchdog_timed_out[:-1]) * time_step,
        "safe_zero_duration": sum(safe_zero[:-1]) * time_step,
        "cancellation_duration": sum(cancelled[:-1]) * time_step,
        "peak_position": max(abs(value) for value in position),
        "peak_velocity": max(abs(value) for value in velocity),
        "peak_controller_force": max(abs(value) for value in controller_force),
        "peak_applied_force": max(abs(value) for value in applied_force),
        "sensor_packet_count": sensor_packet_count,
        "measurement_delivery_count": sum(measurement_delivered),
        "command_sent_count": sum(command_sent),
        "command_drop_count": sum(command_dropped),
        "command_delivery_count": sum(command_delivered),
        "allocated_count": count,
        "controller_ticks": controller_ticks,
        "latency_ticks": latency_ticks,
        "watchdog_ticks": watchdog_ticks,
        "decay": decay,
        "velocity_from_force": velocity_from_force,
        "position_from_velocity": position_from_velocity,
        "position_from_force": position_from_force,
    }


class P24ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P24"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(
            {
                "number": self.module["number"],
                "id": self.module["id"],
                "title": self.module["title"],
                "guiding_question": self.module["guiding_question"],
                "phase": self.module["phase"],
                "phase_title": self.module["phase_title"],
                "slug": self.module["slug"],
                "folder": self.module["folder"],
                "status": self.module["status"],
                "implementation_batch": self.module["implementation_batch"],
                "prerequisites": self.module["prerequisites"],
                "evidence_level": self.module["evidence_level"],
            },
            {
                "number": 24,
                "id": "P24",
                "title": "Close the Loop Through a Hardware-in-the-Loop Plant",
                "guiding_question": QUESTION,
                "phase": 6,
                "phase_title": "Guidance and HIL",
                "slug": "close-the-loop-through-a-hardware-in-the-loop-plant",
                "folder": "modules/24-close-the-loop-through-a-hardware-in-the-loop-plant",
                "status": "implemented",
                "implementation_batch": "P24",
                "prerequisites": ["P23"],
                "evidence_level": "simulated",
            },
        )
        prerequisite = next(
            module for module in self.manifest["modules"] if module["id"] == "P23"
        )
        self.assertEqual(prerequisite["status"], "implemented")

    def test_complete_artifact_set_and_clean_eof(self):
        required = (
            "README.md",
            "lesson.m",
            "model.m",
            "experiment.m",
            "interactive.m",
            "lesson.md",
            "walkthrough.md",
            "checks.md",
            "run_checks.m",
        )
        for name in required:
            with self.subTest(name=name):
                path = self.folder / name
                self.assertTrue(path.is_file(), name)
                content = path.read_bytes()
                self.assertTrue(content.endswith(b"\n"), name)
                self.assertFalse(content.endswith(b"\n\n"), name)

    def test_model_is_transparent_deterministic_timestamped_and_bounded(self):
        model_source = self.read("model.m")
        for marker in (
            "velocityDecay = exp(-plantDampingNPerMPerSec*timeStepSec/plantMassKg)",
            "velocityFromForce = (1-velocityDecay)/plantDampingNPerMPerSec",
            "positionFromVelocity = plantMassKg/plantDampingNPerMPerSec* ...",
            "positionFromForce = timeStepSec/plantDampingNPerMPerSec- ...",
            "sensorPacketTimestampSec",
            "commandPacketTimestampSec",
            "lastMeasurementTimestampSec",
            "lastCommandSourceTimestampSec",
            "commandSourceAgeSec",
            "commandAgeSec",
            "startupSafeActive",
            "watchdogTimedOut",
            "safeZeroActive",
            "cancellationTick",
            "sensorPacketQueued(k:end) = false",
            "commandPacketQueued(k:end) = false",
            "maximumStepCount = 4001",
            "P24:ControllerPeriodRange",
            "P24:LatencyRange",
            "P24:WatchdogRange",
            "P24:DropScheduleRange",
            "P24:CancellationRange",
            "P24:PlantMassRange",
            "P24:TimeStepRange",
            "P24:DurationRange",
            "P24:ControllerGridMismatch",
            "P24:LatencyGridMismatch",
            "P24:WatchdogGridMismatch",
            "P24:CancellationGridMismatch",
            "P24:ReferenceGridMismatch",
            "P24:StepCountRange",
            "P24:ResponseBound",
        ):
            self.assertIn(marker, model_source)
        self.assertLess(
            model_source.index("allocatedStepCount > maximumStepCount"),
            model_source.index("timeSec = (0:durationTickCount)*timeStepSec"),
        )
        self.assertLess(
            model_source.index("if isCancelled"),
            model_source.index("if sensorPacketQueued(k)"),
        )
        self.assertNotRegex(
            model_source.lower(),
            r"\b(?:plot|figure|uifigure|uiaxes|uislider|uidropdown|rng|rand|randn|"
            r"global|persistent|fopen|webread|webwrite|system|tcpclient|udpport|"
            r"serialport|timer|parfor)\s*\(?",
        )

    def test_independent_baseline_exact_plant_and_metrics(self):
        baseline_a = reference_run()
        baseline_b = reference_run()
        self.assertEqual(baseline_a, baseline_b)
        self.assertAlmostEqual(baseline_a["tracking_rms"], 0.35217805690329707)
        self.assertAlmostEqual(
            baseline_a["integrated_absolute_error"], 1.1527771702125116
        )
        self.assertAlmostEqual(baseline_a["maximum_measurement_age"], 0.05)
        self.assertAlmostEqual(baseline_a["peak_position"], 0.9999993310787705)
        self.assertLess(baseline_a["peak_velocity"], 2.8)
        self.assertEqual(baseline_a["startup_safe_duration"], 0.06)
        self.assertEqual(baseline_a["watchdog_duration"], 0)
        self.assertEqual(baseline_a["safe_zero_duration"], 0.06)
        self.assertEqual(baseline_a["cancellation_duration"], 0)
        for index in range(len(baseline_a["time"]) - 1):
            expected_velocity = (
                baseline_a["decay"] * baseline_a["velocity"][index]
                + baseline_a["velocity_from_force"]
                * baseline_a["applied_force"][index]
            )
            expected_position = (
                baseline_a["position"][index]
                + baseline_a["position_from_velocity"]
                * baseline_a["velocity"][index]
                + baseline_a["position_from_force"]
                * baseline_a["applied_force"][index]
            )
            self.assertAlmostEqual(baseline_a["velocity"][index + 1], expected_velocity)
            self.assertAlmostEqual(baseline_a["position"][index + 1], expected_position)

    def test_packet_schedule_timestamps_ages_and_zero_latency_limit(self):
        baseline = reference_run()
        self.assertEqual(baseline["sensor_packet_count"], 161)
        self.assertEqual(baseline["measurement_delivery_count"], 160)
        self.assertEqual(baseline["command_sent_count"], 160)
        self.assertEqual(baseline["command_drop_count"], 0)
        self.assertEqual(baseline["command_delivery_count"], 159)
        first_delivery = baseline["command_delivered"].index(True)
        self.assertAlmostEqual(baseline["time"][first_delivery], 0.06)
        self.assertAlmostEqual(baseline["applied_force"][first_delivery], 18)
        self.assertAlmostEqual(baseline["measurement_timestamp"][first_delivery], 0.05)
        self.assertAlmostEqual(baseline["measurement_age"][first_delivery], 0.01)
        self.assertAlmostEqual(baseline["command_source_timestamp"][first_delivery], 0.05)
        self.assertAlmostEqual(baseline["command_source_age"][first_delivery], 0.01)
        self.assertEqual(baseline["command_arrival_age"][first_delivery], 0)

        zero_latency = reference_run(latency=0)
        self.assertEqual(zero_latency["sensor_packet_count"], 161)
        self.assertEqual(zero_latency["measurement_delivery_count"], 161)
        self.assertEqual(zero_latency["command_sent_count"], 161)
        self.assertEqual(zero_latency["command_delivery_count"], 161)
        self.assertEqual(zero_latency["applied_force"][0], 18)
        self.assertEqual(zero_latency["measurement_age"][0], 0)
        self.assertEqual(zero_latency["command_source_age"][0], 0)
        self.assertEqual(zero_latency["command_arrival_age"][0], 0)
        self.assertEqual(zero_latency["startup_safe_duration"], 0)
        self.assertEqual(zero_latency["watchdog_duration"], 0)

    def test_two_timing_sweeps_are_independent_and_cross_limits(self):
        latency_runs = [reference_run(latency=value) for value in LATENCY_VALUES_SEC]
        latency_ages = [run["maximum_measurement_age"] for run in latency_runs]
        latency_speeds = [run["peak_velocity"] for run in latency_runs]
        for run in latency_runs:
            self.assertEqual(run["controller_ticks"], 5)
            self.assertEqual(run["watchdog_ticks"], 20)
            self.assertEqual(run["command_drop_count"], 0)
        self.assertTrue(all(a < b for a, b in zip(latency_ages, latency_ages[1:])))
        self.assertTrue(all(a < b for a, b in zip(latency_speeds, latency_speeds[1:])))
        self.assertGreater(latency_runs[-1]["tracking_rms"], latency_runs[0]["tracking_rms"])

        period_runs = [
            reference_run(controller_period=value) for value in PERIOD_VALUES_SEC
        ]
        period_ages = [run["maximum_measurement_age"] for run in period_runs]
        period_speeds = [run["peak_velocity"] for run in period_runs]
        period_commands = [run["command_sent_count"] for run in period_runs]
        for run in period_runs:
            self.assertEqual(run["latency_ticks"], 1)
            self.assertEqual(run["watchdog_ticks"], 20)
            self.assertEqual(run["command_drop_count"], 0)
        self.assertTrue(all(a < b for a, b in zip(period_ages, period_ages[1:])))
        self.assertTrue(all(a < b for a, b in zip(period_speeds, period_speeds[1:])))
        self.assertTrue(all(a > b for a, b in zip(period_commands, period_commands[1:])))
        self.assertGreater(period_runs[-1]["tracking_rms"], period_runs[0]["tracking_rms"])

    def test_broken_timeout_no_drop_recovery_and_arrival_clearing(self):
        broken = reference_run(
            controller_period=0.1,
            latency=0.04,
            watchdog_timeout=0.12,
            drop_every=2,
        )
        recovered = reference_run(
            controller_period=0.1,
            latency=0.04,
            watchdog_timeout=0.12,
            drop_every=0,
        )
        self.assertEqual(broken["command_sent_count"], 80)
        self.assertEqual(broken["command_drop_count"], 40)
        self.assertEqual(broken["command_delivery_count"], 40)
        self.assertGreater(broken["watchdog_duration"], 3)
        self.assertTrue(
            all(
                force == 0
                for force, timed_out in zip(
                    broken["applied_force"], broken["watchdog_timed_out"]
                )
                if timed_out
            )
        )
        self.assertEqual(recovered["command_drop_count"], 0)
        self.assertEqual(recovered["command_delivery_count"], 79)
        self.assertEqual(recovered["watchdog_duration"], 0)
        self.assertFalse(any(recovered["watchdog_timed_out"]))
        for index, delivered in enumerate(broken["command_delivered"]):
            if delivered:
                self.assertFalse(broken["watchdog_timed_out"][index])

    def test_watchdog_boundary_and_same_tick_delivery_recovery(self):
        broken = reference_run(
            controller_period=0.1,
            latency=0.04,
            watchdog_timeout=0.12,
            drop_every=2,
        )
        first_delivery = broken["command_delivered"].index(True)
        first_timeout = broken["watchdog_timed_out"].index(True)
        self.assertAlmostEqual(
            broken["time"][first_timeout],
            broken["time"][first_delivery] + 0.12,
        )
        self.assertFalse(broken["watchdog_timed_out"][first_timeout - 1])
        self.assertLess(broken["command_arrival_age"][first_timeout - 1], 0.12)
        self.assertAlmostEqual(broken["command_arrival_age"][first_timeout], 0.12)
        self.assertEqual(
            broken["applied_force"][first_timeout - 1],
            broken["applied_force"][first_delivery],
        )
        self.assertEqual(broken["applied_force"][first_timeout], 0)

        recovery_deliveries = [
            index
            for index in range(1, len(broken["time"]))
            if broken["command_delivered"][index]
            and broken["watchdog_timed_out"][index - 1]
        ]
        self.assertTrue(recovery_deliveries)
        for index in recovery_deliveries:
            with self.subTest(time=broken["time"][index]):
                self.assertEqual(broken["command_arrival_age"][index], 0)
                self.assertFalse(broken["watchdog_timed_out"][index])
                self.assertFalse(broken["safe_zero"][index])

        for startup, timeout, cancelled, safe_zero in zip(
            broken["startup_safe"],
            broken["watchdog_timed_out"],
            broken["cancelled"],
            broken["safe_zero"],
        ):
            self.assertEqual(safe_zero, startup or timeout or cancelled)

    def test_cancellation_precedence_rollback_recovery_and_isolation(self):
        baseline = reference_run()
        immediate = reference_run(cancel_at=0)
        on_arrival = reference_run(cancel_at=0.06)
        at_four = reference_run(cancel_at=4)
        visible_arrival_tie = reference_run(cancel_at=4.01)
        self.assertEqual(immediate["command_sent_count"], 0)
        self.assertEqual(immediate["command_delivery_count"], 0)
        self.assertTrue(all(force == 0 for force in immediate["applied_force"]))
        self.assertTrue(all(position == 0 for position in immediate["position"]))
        self.assertEqual(immediate["watchdog_duration"], 0)

        self.assertEqual(on_arrival["command_sent_count"], 1)
        self.assertEqual(on_arrival["command_delivery_count"], 0)
        self.assertTrue(all(force == 0 for force in on_arrival["applied_force"]))

        cancel_index = at_four["cancelled"].index(True)
        self.assertAlmostEqual(at_four["time"][cancel_index], 4)
        self.assertTrue(all(force == 0 for force in at_four["applied_force"][cancel_index:]))
        self.assertFalse(any(at_four["command_delivered"][cancel_index:]))
        self.assertEqual(at_four["watchdog_duration"], 0)
        self.assertEqual(at_four["cancellation_duration"], 4)
        visible_cancel_index = visible_arrival_tie["cancelled"].index(True)
        self.assertAlmostEqual(visible_arrival_tie["time"][visible_cancel_index], 4.01)
        self.assertTrue(visible_arrival_tie["command_sent"][visible_cancel_index - 1])
        self.assertTrue(baseline["command_delivered"][visible_cancel_index])
        self.assertFalse(visible_arrival_tie["command_delivered"][visible_cancel_index])
        self.assertTrue(
            all(
                force == 0
                for force in visible_arrival_tie["applied_force"][visible_cancel_index:]
            )
        )
        self.assertEqual(reference_run(), baseline)

    def test_resource_bounds_and_extreme_response_stop(self):
        minimum = reference_run(
            controller_period=0.02,
            latency=0,
            watchdog_timeout=1,
            mass=5,
            time_step=0.02,
            duration=4,
        )
        maximum = reference_run(
            controller_period=0.02,
            latency=0,
            watchdog_timeout=1,
            mass=5,
            time_step=0.005,
            duration=20,
        )
        self.assertEqual(minimum["allocated_count"], 201)
        self.assertEqual(maximum["allocated_count"], 4001)
        self.assertTrue(all(math.isfinite(value) for value in maximum["position"]))
        self.assertTrue(all(math.isfinite(value) for value in maximum["velocity"]))
        with self.assertRaisesRegex(ValueError, "P24:ResponseBound"):
            reference_run(
                controller_period=0.2,
                latency=0.2,
                watchdog_timeout=0.5,
                drop_every=2,
                mass=0.5,
                duration=4,
            )
        self.assertEqual(reference_run(), reference_run())

    def test_experiment_has_order_labels_metrics_sweeps_failure_and_cancel(self):
        experiment = self.read("experiment.m")
        ordered_markers = (
            "%% Read:",
            "%% Make one prediction before the baseline",
            "%% Visualize the deterministic baseline position loop",
            "%% Read the mechanism",
            "%% Move lever 1:",
            "%% Explain lever 1",
            "%% Reset, then move lever 2:",
            "%% Explain lever 2",
            "%% Deliberately broken case:",
            "%% Cancel, roll to safe zero, and recover",
            "%% Check and teach back",
        )
        positions = [experiment.index(marker) for marker in ordered_markers]
        self.assertEqual(positions, sorted(positions))
        for marker in (
            "baseline = model(0.05,0.01,0.2,0,Inf,1.5,0.01,8)",
            "latencyValuesSec = [0.01 0.02 0.04 0.06 0.08]",
            "controllerPeriodValuesSec = [0.02 0.04 0.05 0.1 0.2]",
            "broken = model(0.1,0.04,0.12,2,Inf,1.5,0.01,8)",
            "dropRecovered = model(0.1,0.04,0.12,0,Inf,1.5,0.01,8)",
            "cancelledRun = model(0.05,0.01,0.2,0,4.01,1.5,0.01,8)",
            "Virtual time (s)",
            "Position (m)",
            "Force (N)",
            "Measurement age (s)",
            "Tracking RMS (m)",
            "Command packets (count)",
            "run_checks;",
        ):
            self.assertIn(marker, experiment)
        self.assertGreaterEqual(experiment.count("figure("), 6)
        self.assertEqual(experiment.count("%% Make one prediction"), 1)
        self.assertEqual(experiment.count("clear run_checks;"), 1)
        self.assertLess(experiment.index("clear run_checks;"), experiment.index("\nrun_checks;\n"))

    def test_interactive_has_controls_reset_safe_feedback_and_claim_boundary(self):
        interactive = self.read("interactive.m")
        for marker in (
            "function interactive",
            "uifigure(",
            "uiaxes(",
            "uidropdown(",
            "uispinner(",
            "uislider(",
            "Controller period (s)",
            "One-way latency (s)",
            "Watchdog timeout (s)",
            "Drop every Nth command",
            "Plant mass (kg)",
            "Simulated cancellation",
            "ValueChangingFcn",
            "ValueChangedFcn",
            "ButtonPushedFcn",
            "resetBaseline",
            "redraw(0.05,0.01,0.2,0,1.5,Inf)",
            "watchdogTimedOut",
            "simulated cancellation wins",
            "command continuity failed",
            "No hardware command was sent",
            "No virtual command history produced",
            "no physical HIL ran",
        ):
            self.assertIn(marker, interactive)
        self.assertGreaterEqual(interactive.count("uiaxes("), 2)
        self.assertLess(
            interactive.index("if isfinite(cancelAt)"),
            interactive.index("elseif any(result.watchdogTimedOut)"),
        )

    def test_checks_cover_oracles_limits_malformed_timeout_cancel_and_recovery(self):
        checks = self.read("run_checks.m")
        for marker in (
            "isequaln(baselineA,baselineB)",
            "expectedVelocity",
            "expectedPosition",
            "expectedMeasurementDelivery",
            "expectedRawForceN",
            "lastMeasurementTimestampSec",
            "lastCommandSourceTimestampSec",
            "startupSafeDurationSec-0.06",
            "watchdogDurationSec == 0",
            "latencyValuesSec = [0.01 0.02 0.04 0.06 0.08]",
            "controllerPeriodValuesSec = [0.02 0.04 0.05 0.1 0.2]",
            "zeroLatency = model(0.05,0,0.2,0,Inf,1.5,0.01,8)",
            "broken = model(0.1,0.04,0.12,2,Inf,1.5,0.01,8)",
            "dropRecovered = model(0.1,0.04,0.12,0,Inf,1.5,0.01,8)",
            "firstTimeoutIndex",
            "recoveryDeliveryIndices",
            "broken.commandAgeSec(firstTimeoutIndex)",
            "~any(broken.safeZeroActive(recoveryDeliveryIndices))",
            "cancelAtZero",
            "cancelOnArrival",
            "cancelAtFour",
            "P24:ControllerPeriodRange",
            "P24:LatencyGridMismatch",
            "P24:CancellationGridMismatch",
            "P24:ResponseBound",
            "minimumHistory",
            "maximumHistory",
            "assertAnyError",
            "assertErrorId",
        ):
            self.assertIn(marker, checks)

    def test_tutor_text_connects_prerequisites_and_preserves_claim_boundary(self):
        combined = "\n".join(
            self.read(name)
            for name in ("README.md", "lesson.md", "walkthrough.md", "checks.md")
        )
        self.assertIn("P23 separated requested acceleration", self.read("lesson.m"))
        for marker in (
            QUESTION,
            "P23",
            "P10",
            "controller period",
            "one-way latency",
            "measurement age",
            "command age",
            "watchdog",
            "packet",
            "cancellation",
            "safe zero",
            "0.1 s",
            "0.04 s",
            "0.12 s",
            "exactly two sentences",
            "No MATLAB-runtime",
            "physical HIL",
            "RT1/RT2",
        ):
            self.assertIn(marker.lower(), combined.lower())
        for placeholder in (
            "scaffolded",
            "placeholder",
            "todo",
            "not implemented",
            "planned learner sequence",
            "planned concept loop",
        ):
            self.assertNotIn(placeholder, combined.lower())
        opaque_calls = (
            r"\b(?:tf|ss|lsim|c2d|step|bode|ode45|ode23|sim|tcpclient|udpport|"
            r"serialport|timer|inv|pinv|eig|fmincon|quadprog|solve)\s*\("
        )
        for name in (
            "model.m",
            "experiment.m",
            "interactive.m",
            "run_checks.m",
            "lesson.m",
        ):
            self.assertNotRegex(self.read(name), re.compile(opaque_calls, re.I))

    def test_frontier_documents_include_permanent_p24_facts(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("./bin/learn start P24", root_readme)
        self.assertIn("P24", start_here)
        p24_row = next(
            line for line in module_index.splitlines() if line.startswith("| P24 |")
        )
        self.assertTrue(p24_row.endswith("| implemented |"))

    def test_readme_path_scope_and_public_cli_state_isolation(self):
        readme = self.read("README.md")
        self.assertIn(
            'moduleFolder = fullfile(pwd,"modules","24-close-the-loop-through-a-hardware-in-the-loop-plant");',
            readme,
        )
        self.assertIn('addpath(moduleFolder,"-begin");', readme)
        self.assertIn("clear model interactive;", readme)
        self.assertEqual(readme.count("rmpath(moduleFolder);"), 2)
        self.assertIn("rethrow(exception)", readme)

        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            shutil.copytree(ROOT / "bin", fixture / "bin")
            shutil.copytree(ROOT / "curriculum", fixture / "curriculum")
            shutil.copytree(self.folder, fixture / self.module["folder"])
            progress_file = fixture / ".learning/progress.json"
            progress_file.parent.mkdir(parents=True)
            original = {
                "current": "P23",
                "completed": {"P22": True},
                "notes": {"P22": "preserve prior note"},
            }
            progress_file.write_text(
                json.dumps(original, indent=2) + "\n", encoding="utf-8"
            )
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"

            checked = subprocess.run(
                [str(fixture / "bin/learn"), "check", "P24"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(checked.stdout, "Run in MATLAB: run_module_checks('P24')\n")
            self.assertEqual(json.loads(progress_file.read_text()), original)

            started = subprocess.run(
                [str(fixture / "bin/learn"), "start", "P24"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn(f"Guiding question: {QUESTION}", started.stdout)
            retained = json.loads(progress_file.read_text())
            self.assertEqual(retained["current"], "P24")
            self.assertEqual(retained["completed"], original["completed"])
            self.assertEqual(retained["notes"], original["notes"])

            continued = subprocess.run(
                [str(fixture / "bin/learn"), "continue"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(continued.returncode, 0, continued.stderr)
            self.assertEqual(continued.stdout, started.stdout)

            teach_back = (
                "Controller period and one-way latency set when feedback crosses the boundary. "
                "Command age triggers safe zero, but this software emulator is not physical HIL evidence."
            )
            completed = subprocess.run(
                [
                    str(fixture / "bin/learn"),
                    "complete",
                    "P24",
                    "--note",
                    teach_back,
                ],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            retained = json.loads(progress_file.read_text())
            self.assertEqual(retained["completed"], {"P22": True, "P24": True})
            self.assertEqual(retained["notes"]["P22"], "preserve prior note")
            self.assertEqual(retained["notes"]["P24"], teach_back)


if __name__ == "__main__":
    unittest.main()
