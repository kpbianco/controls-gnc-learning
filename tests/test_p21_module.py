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
    "What inputs, observable effects, and failure modes matter when you generate "
    "a Feasible Trajectory?"
)
DISTANCE_VALUES = [5.0, 10.0, 15.0, 20.0, 25.0]
DURATION_VALUES = [4.0, 6.0, 8.0, 10.0, 12.0]


def reference_run(
    target_position: float = 20.0,
    duration: float = 8.0,
    speed_limit: float = 5.0,
    acceleration_limit: float = 2.0,
    sample_count: int = 501,
) -> dict[str, object]:
    tau = [index / (sample_count - 1) for index in range(sample_count)]
    position_shape = [
        10 * value**3 - 15 * value**4 + 6 * value**5 for value in tau
    ]
    speed_shape = [
        30 * value**2 - 60 * value**3 + 30 * value**4 for value in tau
    ]
    acceleration_shape = [
        60 * value - 180 * value**2 + 120 * value**3 for value in tau
    ]
    jerk_shape = [60 - 360 * value + 360 * value**2 for value in tau]
    position = [target_position * value for value in position_shape]
    speed = [target_position / duration * value for value in speed_shape]
    acceleration = [
        target_position / duration**2 * value for value in acceleration_shape
    ]
    jerk = [target_position / duration**3 * value for value in jerk_shape]
    distance = abs(target_position)
    peak_speed = 15 * distance / (8 * duration)
    peak_acceleration = 10 * math.sqrt(3) * distance / (3 * duration**2)
    peak_jerk = 60 * distance / duration**3
    speed_duration = 15 * distance / (8 * speed_limit)
    acceleration_duration = math.sqrt(
        10 * math.sqrt(3) * distance / (3 * acceleration_limit)
    )
    minimum_duration = max(speed_duration, acceleration_duration)
    speed_utilization = peak_speed / speed_limit
    acceleration_utilization = peak_acceleration / acceleration_limit
    ratio_tolerance = 64 * math.ulp(
        max(1.0, speed_utilization, acceleration_utilization)
    )
    speed_feasible = speed_utilization <= 1 + ratio_tolerance
    acceleration_feasible = acceleration_utilization <= 1 + ratio_tolerance
    if distance == 0:
        active_constraint = "none"
    elif math.isclose(speed_duration, acceleration_duration, rel_tol=0, abs_tol=1e-14):
        active_constraint = "tie"
    elif speed_duration > acceleration_duration:
        active_constraint = "speed"
    else:
        active_constraint = "acceleration"
    return {
        "target_position": target_position,
        "duration": duration,
        "speed_limit": speed_limit,
        "acceleration_limit": acceleration_limit,
        "sample_count": sample_count,
        "tau": tau,
        "time": [duration * value for value in tau],
        "position_shape": position_shape,
        "speed_shape": speed_shape,
        "acceleration_shape": acceleration_shape,
        "jerk_shape": jerk_shape,
        "position": position,
        "speed": speed,
        "acceleration": acceleration,
        "jerk": jerk,
        "peak_speed": peak_speed,
        "peak_acceleration": peak_acceleration,
        "peak_jerk": peak_jerk,
        "sampled_peak_speed": max(abs(value) for value in speed),
        "sampled_peak_acceleration": max(abs(value) for value in acceleration),
        "sampled_peak_jerk": max(abs(value) for value in jerk),
        "speed_duration": speed_duration,
        "acceleration_duration": acceleration_duration,
        "minimum_duration": minimum_duration,
        "speed_utilization": speed_utilization,
        "acceleration_utilization": acceleration_utilization,
        "speed_feasible": speed_feasible,
        "acceleration_feasible": acceleration_feasible,
        "feasible": speed_feasible and acceleration_feasible,
        "active_constraint": active_constraint,
    }


