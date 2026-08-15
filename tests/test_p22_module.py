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
    "What inputs, observable effects, and failure modes matter when you implement "
    "Proportional Navigation?"
)
NAVIGATION_VALUES = [1, 2, 3, 4, 5]
AUTHORITY_VALUES = [5, 10, 20, 40, 80]


def reference_run(
    navigation_constant: float = 3,
    target_crossing_speed: float = 60,
    acceleration_limit: float = 80,
    time_step: float = 0.02,
    maximum_time: float = 25,
) -> dict[str, object]:
    interceptor_speed = 300.0
    capture_radius = 5.0
    allocated_count = round(maximum_time / time_step) + 1
    time = [0.0]
    interceptor_x = [0.0]
    interceptor_y = [0.0]
    target_x = [5000.0]
    target_y = [600.0]
    heading = [0.0]
    ranges: list[float] = []
    los_angle: list[float] = []
    los_rate: list[float] = []
    closing_speed: list[float] = []
    command: list[float] = []
    applied: list[float] = []
    saturated: list[bool] = []
    intercepted = False
    final_step_fraction = 1.0

    for index in range(allocated_count):
        interceptor_vx = interceptor_speed * math.cos(heading[index])
        interceptor_vy = interceptor_speed * math.sin(heading[index])
        relative_x = target_x[index] - interceptor_x[index]
        relative_y = target_y[index] - interceptor_y[index]
        relative_vx = -interceptor_vx
        relative_vy = target_crossing_speed - interceptor_vy
        range_squared = relative_x**2 + relative_y**2
        current_range = math.sqrt(range_squared)
        current_closing_speed = -(
            relative_x * relative_vx + relative_y * relative_vy
        ) / current_range
        current_los_rate = (
            relative_x * relative_vy - relative_y * relative_vx
        ) / range_squared
        current_command = (
            navigation_constant
            * max(current_closing_speed, 0.0)
            * current_los_rate
        )
        current_applied = min(
            max(current_command, -acceleration_limit), acceleration_limit
        )
        saturation_tolerance = 64 * math.ulp(
            max(1.0, abs(current_command), acceleration_limit)
        )

        ranges.append(current_range)
        los_angle.append(math.atan2(relative_y, relative_x))
        los_rate.append(current_los_rate)
        closing_speed.append(current_closing_speed)
        command.append(current_command)
        applied.append(current_applied)
        saturated.append(
            abs(current_command) > acceleration_limit + saturation_tolerance
        )

        if current_range <= capture_radius + 1e-8:
            intercepted = True
            break
        if index == allocated_count - 1:
            break

        proposed_heading = (
            heading[index]
            + current_applied / interceptor_speed * time_step
        )
        proposed_interceptor_x = (
            interceptor_x[index]
            + interceptor_speed * math.cos(proposed_heading) * time_step
        )
        proposed_interceptor_y = (
            interceptor_y[index]
            + interceptor_speed * math.sin(proposed_heading) * time_step
        )
        proposed_target_x = target_x[index]
        proposed_target_y = target_y[index] + target_crossing_speed * time_step
        next_relative_x = proposed_target_x - proposed_interceptor_x
        next_relative_y = proposed_target_y - proposed_interceptor_y
        delta_x = next_relative_x - relative_x
        delta_y = next_relative_y - relative_y
        segment_a = delta_x**2 + delta_y**2
        segment_b = 2 * (relative_x * delta_x + relative_y * delta_y)
        segment_c = range_squared - capture_radius**2
        discriminant = segment_b**2 - 4 * segment_a * segment_c
        crossing_fraction: float | None = None
        if segment_a > 0 and discriminant >= 0:
            candidate = (-segment_b - math.sqrt(discriminant)) / (2 * segment_a)
            if 0 <= candidate <= 1:
                crossing_fraction = candidate

        if crossing_fraction is None:
            time.append(time[index] + time_step)
            heading.append(proposed_heading)
            interceptor_x.append(proposed_interceptor_x)
            interceptor_y.append(proposed_interceptor_y)
            target_x.append(proposed_target_x)
            target_y.append(proposed_target_y)
        else:
            final_step_fraction = crossing_fraction
            time.append(time[index] + crossing_fraction * time_step)
            heading.append(
                heading[index]
                + crossing_fraction * (proposed_heading - heading[index])
            )
            interceptor_x.append(
                interceptor_x[index]
                + crossing_fraction
                * (proposed_interceptor_x - interceptor_x[index])
            )
            interceptor_y.append(
                interceptor_y[index]
                + crossing_fraction
                * (proposed_interceptor_y - interceptor_y[index])
            )
            target_x.append(
                target_x[index]
                + crossing_fraction * (proposed_target_x - target_x[index])
            )
            target_y.append(
                target_y[index]
                + crossing_fraction * (proposed_target_y - target_y[index])
            )

    sampled_closest = min(ranges)
    closest_distance = sampled_closest
    closest_time = time[ranges.index(sampled_closest)]
    for index in range(len(time) - 1):
        relative_start = (
            target_x[index] - interceptor_x[index],
            target_y[index] - interceptor_y[index],
        )
        relative_end = (
            target_x[index + 1] - interceptor_x[index + 1],
            target_y[index + 1] - interceptor_y[index + 1],
        )
        delta = (
            relative_end[0] - relative_start[0],
            relative_end[1] - relative_start[1],
        )
        delta_squared = delta[0] ** 2 + delta[1] ** 2
        fraction = 0.0
        if delta_squared > 0:
            fraction = min(
                max(
                    -(
                        relative_start[0] * delta[0]
                        + relative_start[1] * delta[1]
                    )
                    / delta_squared,
                    0.0,
                ),
                1.0,
            )
        distance = math.hypot(
            relative_start[0] + fraction * delta[0],
            relative_start[1] + fraction * delta[1],
        )
        if distance < closest_distance:
            closest_distance = distance
            closest_time = time[index] + fraction * (
                time[index + 1] - time[index]
            )

    if intercepted:
        saturation_duration = (
            sum(saturated[:-2]) * time_step
            + saturated[-2] * final_step_fraction * time_step
        )
    else:
        saturation_duration = sum(saturated[:-1]) * time_step

    return {
        "navigation_constant": navigation_constant,
        "target_crossing_speed": target_crossing_speed,
        "acceleration_limit": acceleration_limit,
        "time_step": time_step,
        "maximum_time": maximum_time,
        "allocated_count": allocated_count,
        "used_count": len(time),
        "time": time,
        "interceptor_x": interceptor_x,
        "interceptor_y": interceptor_y,
        "target_x": target_x,
        "target_y": target_y,
        "heading": heading,
        "range": ranges,
        "los_angle": los_angle,
        "los_rate": los_rate,
        "closing_speed": closing_speed,
        "command": command,
        "applied": applied,
        "saturated": saturated,
        "intercepted": intercepted,
        "termination": "intercept" if intercepted else "time-limit",
        "closest_distance": closest_distance,
        "closest_time": closest_time,
        "sampled_closest": sampled_closest,
        "final_step_fraction": final_step_fraction,
        "peak_command": max(abs(value) for value in command),
        "peak_applied": max(abs(value) for value in applied),
        "saturation_duration": saturation_duration,
    }


