from __future__ import annotations

from dataclasses import dataclass
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
    "What inputs, observable effects, and failure modes matter when you test "
    "Observability?"
)


@dataclass
class ReferenceResult:
    discrete_a: tuple[tuple[float, float], tuple[float, float]]
    observation: list[tuple[float, float]]
    gramian: tuple[float, float, float]
    minimum_singular_value: float
    condition_number: float
    inverse_noise_gain: float
    rank: int
    unique: bool
    state: list[tuple[float, float]]
    alternative_state: list[tuple[float, float]]
    output: list[float]
    alternative_output: list[float]
    estimate: tuple[float, float]
    state_error: float
    residual: float
    separation_rms: float


def matvec(
    matrix: tuple[tuple[float, float], tuple[float, float]],
    vector: tuple[float, float],
) -> tuple[float, float]:
    return (
        matrix[0][0] * vector[0] + matrix[0][1] * vector[1],
        matrix[1][0] * vector[0] + matrix[1][1] * vector[1],
    )


def reference_model(
    sensor_gain: float = 1.0,
    window: float = 2.0,
    time_step: float = 0.05,
    measure_position: bool = True,
    initial_state: tuple[float, float] = (0.8, 0.6),
) -> ReferenceResult:
    damping = 0.5
    step_count = round(window / time_step)
    decay = math.exp(-damping * time_step)
    discrete_a = ((1.0, (1 - decay) / damping), (0.0, decay))
    observation = []
    for index in range(step_count + 1):
        if measure_position:
            observation.append(
                (sensor_gain, sensor_gain * (1 - decay**index) / damping)
            )
        else:
            observation.append((0.0, sensor_gain * decay**index))

    g11 = sum(row[0] ** 2 for row in observation)
    g12 = sum(row[0] * row[1] for row in observation)
    g22 = sum(row[1] ** 2 for row in observation)
    trace = g11 + g22
    spread = math.hypot(g11 - g22, 2 * g12)
    lambda_maximum = max(0.0, 0.5 * (trace + spread))
    lambda_minimum = max(0.0, 0.5 * (trace - spread))
    singular_maximum = math.sqrt(lambda_maximum)
    singular_minimum = math.sqrt(lambda_minimum)
    tolerance = 128 * math.ulp(max(trace, 1.0))
    if lambda_maximum <= tolerance:
        rank = 0
    elif lambda_minimum <= tolerance:
        rank = 1
    else:
        rank = 2

    alternative_initial = (initial_state[0] + 1.0, initial_state[1])

    def simulate(start: tuple[float, float]) -> list[tuple[float, float]]:
        result = [start]
        for _ in range(step_count):
            result.append(matvec(discrete_a, result[-1]))
        return result

    state = simulate(initial_state)
    alternative_state = simulate(alternative_initial)
    output = [
        row[0] * initial_state[0] + row[1] * initial_state[1]
        for row in observation
    ]
    alternative_output = [
        row[0] * alternative_initial[0] + row[1] * alternative_initial[1]
        for row in observation
    ]
    differences = [
        alternative - actual
        for alternative, actual in zip(alternative_output, output)
    ]
    separation_rms = math.sqrt(
        sum(value * value for value in differences) / len(differences)
    )
    if rank == 2:
        determinant = g11 * g22 - g12 * g12
        information = (
            sum(row[0] * value for row, value in zip(observation, output)),
            sum(row[1] * value for row, value in zip(observation, output)),
        )
        estimate = (
            (g22 * information[0] - g12 * information[1]) / determinant,
            (-g12 * information[0] + g11 * information[1]) / determinant,
        )
        reconstructed = [
            row[0] * estimate[0] + row[1] * estimate[1]
            for row in observation
        ]
        residual = math.sqrt(
            sum((actual - rebuilt) ** 2 for actual, rebuilt in zip(output, reconstructed))
        )
        state_error = math.hypot(
            estimate[0] - initial_state[0], estimate[1] - initial_state[1]
        )
    else:
        estimate = (math.nan, math.nan)
        residual = math.inf
        state_error = math.inf
    return ReferenceResult(
        discrete_a=discrete_a,
        observation=observation,
        gramian=(g11, g12, g22),
        minimum_singular_value=singular_minimum,
        condition_number=(
            singular_maximum / singular_minimum
            if singular_minimum
            else math.inf
        ),
        inverse_noise_gain=(1 / singular_minimum if singular_minimum else math.inf),
        rank=rank,
        unique=rank == 2,
        state=state,
        alternative_state=alternative_state,
        output=output,
        alternative_output=alternative_output,
        estimate=estimate,
        state_error=state_error,
        residual=residual,
        separation_rms=separation_rms,
    )