class P21ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P21"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 21)
        self.assertEqual(self.module["title"], "Generate a Feasible Trajectory")
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["phase"], 6)
        self.assertEqual(self.module["phase_title"], "Guidance and HIL")
        self.assertEqual(
            self.module["folder"],
            "modules/21-generate-a-feasible-trajectory",
        )
        self.assertEqual(self.module["slug"], "generate-a-feasible-trajectory")
        self.assertEqual(self.module["prerequisites"], ["P20"])
        self.assertEqual(self.module["implementation_batch"], "P21")
        self.assertEqual(self.module["status"], "implemented")
        self.assertEqual(self.module["evidence_level"], "simulated")

    def test_complete_artifact_set_and_clean_eof(self):
        required = {
            "README.md",
            "lesson.m",
            "model.m",
            "experiment.m",
            "interactive.m",
            "lesson.md",
            "walkthrough.md",
            "checks.md",
            "run_checks.m",
        }
        self.assertTrue(required <= {path.name for path in self.folder.iterdir()})
        for name in required:
            with self.subTest(name=name):
                payload = (self.folder / name).read_bytes()
                self.assertTrue(payload.endswith(b"\n"))
                self.assertFalse(payload.endswith(b"\n\n"))

    def test_model_is_transparent_deterministic_and_resource_bounded(self):
        model = self.read("model.m")
        for formula in (
            "positionShape = 10*normalizedTime.^3-15*normalizedTime.^4+ ...",
            "speedShape = 30*normalizedTime.^2-60*normalizedTime.^3+ ...",
            "accelerationShape = 60*normalizedTime-180*normalizedTime.^2+ ...",
            "jerkShape = 60-360*normalizedTime+360*normalizedTime.^2",
            "positionM = targetPositionM*positionShape",
            "speedMPerSec = targetPositionM/moveDurationSec*speedShape",
            "analyticPeakSpeedMPerSec = 15*travelDistanceM/(8*moveDurationSec)",
            "analyticPeakAccelerationMPerSec2 = 10*sqrt(3)*travelDistanceM/ ...",
            "analyticPeakJerkMPerSec3 = 60*travelDistanceM/moveDurationSec^3",
            "minimumFeasibleDurationSec = max(minimumDurationFromSpeedSec, ...",
            "feasible = speedFeasible && accelerationFeasible",
        ):
            self.assertIn(formula, model)
        for marker in (
            "minimumSampleCount = 51",
            "maximumSampleCount = 5001",
            "P21:TargetPositionRange",
            "P21:DurationRange",
            "P21:SpeedLimitRange",
            "P21:AccelerationLimitRange",
            "P21:SampleCountRange",
            "ratioTolerance = 64*eps",
            "accelerationExtremaNormalizedTime",
            "endpointPositionResidualM",
        ):
            self.assertIn(marker, model)
        self.assertLess(
            model.index("sampleCount > maximumSampleCount"),
            model.index("normalizedTime = linspace"),
        )
        self.assertNotRegex(
            model.lower(),
            r"\b(?:plot|figure|uifigure|uiaxes|uislider|uidropdown|rng|rand|randn|"
            r"global|persistent|fopen|webread|webwrite|system)\s*\(?",
        )

    def test_independent_baseline_samples_endpoints_and_symmetry(self):
        baseline = reference_run()
        self.assertEqual(baseline["position"][0], 0)
        self.assertEqual(baseline["position"][-1], 20)
        self.assertEqual(baseline["speed"][0], 0)
        self.assertEqual(baseline["speed"][-1], 0)
        self.assertEqual(baseline["acceleration"][0], 0)
        self.assertEqual(baseline["acceleration"][-1], 0)
        midpoint = len(baseline["tau"]) // 2
        self.assertEqual(baseline["tau"][midpoint], 0.5)
        self.assertAlmostEqual(baseline["position"][midpoint], 10)
        self.assertAlmostEqual(baseline["speed"][midpoint], 4.6875)
        self.assertAlmostEqual(baseline["acceleration"][midpoint], 0)
        self.assertAlmostEqual(baseline["jerk"][midpoint], -1.171875)
        for index in range(len(baseline["tau"])):
            mirror = len(baseline["tau"]) - 1 - index
            self.assertAlmostEqual(
                baseline["position_shape"][index]
                + baseline["position_shape"][mirror],
                1,
            )
            self.assertAlmostEqual(
                baseline["speed_shape"][index],
                baseline["speed_shape"][mirror],
            )
            self.assertAlmostEqual(
                baseline["acceleration_shape"][index],
                -baseline["acceleration_shape"][mirror],
            )
        self.assertTrue(
            all(
                right >= left - 1e-12
                for left, right in zip(
                    baseline["position"], baseline["position"][1:]
                )
            )
        )

    def test_independent_analytic_peaks_and_minimum_duration(self):
        baseline = reference_run()
        self.assertAlmostEqual(baseline["peak_speed"], 4.6875)
        self.assertAlmostEqual(
            baseline["peak_acceleration"], 1.8042195912175802
        )
        self.assertAlmostEqual(baseline["peak_jerk"], 2.34375)
        self.assertAlmostEqual(baseline["speed_duration"], 7.5)
        self.assertAlmostEqual(
            baseline["acceleration_duration"], 7.598356856515925
        )
        self.assertAlmostEqual(baseline["minimum_duration"], 7.598356856515925)
        self.assertEqual(baseline["active_constraint"], "acceleration")
        self.assertTrue(baseline["feasible"])
        extrema = [(3 - math.sqrt(3)) / 6, (3 + math.sqrt(3)) / 6]
        exact_accelerations = [
            20
            / 8**2
            * (60 * tau - 180 * tau**2 + 120 * tau**3)
            for tau in extrema
        ]
        self.assertAlmostEqual(
            max(abs(value) for value in exact_accelerations),
            baseline["peak_acceleration"],
        )
        self.assertLess(
            baseline["sampled_peak_acceleration"],
            baseline["peak_acceleration"],
        )

    def test_two_sweeps_are_independent_and_match_scaling(self):
        distance_runs = [reference_run(target_position=value) for value in DISTANCE_VALUES]
        self.assertTrue(all(run["duration"] == 8 for run in distance_runs))
        self.assertTrue(all(run["speed_limit"] == 5 for run in distance_runs))
        self.assertEqual(
            [run["peak_speed"] for run in distance_runs],
            [15 * value / 64 for value in DISTANCE_VALUES],
        )
        self.assertTrue(distance_runs[-2]["feasible"])
        self.assertFalse(distance_runs[-1]["feasible"])
        self.assertEqual(distance_runs[0]["active_constraint"], "acceleration")
        self.assertEqual(distance_runs[-1]["active_constraint"], "speed")

        duration_runs = [reference_run(duration=value) for value in DURATION_VALUES]
        self.assertTrue(all(run["target_position"] == 20 for run in duration_runs))
        self.assertTrue(all(run["acceleration_limit"] == 2 for run in duration_runs))
        self.assertAlmostEqual(
            duration_runs[0]["peak_speed"] / duration_runs[2]["peak_speed"],
            2,
        )
        self.assertAlmostEqual(
            duration_runs[0]["peak_acceleration"]
            / duration_runs[2]["peak_acceleration"],
            4,
        )
        self.assertAlmostEqual(
            duration_runs[0]["peak_jerk"] / duration_runs[2]["peak_jerk"],
            8,
        )
        self.assertEqual(
            [run["feasible"] for run in duration_runs],
            [False, False, True, True, True],
        )

    def test_exact_boundaries_broken_case_and_limiting_cases(self):
        speed_duration = 15 * 25 / (8 * 5)
        speed_boundary = reference_run(25, speed_duration, 5, 20)
        speed_below = reference_run(25, speed_duration - 1e-6, 5, 20)
        self.assertEqual(speed_boundary["active_constraint"], "speed")
        self.assertTrue(speed_boundary["feasible"])
        self.assertAlmostEqual(speed_boundary["speed_utilization"], 1)
        self.assertFalse(speed_below["speed_feasible"])

        acceleration_duration = math.sqrt(10 * math.sqrt(3) * 5 / (3 * 2))
        acceleration_boundary = reference_run(5, acceleration_duration, 20, 2)
        acceleration_below = reference_run(
            5, acceleration_duration - 1e-6, 20, 2
        )
        self.assertEqual(
            acceleration_boundary["active_constraint"], "acceleration"
        )
        self.assertTrue(acceleration_boundary["feasible"])
        self.assertAlmostEqual(
            acceleration_boundary["acceleration_utilization"], 1
        )
        self.assertFalse(acceleration_below["acceleration_feasible"])

        tie_duration = 15 * 20 / (8 * 5)
        tie_acceleration_limit = (
            10 * math.sqrt(3) * 20 / (3 * tie_duration**2)
        )
        tie = reference_run(20, tie_duration, 5, tie_acceleration_limit)
        self.assertEqual(tie["active_constraint"], "tie")
        self.assertTrue(tie["feasible"])
        self.assertAlmostEqual(tie["speed_utilization"], 1)
        self.assertAlmostEqual(tie["acceleration_utilization"], 1)

        broken = reference_run(duration=4)
        self.assertAlmostEqual(broken["peak_speed"], 9.375)
        self.assertAlmostEqual(broken["peak_acceleration"], 7.216878364870321)
        self.assertFalse(broken["speed_feasible"])
        self.assertFalse(broken["acceleration_feasible"])
        self.assertFalse(broken["feasible"])

        zero = reference_run(0, 2, 0.5, 0.1, 51)
        for field in ("position", "speed", "acceleration", "jerk"):
            self.assertEqual(max(abs(value) for value in zero[field]), 0)
        self.assertEqual(zero["minimum_duration"], 0)
        self.assertEqual(zero["active_constraint"], "none")
        self.assertTrue(zero["feasible"])

    def test_direction_recovery_sampling_isolation_and_resource_bound(self):
        baseline_a = reference_run()
        broken = reference_run(duration=4)
        baseline_b = reference_run()
        self.assertFalse(broken["feasible"])
        self.assertEqual(baseline_a, baseline_b)
        reverse = reference_run(-20)
        for field in ("position", "speed", "acceleration", "jerk"):
            self.assertEqual(
                reverse[field], [-value for value in baseline_a[field]]
            )
        self.assertEqual(reverse["minimum_duration"], baseline_a["minimum_duration"])
        self.assertEqual(reverse["feasible"], baseline_a["feasible"])

        coarse = reference_run(sample_count=51)
        maximum = reference_run(30, 20, 20, 20, 5001)
        self.assertEqual(maximum["sample_count"], 5001)
        self.assertEqual(len(maximum["time"]), 5001)
        for field in ("position", "speed", "acceleration", "jerk"):
            self.assertTrue(all(math.isfinite(value) for value in maximum[field]))
        self.assertEqual(coarse["peak_speed"], baseline_a["peak_speed"])
        self.assertEqual(
            coarse["peak_acceleration"], baseline_a["peak_acceleration"]
        )
        self.assertEqual(coarse["feasible"], baseline_a["feasible"])

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
            "baseline = model(20,8,5,2,501)",
            "targetPositionValuesM = [5 10 15 20 25]",
            "moveDurationValuesSec = [4 6 8 10 12]",
            "changed = model(targetPositionValuesM(k),8,5,2,501)",
            "changed = model(20,moveDurationValuesSec(k),5,2,501)",
            "distanceFeasibleMarkersSec(~distanceFeasible) = NaN",
            "distanceInfeasibleMarkersSec(distanceFeasible) = NaN",
            "durationFeasibleJerkMarkers(~durationFeasible) = NaN",
            "durationInfeasibleJerkMarkers(durationFeasible) = NaN",
            "broken = model(20,4,5,2,501)",
            "recovered = model(20,8,5,2,501)",
            "Position (m)",
            "Speed (m/s)",
            "Acceleration (m/s^2)",
            "Peak jerk (m/s^3)",
            "Constraint utilization (%)",
            "Minimum feasible duration",
            "run_checks;",
        ):
            self.assertIn(marker, experiment)
        self.assertGreaterEqual(experiment.count("figure("), 5)
        self.assertEqual(experiment.count("%% Make one prediction"), 1)

    def test_experiment_clears_cached_checks_before_module_local_dispatch(self):
        experiment = self.read("experiment.m")
        clear_marker = "clear run_checks;"
        dispatch_marker = "\nrun_checks;\n"
        self.assertEqual(experiment.count(clear_marker), 1)
        self.assertEqual(experiment.count(dispatch_marker), 1)
        self.assertLess(
            experiment.index(clear_marker),
            experiment.index(dispatch_marker),
        )

    def test_interactive_has_meaningful_controls_reset_and_immediate_feedback(self):
        interactive = self.read("interactive.m")
        for marker in (
            "function interactive",
            "uifigure(",
            "uiaxes(",
            "uislider(",
            "uispinner(",
            "Target position from zero (m)",
            "Move duration (s)",
            "Speed limit (m/s)",
            "Acceleration limit (m/s^2)",
            "ValueChangingFcn",
            "ValueChangedFcn",
            "ButtonPushedFcn",
            "resetBaseline",
            "redraw(20,8,5,2)",
            "result = modelFunction(targetPosition,duration,speedLimit, ...",
            "zero-distance limit",
            "infeasible: increase duration",
            "obstacle clearance remain separate questions",
            "minimum feasible duration",
            "active minimum-duration constraint",
        ):
            self.assertIn(marker, interactive)
        self.assertGreaterEqual(interactive.count("uiaxes("), 3)

    def test_checks_cover_oracles_limits_malformed_recovery_and_bounds(self):
        checks = self.read("run_checks.m")
        for marker in (
            "isequaln(baselineA,baselineB)",
            "expectedPositionShape",
            "expectedSpeedShape",
            "expectedAccelerationShape",
            "expectedJerkShape",
            "accelerationPeakTau",
            "targetPositionValuesM = [5 10 15 20 25]",
            "moveDurationValuesSec = [4 6 8 10 12]",
            "speedBoundaryDuration",
            "accelerationBoundaryDuration",
            "tieBoundary = model(20,tieDuration,5,tieAccelerationLimit,501)",
            "reverse = model(-20,8,5,2,501)",
            "zeroDistance = model(0,2,0.5,0.1,51)",
            "broken = model(20,4,5,2,501)",
            "recovered = model(20,8,5,2,501)",
            "P21:TargetPositionRange",
            "P21:DurationRange",
            "P21:SpeedLimitRange",
            "P21:AccelerationLimitRange",
            "P21:SampleCountRange",
            "boundedGrid = model(30,20,20,20,5001)",
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
            "P20",
            "quintic",
            "target position",
            "move duration",
            "speed limit",
            "acceleration limit",
            "analytic peaks",
            "minimum feasible duration",
            "1/T^2",
            "smooth is not the same as feasible",
            "20 m",
            "4 s",
            "exactly two sentences",
            "No MATLAB-runtime",
            "plant-tracking",
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
            r"\b(?:quinticpolytraj|cubicpolytraj|trapveltraj|bsplinepolytraj|"
            r"minjerkpolytraj|mstraj|fmincon|quadprog|optimproblem|solve|ode45|"
            r"ode23|sim|ss|tf|lsim|inv|pinv|eig|spline|pchip)\s*\("
        )
        for name in (
            "model.m",
            "experiment.m",
            "interactive.m",
            "run_checks.m",
            "lesson.m",
        ):
            self.assertNotRegex(self.read(name).lower(), opaque_calls)

    def test_learner_frontier_documents_include_permanent_p21_facts(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("./bin/learn start P21", root_readme)
        self.assertIn("P21", start_here)
        p21_row = next(
            line for line in module_index.splitlines() if line.startswith("| P21 |")
        )
        self.assertTrue(p21_row.endswith("| implemented |"))

    def test_readme_path_scope_and_public_cli_state_isolation(self):
        readme = self.read("README.md")
        self.assertIn(
            'moduleFolder = fullfile(pwd,"modules","21-generate-a-feasible-trajectory");',
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
                "current": "P20",
                "completed": {"P19": True},
                "notes": {"P19": "preserve prior note"},
            }
            progress_file.write_text(
                json.dumps(original, indent=2) + "\n", encoding="utf-8"
            )
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"

            checked = subprocess.run(
                [str(fixture / "bin/learn"), "check", "P21"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(
                checked.stdout, "Run in MATLAB: run_module_checks('P21')\n"
            )
            self.assertEqual(json.loads(progress_file.read_text()), original)

            started = subprocess.run(
                [str(fixture / "bin/learn"), "start", "P21"],
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
            self.assertEqual(retained["current"], "P21")
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
                "Target and duration set derivative demand, with speed scaling as "
                "1/T and acceleration as 1/T^2. A smooth move is feasible only "
                "when both analytic peaks fit their declared limits."
            )
            completed = subprocess.run(
                [
                    str(fixture / "bin/learn"),
                    "complete",
                    "P21",
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
            self.assertEqual(retained["completed"], {"P19": True, "P21": True})
            self.assertEqual(retained["notes"]["P19"], "preserve prior note")
            self.assertEqual(retained["notes"]["P21"], teach_back)


if __name__ == "__main__":
    unittest.main()