class P22ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P22"
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
                "number": 22,
                "id": "P22",
                "title": "Implement Proportional Navigation",
                "guiding_question": QUESTION,
                "phase": 6,
                "phase_title": "Guidance and HIL",
                "slug": "implement-proportional-navigation",
                "folder": "modules/22-implement-proportional-navigation",
                "status": "implemented",
                "implementation_batch": "P22",
                "prerequisites": ["P21"],
                "evidence_level": "simulated",
            },
        )
        prerequisite = next(
            module for module in self.manifest["modules"] if module["id"] == "P21"
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

    def test_model_is_transparent_deterministic_and_resource_bounded(self):
        model = self.read("model.m")
        for marker in (
            "relativeXM = targetXM(k)-interceptorXM(k)",
            "rangeSquaredM2 = relativeXM^2+relativeYM^2",
            "closingSpeedMPerSec(k) = -(relativeXM*relativeVelocityXMPerSec+",
            "(relativeXM*relativeVelocityYMPerSec- ...",
            "positiveClosingSpeedMPerSec = max(closingSpeedMPerSec(k),0)",
            "commandAccelerationMPerSec2(k) = navigationConstant*",
            "actualAccelerationMPerSec2(k) = min(max(",
            "actualAccelerationMPerSec2(k)/interceptorSpeedMPerSec*timeStepSec",
            "segmentDiscriminant = segmentB^2-4*segmentA*segmentC",
            "candidateFraction = (-segmentB-sqrt(segmentDiscriminant))/(2*segmentA)",
            "if closestFraction <= 0.5",
            "closestApproachIndex = k+1",
            "maximumStepCount = 5001",
            "P22:NavigationConstantRange",
            "P22:TargetCrossingSpeedRange",
            "P22:AccelerationLimitRange",
            "P22:TimeStepRange",
            "P22:MaximumTimeRange",
            "P22:TimeGridMismatch",
            "P22:StepCountRange",
        ):
            self.assertIn(marker, model)
        self.assertLess(
            model.index("allocatedStepCount > maximumStepCount"),
            model.index("timeSec = (0:roundedStepRatio)*timeStepSec"),
        )
        self.assertNotRegex(
            model.lower(),
            r"\b(?:plot|figure|uifigure|uiaxes|uislider|uidropdown|rng|rand|randn|"
            r"global|persistent|fopen|webread|webwrite|system|parfor)\s*\(?",
        )

    def test_independent_baseline_geometry_recurrence_and_event(self):
        baseline_a = reference_run()
        baseline_b = reference_run()
        self.assertEqual(baseline_a, baseline_b)
        self.assertAlmostEqual(baseline_a["range"][0], 5035.871324805668)
        self.assertAlmostEqual(
            baseline_a["closing_speed"][0], 290.7143383089708
        )
        self.assertAlmostEqual(
            baseline_a["los_rate"][0], 0.018927444794952685
        )
        self.assertAlmostEqual(
            baseline_a["command"][0], 16.50743876833273
        )
        self.assertTrue(baseline_a["intercepted"])
        self.assertEqual(baseline_a["termination"], "intercept")
        self.assertAlmostEqual(
            baseline_a["closest_distance"], 5.0, places=9
        )
        self.assertAlmostEqual(
            baseline_a["closest_time"], 17.72639209846985, places=10
        )
        self.assertEqual(baseline_a["saturation_duration"], 0)
        self.assertGreater(baseline_a["final_step_fraction"], 0)
        self.assertLess(baseline_a["final_step_fraction"], 1)
        self.assertLess(abs(baseline_a["los_rate"][-1]), 2e-6)

        for index in range(len(baseline_a["time"]) - 2):
            expected_heading = (
                baseline_a["heading"][index]
                + baseline_a["applied"][index] / 300 * 0.02
            )
            self.assertAlmostEqual(
                baseline_a["heading"][index + 1], expected_heading
            )
            self.assertAlmostEqual(
                baseline_a["interceptor_x"][index + 1],
                baseline_a["interceptor_x"][index]
                + 300 * math.cos(expected_heading) * 0.02,
            )
            self.assertAlmostEqual(
                baseline_a["interceptor_y"][index + 1],
                baseline_a["interceptor_y"][index]
                + 300 * math.sin(expected_heading) * 0.02,
            )

    def test_two_sweeps_are_independent_and_cross_boundaries(self):
        navigation_runs = [reference_run(navigation_constant=value) for value in NAVIGATION_VALUES]
        self.assertTrue(
            all(run["target_crossing_speed"] == 60 for run in navigation_runs)
        )
        self.assertTrue(
            all(run["acceleration_limit"] == 80 for run in navigation_runs)
        )
        initial_command_per_n = (
            reference_run()["closing_speed"][0]
            * reference_run()["los_rate"][0]
        )
        for value, run in zip(NAVIGATION_VALUES, navigation_runs):
            self.assertAlmostEqual(run["command"][0], value * initial_command_per_n)
        self.assertEqual(
            [run["intercepted"] for run in navigation_runs],
            [False, True, True, True, True],
        )
        self.assertGreater(navigation_runs[0]["closest_distance"], 50)

        authority_runs = [reference_run(acceleration_limit=value) for value in AUTHORITY_VALUES]
        self.assertTrue(
            all(run["navigation_constant"] == 3 for run in authority_runs)
        )
        self.assertTrue(
            all(run["target_crossing_speed"] == 60 for run in authority_runs)
        )
        self.assertEqual(
            [run["intercepted"] for run in authority_runs],
            [False, False, True, True, True],
        )
        for limit, run in zip(AUTHORITY_VALUES, authority_runs):
            self.assertLessEqual(run["peak_applied"], limit)
        self.assertGreater(authority_runs[0]["saturation_duration"], 17)
        self.assertEqual(authority_runs[-1]["saturation_duration"], 0)

    def test_negative_los_commands_clips_and_turns_in_negative_direction(self):
        run = reference_run(
            target_crossing_speed=-150,
            acceleration_limit=5,
        )
        initial_range = math.hypot(5000, 600)
        expected_closing_speed = -(5000 * -300 + 600 * -150) / initial_range
        expected_los_rate = (5000 * -150 - 600 * -300) / initial_range**2
        expected_command = 3 * expected_closing_speed * expected_los_rate

        self.assertLess(expected_los_rate, 0)
        self.assertAlmostEqual(run["closing_speed"][0], expected_closing_speed)
        self.assertAlmostEqual(run["los_rate"][0], expected_los_rate)
        self.assertAlmostEqual(run["command"][0], expected_command)
        self.assertLess(run["command"][0], -5)
        self.assertEqual(run["applied"][0], -5)
        self.assertTrue(run["saturated"][0])
        self.assertAlmostEqual(run["heading"][1], -5 / 300 * 0.02)

        checks = self.read("run_checks.m")
        self.assertIn(
            "negativeLineOfSight = model(3,-150,5,0.02,25)",
            checks,
        )
        self.assertIn(
            "Negative LOS motion must command, clip, and turn in the negative direction.",
            checks,
        )

    def test_limiting_broken_timeout_recovery_and_resource_cases(self):
        collision_course = reference_run(target_crossing_speed=-36)
        self.assertTrue(collision_course["intercepted"])
        self.assertEqual(collision_course["los_rate"][0], 0)
        self.assertEqual(collision_course["command"][0], 0)
        self.assertLess(max(abs(value) for value in collision_course["command"]), 1e-8)

        disabled = reference_run(navigation_constant=0)
        relative_velocity = (-300.0, 60.0)
        closest_time = -(
            5000 * relative_velocity[0] + 600 * relative_velocity[1]
        ) / (relative_velocity[0] ** 2 + relative_velocity[1] ** 2)
        closest_distance = math.hypot(
            5000 + closest_time * relative_velocity[0],
            600 + closest_time * relative_velocity[1],
        )
        self.assertFalse(disabled["intercepted"])
        self.assertTrue(all(value == 0 for value in disabled["command"]))
        self.assertTrue(all(value == 0 for value in disabled["heading"]))
        self.assertAlmostEqual(disabled["closest_time"], closest_time)
        self.assertAlmostEqual(disabled["closest_distance"], closest_distance)

        broken = reference_run(acceleration_limit=5)
        recovered = reference_run()
        short = reference_run(maximum_time=5)
        self.assertFalse(broken["intercepted"])
        self.assertEqual(broken["termination"], "time-limit")
        self.assertGreater(broken["closest_distance"], 900)
        self.assertEqual(broken["peak_applied"], 5)
        opening = [
            command
            for command, closing in zip(
                broken["command"], broken["closing_speed"]
            )
            if closing <= 0
        ]
        self.assertTrue(opening)
        self.assertTrue(all(value == 0 for value in opening))
        self.assertEqual(recovered, reference_run())
        self.assertFalse(short["intercepted"])
        self.assertAlmostEqual(short["time"][-1], 5)

        coarse = reference_run(time_step=0.1)
        fine = reference_run(time_step=0.005)
        self.assertTrue(coarse["intercepted"] and fine["intercepted"])
        self.assertAlmostEqual(coarse["closest_distance"], 5, places=9)
        self.assertAlmostEqual(fine["closest_distance"], 5, places=9)
        self.assertLess(abs(coarse["closest_time"] - fine["closest_time"]), 0.01)
        maximum = reference_run(
            navigation_constant=0,
            acceleration_limit=120,
            time_step=0.008,
            maximum_time=40,
        )
        self.assertEqual(maximum["allocated_count"], 5001)
        self.assertEqual(maximum["used_count"], 5001)
        for field in ("range", "los_rate", "command", "applied"):
            self.assertTrue(all(math.isfinite(value) for value in maximum[field]))

    def test_experiment_has_ordered_flow_labels_metrics_sweeps_and_broken_case(self):
        experiment = self.read("experiment.m")
        ordered = (
            "%% Read:",
            "%% Make one prediction",
            "%% Visualize the deterministic baseline",
            "%% Read the mechanism:",
            "%% Move lever 1:",
            "%% Explain lever 1",
            "%% Reset, then move lever 2:",
            "%% Explain lever 2",
            "%% Deliberately broken case:",
            "%% Check, recover, and teach back",
        )
        positions = [experiment.index(marker) for marker in ordered]
        self.assertEqual(positions, sorted(positions))
        for marker in (
            "baseline = model(3,60,80,0.02,25)",
            "navigationConstantValues = [1 2 3 4 5]",
            "navigationInitialCommandMPerSec2",
            "accelerationLimitValuesMPerSec2 = [5 10 20 40 80]",
            "changed = model(navigationConstantValues(k),60,80,0.02,25)",
            "changed = model(3,60,accelerationLimitValuesMPerSec2(k),0.02,25)",
            "broken = model(3,60,5,0.02,25)",
            "recovered = model(3,60,80,0.02,25)",
            "Downrange x (m)",
            "Crossrange y (m)",
            "Range (m)",
            "LOS rate (deg/s)",
            "Lateral acceleration (m/s^2)",
            "Navigation constant N (dimensionless)",
            "run_checks;",
        ):
            self.assertIn(marker, experiment)
        self.assertGreaterEqual(experiment.count("figure("), 5)
        self.assertEqual(experiment.count("%% Make one prediction"), 1)
        self.assertEqual(experiment.count("clear run_checks;"), 1)
        self.assertLess(
            experiment.index("clear run_checks;"),
            experiment.index("\nrun_checks;\n"),
        )

    def test_interactive_has_controls_reset_feedback_and_outcome_precedence(self):
        interactive = self.read("interactive.m")
        for marker in (
            "function interactive",
            "uifigure(",
            "uiaxes(",
            "uislider(",
            "uispinner(",
            "Navigation constant N (dimensionless)",
            "Target crossing speed (m/s)",
            "Acceleration limit (m/s^2)",
            "ValueChangingFcn",
            "ValueChangedFcn",
            "ButtonPushedFcn",
            "resetBaseline",
            "redraw(3,60,80)",
            "result = modelFunction(navigationConstant,targetCrossingSpeed, ...",
            "time-limit miss with clipping",
            "compare a higher limit before",
            "N=0 disables guidance",
            "capture radius",
            "saturation duration",
        ):
            self.assertIn(marker, interactive)
        self.assertGreaterEqual(interactive.count("uiaxes("), 3)
        self.assertLess(
            interactive.index("elseif result.saturationDurationSec > 0"),
            interactive.index("elseif navigationConstant == 0"),
        )

    def test_checks_cover_oracles_limits_malformed_timeout_recovery_and_bounds(self):
        checks = self.read("run_checks.m")
        for marker in (
            "isequaln(baselineA,baselineB)",
            "expectedRangeM",
            "expectedClosingSpeedMPerSec",
            "expectedLineOfSightRateRadPerSec",
            "expectedCommandAccelerationMPerSec2",
            "expectedNextHeading",
            "navigationConstantValues = [1 2 3 4 5]",
            "accelerationLimitValuesMPerSec2 = [5 10 20 40 80]",
            "collisionCourse = model(3,-36,80,0.02,25)",
            "guidanceDisabled = model(0,60,80,0.02,25)",
            "atLimit = model(3,60,exactLimit,0.02,25)",
            "broken = model(3,60,5,0.02,25)",
            "shortHorizon = model(3,60,80,0.02,5)",
            "recovered = model(3,60,80,0.02,25)",
            "P22:NavigationConstantRange",
            "P22:TargetCrossingSpeedRange",
            "P22:AccelerationLimitRange",
            "P22:TimeStepRange",
            "P22:MaximumTimeRange",
            "P22:TimeGridMismatch",
            "P22:StepCountRange",
            "boundedHistory = model(0,60,120,0.008,40)",
            "assertAnyError",
            "assertErrorId",
        ):
            self.assertIn(marker, checks)

    def test_tutor_text_connects_prerequisite_and_preserves_claim_boundary(self):
        combined = "\n".join(
            self.read(name)
            for name in ("README.md", "lesson.md", "walkthrough.md", "checks.md")
        )
        for marker in (
            QUESTION,
            "P21",
            "relative position",
            "relative velocity",
            "closing speed",
            "LOS rate",
            "constant bearing",
            "decreasing range",
            "navigation constant",
            "acceleration authority",
            "5 m/s^2",
            "80 m/s^2",
            "time limit",
            "exactly two sentences",
            "No MATLAB-runtime",
            "HIL",
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
            r"\b(?:proNav|trackingScenario|platform|waypointTrajectory|"
            r"quinticpolytraj|fmincon|quadprog|optimproblem|solve|ode45|ode23|"
            r"sim|ss|tf|lsim|inv|pinv|eig|spline|pchip)\s*\("
        )
        for name in (
            "model.m",
            "experiment.m",
            "interactive.m",
            "run_checks.m",
            "lesson.m",
        ):
            self.assertNotRegex(self.read(name), re.compile(opaque_calls, re.I))

    def test_learner_frontier_documents_include_permanent_p22_facts(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("./bin/learn start P22", root_readme)
        self.assertIn("P22", start_here)
        p22_row = next(
            line for line in module_index.splitlines() if line.startswith("| P22 |")
        )
        self.assertTrue(p22_row.endswith("| implemented |"))

    def test_readme_path_scope_and_public_cli_state_isolation(self):
        readme = self.read("README.md")
        self.assertIn(
            'moduleFolder = fullfile(pwd,"modules","22-implement-proportional-navigation");',
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
                "current": "P21",
                "completed": {"P20": True},
                "notes": {"P20": "preserve prior note"},
            }
            progress_file.write_text(
                json.dumps(original, indent=2) + "\n", encoding="utf-8"
            )
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"

            checked = subprocess.run(
                [str(fixture / "bin/learn"), "check", "P22"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(
                checked.stdout, "Run in MATLAB: run_module_checks('P22')\n"
            )
            self.assertEqual(json.loads(progress_file.read_text()), original)

            started = subprocess.run(
                [str(fixture / "bin/learn"), "start", "P22"],
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
            self.assertEqual(retained["current"], "P22")
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
                "Relative geometry gives closing speed and LOS rate, which N "
                "turns into a lateral command. Constant bearing with decreasing "
                "range supports capture only when acceleration authority can apply it."
            )
            completed = subprocess.run(
                [
                    str(fixture / "bin/learn"),
                    "complete",
                    "P22",
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
            self.assertEqual(retained["completed"], {"P20": True, "P22": True})
            self.assertEqual(retained["notes"]["P20"], "preserve prior note")
            self.assertEqual(retained["notes"]["P22"], teach_back)


if __name__ == "__main__":
    unittest.main()