class P14ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P14"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 14)
        self.assertEqual(self.module["title"], "Test Observability")
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["phase"], 4)
        self.assertEqual(self.module["phase_title"], "State-space control")
        self.assertEqual(self.module["prerequisites"], ["P13"])
        self.assertEqual(self.module["implementation_batch"], "P14")
        self.assertEqual(self.module["status"], "implemented")
        self.assertEqual(self.module["evidence_level"], "simulated")

    def test_public_check_route_resolves_p14(self):
        checked = subprocess.run(
            [str(ROOT / "bin/learn"), "check", "P14"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertEqual(checked.stdout, "Run in MATLAB: run_module_checks('P14')\n")

    def test_public_check_route_preserves_existing_learner_progress(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            shutil.copytree(ROOT / "bin", fixture / "bin")
            shutil.copytree(ROOT / "curriculum", fixture / "curriculum")
            shutil.copytree(self.folder, fixture / self.module["folder"])
            progress_file = fixture / ".learning/progress.json"
            progress_file.parent.mkdir(parents=True)
            retained_progress = (
                b'{\n  "current": "P12",\n  "completed": {"P11": true},\n'
                b'  "notes": {"P11": "retain this note"}\n}\n'
            )
            progress_file.write_bytes(retained_progress)
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"

            checked = subprocess.run(
                [str(fixture / "bin/learn"), "check", "P14"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )

            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(checked.stderr, "")
            self.assertEqual(
                checked.stdout,
                "Run in MATLAB: run_module_checks('P14')\n",
            )
            self.assertEqual(progress_file.read_bytes(), retained_progress)

    def test_public_start_then_continue_retains_p14_in_isolated_learner_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            shutil.copytree(ROOT / "bin", fixture / "bin")
            shutil.copytree(ROOT / "curriculum", fixture / "curriculum")
            shutil.copytree(self.folder, fixture / self.module["folder"])
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"

            started = subprocess.run(
                [str(fixture / "bin/learn"), "start", "P14"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertEqual(started.stderr, "")
            for expected in (
                "P14 — Test Observability",
                "Status: implemented",
                f"Guiding question: {QUESTION}",
                "Folder: modules/14-test-observability",
                "launch_lesson('P14')",
                "modules/14-test-observability/checks.md",
            ):
                self.assertIn(expected, started.stdout)

            progress = json.loads(
                (fixture / ".learning/progress.json").read_text(encoding="utf-8")
            )
            self.assertEqual(progress["current"], "P14")
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
            self.assertEqual(continued.stderr, "")
            self.assertEqual(continued.stdout, started.stdout)

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

    def test_model_is_transparent_pure_and_resource_bounded(self):
        model = self.read("model.m")
        for formula in (
            "continuousA = [0 1;0 -dampingPerSec]",
            "continuousC = [sensorGain 0]",
            "continuousC = [0 sensorGain]",
            "[continuousC;continuousC*continuousA]",
            "decay = exp(-dampingPerSec*timeStepSec)",
            "discreteA = [1 positionFromRate;0 decay]",
            "observationMatrix(k,:) = continuousC*stateTransition",
            "scaledObservationMatrix = observationMatrix*physicalStateFromScaledState",
            "gramian = scaledObservationMatrix.'*scaledObservationMatrix",
            "estimatedScaledInitialState = [ ...",
            "stateTrajectory(:,k+1) = discreteA*stateTrajectory(:,k)",
        ):
            self.assertIn(formula, model)
        for validation in (
            "maximumStepCount = 5000",
            "P14:SensorGainRange",
            "P14:WindowRange",
            "P14:DisplayResolution",
            "P14:InitialPositionRange",
            "P14:InitialRateRange",
            "P14:TooManySteps",
            "P14:GridAlignment",
        ):
            self.assertIn(validation, model)
        self.assertLess(
            model.index("stepCount > maximumStepCount"),
            model.index("observationMatrix = zeros(sampleCount,2)"),
        )
        self.assertNotRegex(
            model.lower(),
            r"\b(?:plot|figure|uifigure|uiaxes|uislider|uidropdown|rng|random)\s*\(",
        )

    def test_independent_baseline_transition_reconstruction_and_metrics(self):
        result = reference_model()
        decay = math.exp(-0.025)
        self.assertAlmostEqual(result.discrete_a[0][1], 2 * (1 - decay))
        self.assertAlmostEqual(result.discrete_a[1][1], decay)
        self.assertEqual(result.rank, 2)
        self.assertTrue(result.unique)
        self.assertAlmostEqual(result.minimum_singular_value, 1.8873067184396513)
        self.assertAlmostEqual(result.condition_number, 4.276289080641569)
        self.assertAlmostEqual(result.inverse_noise_gain, 0.529855582152942)
        self.assertLess(result.state_error, 2e-14)
        self.assertLess(result.residual, 5e-14)
        self.assertAlmostEqual(result.separation_rms, 1.0)
        self.assertAlmostEqual(result.estimate[0], 0.8)
        self.assertAlmostEqual(result.estimate[1], 0.6)

    def test_independent_observation_rows_gramian_and_state_recurrence(self):
        result = reference_model()
        decay = math.exp(-0.025)
        self.assertEqual(len(result.observation), 41)
        for index, row in enumerate(result.observation):
            self.assertAlmostEqual(row[0], 1.0)
            self.assertAlmostEqual(row[1], 2 * (1 - decay**index))
        g11, g12, g22 = result.gramian
        self.assertAlmostEqual(g11, 41.0)
        self.assertAlmostEqual(g12, 30.05984204431758)
        self.assertAlmostEqual(g22, 27.697626563001304)
        for current, following in zip(result.state, result.state[1:]):
            expected = matvec(result.discrete_a, current)
            self.assertAlmostEqual(following[0], expected[0])
            self.assertAlmostEqual(following[1], expected[1])
        for row, output in zip(result.observation, result.output):
            self.assertAlmostEqual(output, 0.8 * row[0] + 0.6 * row[1])

    def test_two_sweeps_are_independent_and_have_expected_limits(self):
        baseline = reference_model()
        gains = [0.25, 0.5, 1.0, 1.5, 2.0]
        gain_results = [reference_model(sensor_gain=gain) for gain in gains]
        self.assertTrue(all(result.rank == 2 for result in gain_results))
        for gain, result in zip(gains, gain_results):
            self.assertAlmostEqual(
                result.minimum_singular_value,
                gain * baseline.minimum_singular_value,
            )
            self.assertAlmostEqual(result.separation_rms, gain)
            self.assertAlmostEqual(
                result.inverse_noise_gain, baseline.inverse_noise_gain / gain
            )
        windows = [0.1, 0.25, 0.5, 1.0, 2.0, 4.0]
        window_results = [reference_model(window=window) for window in windows]
        self.assertTrue(all(result.rank == 2 for result in window_results))
        self.assertEqual(
            [result.minimum_singular_value for result in window_results],
            sorted(result.minimum_singular_value for result in window_results),
        )
        self.assertEqual(
            [result.inverse_noise_gain for result in window_results],
            sorted(
                (result.inverse_noise_gain for result in window_results),
                reverse=True,
            ),
        )
        self.assertGreater(
            window_results[0].inverse_noise_gain,
            8 * window_results[4].inverse_noise_gain,
        )

    def test_broken_zero_sensor_short_window_and_recovery_are_isolated(self):
        broken = reference_model(measure_position=False)
        recovered = reference_model(measure_position=True)
        no_sensor = reference_model(sensor_gain=0)
        short = reference_model(window=0.1)
        zero_rate = reference_model(initial_state=(0.8, 0.0))
        self.assertEqual(broken.rank, 1)
        self.assertFalse(broken.unique)
        self.assertEqual(broken.output, broken.alternative_output)
        self.assertTrue(math.isnan(broken.estimate[0]))
        self.assertTrue(math.isinf(broken.state_error))
        self.assertTrue(
            all(
                abs((alternative[0] - actual[0]) - 1.0) < 2e-15
                for actual, alternative in zip(
                    broken.state, broken.alternative_state
                )
            )
        )
        self.assertEqual(
            [state[1] for state in broken.state],
            [state[1] for state in broken.alternative_state],
        )
        self.assertEqual(no_sensor.rank, 0)
        self.assertEqual(no_sensor.output, [0.0] * 41)
        self.assertEqual(short.rank, 2)
        self.assertEqual(len(short.output), 3)
        self.assertLess(short.minimum_singular_value, recovered.minimum_singular_value)
        self.assertTrue(all(state == (0.8, 0.0) for state in zero_rate.state))
        self.assertEqual(zero_rate.rank, 2)
        self.assertLess(recovered.state_error, 2e-14)

    def test_independent_maximum_accepted_grid_is_finite(self):
        bounded = reference_model(window=5.0, time_step=0.001)
        self.assertEqual(len(bounded.output), 5001)
        self.assertEqual(len(bounded.state), 5001)
        self.assertEqual(bounded.rank, 2)
        self.assertTrue(all(math.isfinite(value) for value in bounded.output))
        self.assertTrue(
            all(
                math.isfinite(position) and math.isfinite(rate)
                for position, rate in bounded.state
            )
        )
        self.assertLess(bounded.state_error, 2e-13)

    def test_experiment_has_learning_flow_labels_metrics_sweeps_and_broken_case(self):
        experiment = self.read("experiment.m")
        section_titles = re.findall(r"^%% (.+)$", experiment, flags=re.MULTILINE)
        self.assertGreaterEqual(len(section_titles), 10)
        for marker in (
            "%% Read -",
            "%% Visualize baseline",
            "%% Changed view",
            "%% Sweep 1",
            "%% Read and explain sweep 1",
            "%% Sweep 2",
            "%% Read and explain sweep 2",
            "%% Broken case",
            "%% Check and teach back",
            "sensorGains = [0.25 0.5 1 1.5 2]",
            "observationWindowsSec = [0.1 0.25 0.5 1 2 4]",
            "broken = model(1,2,0.05,false)",
            "recovered = model(1,2,0.05,true)",
        ):
            self.assertIn(marker, experiment)
        for unit in (
            "Time (s)",
            "Position (m)",
            "Rate (m/s)",
            "Sensor output (sensor unit)",
            "Position-sensor gain (sensor unit/m)",
            "Observation window (s)",
            "Scaled minimum singular value (sensor unit)",
        ):
            self.assertIn(unit, experiment)
        self.assertIn("state error %.3g", experiment)
        self.assertIn("output separation RMS", experiment)

    def test_interactive_exposes_meaningful_controls_reset_and_immediate_feedback(self):
        interactive = self.read("interactive.m")
        for marker in (
            "uifigure(",
            "uiaxes(",
            "uislider(",
            "uispinner(",
            "uidropdown(",
            "Sensor sensitivity (normalized output/state)",
            "Observation window (s)",
            "Rate-only measurement (broken)",
            "ValueChangingFcn",
            "ValueChangedFcn",
            "ButtonPushedFcn",
            "resetBaseline",
            "redraw(1,2,'Position measurement')",
            "round(observationWindowSec/0.05)*0.05",
            "result = modelFunction(sensorGain,observationWindowSec,0.05, ...",
            "initial position not unique",
            "inverse noise gain N/A",
            "full rank, weakly separated",
        ):
            self.assertIn(marker, interactive)

    def test_checks_cover_invariants_malformed_inputs_recovery_and_bounds(self):
        checks = self.read("run_checks.m")
        for marker in (
            "isequaln(baselineA,baselineB)",
            "expectedContinuousRows",
            "expectedAd",
            "expectedGramian",
            "reconstructedHistory",
            "sensorGains = [0.25 0.5 1 1.5 2]",
            "observationWindowsSec = [0.1 0.25 0.5 1 2 4]",
            "broken = model(1,2,0.05,false)",
            "recovered = model(1,2,0.05,true)",
            "noSensor = model(0,2,0.05,true)",
            "all(isnan(broken.estimatedInitialPhysicalState))",
            "model(NaN,2,0.05,true)",
            "model([1 2],2,0.05,true)",
            "model(1+1i,2,0.05,true)",
            "P14:GridAlignment",
            "P14:TooManySteps",
            "boundedGrid = model(1,5,0.001,true)",
        ):
            self.assertIn(marker, checks)

    def test_tutor_text_connects_prerequisite_interpretation_and_claim_boundary(self):
        readme = self.read("README.md")
        lesson = self.read("lesson.md")
        walkthrough = self.read("walkthrough.md")
        checks = self.read("checks.md")
        combined = "\n".join((readme, lesson, walkthrough, checks))
        self.assertIn(QUESTION, combined)
        self.assertIn("P13", lesson)
        self.assertIn("two sentences", combined.lower())
        self.assertIn("coordinate-scaled", readme)
        self.assertIn("Full rank does not mean", lesson)
        for excluded_claim in (
            "No MATLAB-runtime",
            "UI",
            "MATLAB numerical-",
            "bench",
            "HIL",
            "field",
            "production",
        ):
            self.assertIn(excluded_claim, combined)
        self.assertNotIn("syntax-first", combined.lower())

    def test_no_placeholder_or_opaque_control_toolbox_path(self):
        combined = "\n".join(
            self.read(name)
            for name in ("model.m", "experiment.m", "interactive.m", "run_checks.m")
        )
        self.assertNotIn("scaffolded", combined.lower())
        self.assertNotIn("not implemented", combined.lower())
        self.assertNotRegex(
            combined.lower(),
            r"\b(?:obsv|rank|gram|c2d|ss|lsim|pinv|expm|ode45)\s*\(",
        )


if __name__ == "__main__":
    unittest.main()
