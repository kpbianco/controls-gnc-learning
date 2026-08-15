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
    "What inputs, observable effects, and failure modes matter when you build "
    "a State Observer?"
)


@dataclass
class ReferenceResult:
    discrete_a: tuple[tuple[float, float], tuple[float, float]]
    discrete_b: tuple[float, float]
    gain: tuple[float, float]
    error_transition: tuple[tuple[float, float], tuple[float, float]]
    pole: float
    time: list[float]
    command: list[float]
    interference: list[float]
    measurement: list[float]
    innovation: list[float]
    truth: list[tuple[float, float]]
    estimate: list[tuple[float, float]]
    error: list[tuple[float, float]]
    final_error: float
    tail_position_rms: float
    tail_rate_rms: float


def matvec(
    matrix: tuple[tuple[float, float], tuple[float, float]],
    vector: tuple[float, float],
) -> tuple[float, float]:
    return (
        matrix[0][0] * vector[0] + matrix[0][1] * vector[1],
        matrix[1][0] * vector[0] + matrix[1][1] * vector[1],
    )


def reference_model(
    speed: float = 2.0,
    interference_amplitude: float = 0.0,
    sensor_bias: float = 0.0,
    command_amplitude: float = 0.4,
    duration: float = 8.0,
    time_step: float = 0.02,
    initial_estimate: tuple[float, float] = (-0.4, 0.4),
) -> ReferenceResult:
    damping = 0.5
    step_count = round(duration / time_step)
    decay = math.exp(-damping * time_step)
    position_from_rate = (1 - decay) / damping
    position_from_acceleration = (time_step - position_from_rate) / damping
    discrete_a = ((1.0, position_from_rate), (0.0, decay))
    discrete_b = (position_from_acceleration, position_from_rate)
    pole = math.exp(-speed * time_step)
    gain = (
        1 + decay - 2 * pole,
        (pole - decay) ** 2 / position_from_rate,
    )
    error_transition = (
        (1 - gain[0], position_from_rate),
        (-gain[1], decay),
    )
    time = [index * time_step for index in range(step_count + 1)]
    command = [command_amplitude if value >= 0.5 else 0.0 for value in time]
    interference = [
        interference_amplitude * math.sin(2 * math.pi * 2.5 * value)
        for value in time
    ]
    truth = [(0.8, -0.3)]
    estimate = [initial_estimate]
    measurement: list[float] = []
    innovation: list[float] = []
    for index in range(step_count + 1):
        measured = truth[index][0] + sensor_bias + interference[index]
        residual = measured - estimate[index][0]
        measurement.append(measured)
        innovation.append(residual)
        if index == step_count:
            continue
        predicted_truth = matvec(discrete_a, truth[index])
        predicted_estimate = matvec(discrete_a, estimate[index])
        truth.append(
            (
                predicted_truth[0] + discrete_b[0] * command[index],
                predicted_truth[1] + discrete_b[1] * command[index],
            )
        )
        estimate.append(
            (
                predicted_estimate[0]
                + discrete_b[0] * command[index]
                + gain[0] * residual,
                predicted_estimate[1]
                + discrete_b[1] * command[index]
                + gain[1] * residual,
            )
        )
    error = [
        (actual[0] - inferred[0], actual[1] - inferred[1])
        for actual, inferred in zip(truth, estimate)
    ]
    tail = [value for instant, value in zip(time, error) if instant >= duration - 1]
    tail_position_rms = math.sqrt(sum(value[0] ** 2 for value in tail) / len(tail))
    tail_rate_rms = math.sqrt(sum(value[1] ** 2 for value in tail) / len(tail))
    final_error = math.hypot(error[-1][0], error[-1][1])
    return ReferenceResult(
        discrete_a=discrete_a,
        discrete_b=discrete_b,
        gain=gain,
        error_transition=error_transition,
        pole=pole,
        time=time,
        command=command,
        interference=interference,
        measurement=measurement,
        innovation=innovation,
        truth=truth,
        estimate=estimate,
        error=error,
        final_error=final_error,
        tail_position_rms=tail_position_rms,
        tail_rate_rms=tail_rate_rms,
    )


class P15ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P15"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 15)
        self.assertEqual(self.module["title"], "Build a State Observer")
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["phase"], 4)
        self.assertEqual(self.module["phase_title"], "State-space control")
        self.assertEqual(self.module["folder"], "modules/15-build-a-state-observer")
        self.assertEqual(self.module["prerequisites"], ["P14"])
        self.assertEqual(self.module["implementation_batch"], "P15")
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

    def test_model_is_transparent_pure_and_resource_bounded(self):
        model = self.read("model.m")
        for formula in (
            "continuousA = [0 1;0 -dampingPerSec]",
            "continuousB = [0;1]",
            "measurementRow = [1 0]",
            "decay = exp(-dampingPerSec*timeStepSec)",
            "discreteA = [1 positionFromRateSec;0 decay]",
            "discreteB = [positionFromAccelerationSec2;positionFromRateSec]",
            "desiredErrorPole = exp(-observerPoleSpeedPerSec*timeStepSec)",
            "observerGainPosition = 1+decay-2*desiredErrorPole",
            "(desiredErrorPole-decay)^2/positionFromRateSec",
            "normalizedObserverGain = [ ...",
            "errorTransition = discreteA-observerGain*measurementRow",
            "estimatedState(:,k+1) = discreteA*estimatedState(:,k)+ ...",
            "observerGain*innovationM(k)",
        ):
            self.assertIn(formula, model)
        for validation in (
            "maximumStepCount = 5000",
            "P15:ObserverSpeedRange",
            "P15:InterferenceRange",
            "P15:SensorBiasRange",
            "P15:CommandRange",
            "P15:DurationRange",
            "P15:DisplayResolution",
            "P15:GridAlignment",
            "P15:TooManySteps",
            "P15:InitialEstimatePositionRange",
            "P15:InitialEstimateRateRange",
        ):
            self.assertIn(validation, model)
        self.assertLess(
            model.index("stepCount > maximumStepCount"),
            model.index("trueState = zeros(2,sampleCount)"),
        )
        self.assertNotRegex(
            model.lower(),
            r"\b(?:plot|figure|uifigure|uiaxes|uislider|uidropdown|rng|random)\s*\(",
        )

    def test_independent_baseline_matrices_gain_and_pole_invariants(self):
        result = reference_model()
        self.assertAlmostEqual(result.discrete_a[1][1], 0.9900498337491681)
        self.assertAlmostEqual(result.discrete_a[0][1], 0.0199003325016638)
        self.assertAlmostEqual(result.discrete_b[0], 0.0001993349966724)
        self.assertAlmostEqual(result.discrete_b[1], 0.0199003325016638)
        self.assertAlmostEqual(result.pole, 0.9607894391523232)
        self.assertAlmostEqual(result.gain[0], 0.06847095544452175)
        self.assertAlmostEqual(result.gain[1], 0.04302293400833835)
        transition = result.error_transition
        trace = transition[0][0] + transition[1][1]
        determinant = transition[0][0] * transition[1][1] - transition[0][1] * transition[1][0]
        self.assertAlmostEqual(trace, 2 * result.pole)
        self.assertAlmostEqual(determinant, result.pole**2)
        shifted = (
            (transition[0][0] - result.pole, transition[0][1]),
            (transition[1][0], transition[1][1] - result.pole),
        )
        squared = (
            shifted[0][0] * shifted[0][0] + shifted[0][1] * shifted[1][0],
            shifted[0][0] * shifted[0][1] + shifted[0][1] * shifted[1][1],
            shifted[1][0] * shifted[0][0] + shifted[1][1] * shifted[1][0],
            shifted[1][0] * shifted[0][1] + shifted[1][1] * shifted[1][1],
        )
        self.assertLess(max(abs(value) for value in squared), 2e-16)

    def test_independent_state_observer_and_error_recurrences(self):
        result = reference_model()
        for index in range(len(result.time) - 1):
            predicted_truth = matvec(result.discrete_a, result.truth[index])
            predicted_estimate = matvec(result.discrete_a, result.estimate[index])
            expected_truth = (
                predicted_truth[0] + result.discrete_b[0] * result.command[index],
                predicted_truth[1] + result.discrete_b[1] * result.command[index],
            )
            expected_estimate = (
                predicted_estimate[0]
                + result.discrete_b[0] * result.command[index]
                + result.gain[0] * result.innovation[index],
                predicted_estimate[1]
                + result.discrete_b[1] * result.command[index]
                + result.gain[1] * result.innovation[index],
            )
            expected_error = matvec(result.error_transition, result.error[index])
            for actual, expected in zip(result.truth[index + 1], expected_truth):
                self.assertAlmostEqual(actual, expected)
            for actual, expected in zip(result.estimate[index + 1], expected_estimate):
                self.assertAlmostEqual(actual, expected)
            for actual, expected in zip(result.error[index + 1], expected_error):
                self.assertAlmostEqual(actual, expected, places=13)
        self.assertAlmostEqual(result.final_error, 4.077503108033036e-06)
        self.assertAlmostEqual(result.tail_position_rms, 7.1789032053976655e-06)
        self.assertAlmostEqual(result.tail_rate_rms, 1.1581117653879921e-05)

    def test_two_sweeps_are_independent_and_have_expected_limits(self):
        speeds = [1.0, 2.0, 3.0, 4.0]
        speed_runs = [reference_model(speed=value) for value in speeds]
        self.assertEqual(
            [run.pole for run in speed_runs],
            sorted((run.pole for run in speed_runs), reverse=True),
        )
        self.assertEqual(
            [run.final_error for run in speed_runs],
            sorted((run.final_error for run in speed_runs), reverse=True),
        )
        self.assertTrue(all(run.interference == [0.0] * 401 for run in speed_runs))
        for run in speed_runs:
            self.assertEqual(run.command, speed_runs[0].command)
            self.assertEqual(run.truth, speed_runs[0].truth)

        amplitudes = [0.0, 0.005, 0.02, 0.05]
        interference_runs = [
            reference_model(interference_amplitude=value) for value in amplitudes
        ]
        self.assertEqual(
            [run.tail_position_rms for run in interference_runs],
            sorted(run.tail_position_rms for run in interference_runs),
        )
        self.assertEqual(
            [run.tail_rate_rms for run in interference_runs],
            sorted(run.tail_rate_rms for run in interference_runs),
        )
        clean = interference_runs[0]
        unit_impacts: list[list[tuple[float, float]]] = []
        for amplitude, run in zip(amplitudes[1:], interference_runs[1:]):
            self.assertEqual(run.truth, clean.truth)
            self.assertEqual(run.command, clean.command)
            unit_impacts.append(
                [
                    (
                        (changed[0] - base[0]) / amplitude,
                        (changed[1] - base[1]) / amplitude,
                    )
                    for changed, base in zip(run.estimate, clean.estimate)
                ]
            )
        for comparison in unit_impacts[1:]:
            for actual, expected in zip(comparison, unit_impacts[0]):
                self.assertAlmostEqual(actual[0], expected[0], places=11)
                self.assertAlmostEqual(actual[1], expected[1], places=11)

    def test_limiting_broken_case_recovery_and_isolation(self):
        exact = reference_model(initial_estimate=(0.8, -0.3))
        self.assertTrue(all(error == (0.0, 0.0) for error in exact.error))
        self.assertTrue(all(value == 0.0 for value in exact.innovation))
        commanded = reference_model(command_amplitude=0.4)
        command_free = reference_model(command_amplitude=0.0)
        for actual, expected in zip(commanded.error, command_free.error):
            self.assertAlmostEqual(actual[0], expected[0], places=13)
            self.assertAlmostEqual(actual[1], expected[1], places=13)

        broken = reference_model(sensor_bias=0.15)
        recovered = reference_model(sensor_bias=0.0)
        self.assertEqual(broken.truth, recovered.truth)
        self.assertEqual(broken.command, recovered.command)
        for broken_measurement, good_measurement in zip(
            broken.measurement, recovered.measurement
        ):
            self.assertAlmostEqual(broken_measurement - good_measurement, 0.15)
        self.assertAlmostEqual(broken.error[-1][0], -0.15, delta=1e-4)
        self.assertAlmostEqual(broken.error[-1][1], 0.0, delta=1e-4)
        self.assertAlmostEqual(broken.innovation[-1], 0.0, delta=1e-4)
        self.assertGreater(broken.tail_position_rms, 0.14)
        self.assertLess(recovered.final_error, 5e-6)

    def test_independent_maximum_accepted_grid_is_finite(self):
        bounded = reference_model(duration=10.0, time_step=0.002)
        self.assertEqual(len(bounded.time), 5001)
        self.assertEqual(len(bounded.truth), 5001)
        self.assertEqual(len(bounded.estimate), 5001)
        self.assertTrue(
            all(math.isfinite(value) for state in bounded.truth for value in state)
        )
        self.assertTrue(
            all(math.isfinite(value) for state in bounded.estimate for value in state)
        )
        self.assertLess(bounded.final_error, 1e-7)

    def test_experiment_has_learning_flow_labels_metrics_sweeps_and_broken_case(self):
        experiment = self.read("experiment.m")
        section_titles = re.findall(r"^%% (.+)$", experiment, flags=re.MULTILINE)
        self.assertGreaterEqual(len(section_titles), 11)
        markers = (
            "%% Read -",
            "%% Visualize baseline",
            "%% Changed view",
            "%% Sweep 1",
            "%% Read and explain sweep 1",
            "%% Sweep 2",
            "%% Read and explain sweep 2",
            "%% Broken case",
            "%% Read and explain the broken mechanism",
            "%% Check and teach back",
            "observerPoleSpeedsPerSec = [1 2 3 4]",
            "interferenceAmplitudesM = [0 0.005 0.02 0.05]",
            "broken = model(2,0,0.15,0.4,8,0.02)",
            "recovered = model(2,0,0,0.4,8,0.02)",
        )
        for marker in markers:
            self.assertIn(marker, experiment)
        for earlier, later in zip(markers[:10], markers[1:10]):
            self.assertLess(experiment.index(earlier), experiment.index(later))
        for unit in (
            "Time (s)",
            "Position (m)",
            "Rate (m/s)",
            "Innovation (m)",
            "Observer pole speed (1/s)",
            "Measurement interference amplitude (m)",
            "Normalized state-error norm",
        ):
            self.assertIn(unit, experiment)
        self.assertIn("final normalized error", experiment)
        self.assertIn("last-second position RMS", experiment)

    def test_interactive_exposes_meaningful_controls_reset_and_immediate_feedback(self):
        interactive = self.read("interactive.m")
        for marker in (
            "uifigure(",
            "uiaxes(",
            "uislider(",
            "uispinner(",
            "uidropdown(",
            "Observer pole speed (1/s)",
            "Measurement interference amplitude (m)",
            "+0.15 m bias (broken)",
            "ValueChangingFcn",
            "ValueChangedFcn",
            "ButtonPushedFcn",
            "resetBaseline",
            "redraw(2,0,'Calibrated sensor')",
            "result = modelFunction(observerPoleSpeedPerSec, ...",
            "quiet innovation, biased position",
            "measurement ripple enters both estimates",
        ):
            self.assertIn(marker, interactive)

    def test_checks_cover_invariants_malformed_inputs_recovery_and_bounds(self):
        checks = self.read("run_checks.m")
        for marker in (
            "isequaln(baselineA,baselineB)",
            "expectedA = [1 expectedPositionFromRate;0 expectedDecay]",
            "expectedGain = [1+expectedDecay-2*expectedPole; ...",
            "errorTransitionTrace-2*expectedPole",
            "errorTransitionDeterminant-expectedPole^2",
            "jordanResidual",
            "expectedError = ...",
            "exactStart = model(2,0,0,0.4,8,0.02,0.8,-0.3)",
            "commandFree = model(2,0,0,0,8,0.02)",
            "observerPoleSpeedsPerSec = [1 2 3 4]",
            "interferenceAmplitudesM = [0 0.005 0.02 0.05]",
            "broken = model(2,0,0.15,0.4,8,0.02)",
            "recovered = model(2,0,0,0.4,8,0.02)",
            "P15:ObserverSpeedRange",
            "P15:InterferenceRange",
            "P15:SensorBiasRange",
            "P15:CommandRange",
            "P15:DurationRange",
            "P15:DisplayResolution",
            "P15:GridAlignment",
            "P15:TooManySteps",
            "boundedGrid = model(2,0,0,0.4,10,0.002)",
            "assertAnyError",
            "assertErrorId",
        ):
            self.assertIn(marker, checks)

    def test_tutor_text_connects_prerequisite_interpretation_and_claim_boundary(self):
        readme = self.read("README.md")
        lesson = self.read("lesson.md")
        walkthrough = self.read("walkthrough.md")
        checks = self.read("checks.md")
        combined = "\n".join((readme, lesson, walkthrough, checks))
        for marker in (
            QUESTION,
            "P14",
            "observab",
            "known input",
            "innovation",
            "sensor bias",
            "P16",
            "two sentences",
            "MATLAB-runtime",
            "No MATLAB-runtime",
        ):
            self.assertIn(marker.lower(), combined.lower())
        opaque_calls = r"\b(?:place|acker|obsv|rank|gram|c2d|ss|lsim|pinv|expm|ode45|kalman)\s*\("
        for name in (
            "model.m",
            "experiment.m",
            "interactive.m",
            "run_checks.m",
            "lesson.m",
        ):
            self.assertNotRegex(self.read(name).lower(), opaque_calls)
        for placeholder in ("scaffolded", "placeholder", "todo"):
            self.assertNotIn(placeholder, combined.lower())

    def test_readme_scopes_the_interactive_module_path(self):
        readme = self.read("README.md")
        add_path = 'addpath(moduleFolder,"-begin");'
        remove_path = "rmpath(moduleFolder);"
        clear_path = "clear moduleFolder"
        self.assertIn(
            'moduleFolder = fullfile(pwd,"modules","15-build-a-state-observer");',
            readme,
        )
        self.assertIn(add_path, readme)
        self.assertEqual(readme.count(remove_path), 2)
        self.assertIn("catch exception", readme)
        self.assertIn("rethrow(exception)", readme)
        self.assertIn(clear_path, readme)
        interactive_call = "\n    interactive\n"
        self.assertLess(readme.index(add_path), readme.index(interactive_call))
        self.assertLess(readme.index(interactive_call), readme.rindex(remove_path))
        self.assertLess(readme.rindex(remove_path), readme.index(clear_path))

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
                [str(fixture / "bin/learn"), "check", "P15"],
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
                checked.stdout, "Run in MATLAB: run_module_checks('P15')\n"
            )
            self.assertEqual(progress_file.read_bytes(), retained_progress)

    def test_public_start_then_continue_retains_p15_in_isolated_learner_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            shutil.copytree(ROOT / "bin", fixture / "bin")
            shutil.copytree(ROOT / "curriculum", fixture / "curriculum")
            shutil.copytree(self.folder, fixture / self.module["folder"])
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            started = subprocess.run(
                [str(fixture / "bin/learn"), "start", "P15"],
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
                "P15 — Build a State Observer",
                "Status: implemented",
                f"Guiding question: {QUESTION}",
                "Folder: modules/15-build-a-state-observer",
                "launch_lesson('P15')",
                "modules/15-build-a-state-observer/checks.md",
            ):
                self.assertIn(expected, started.stdout)
            progress = json.loads(
                (fixture / ".learning/progress.json").read_text(encoding="utf-8")
            )
            self.assertEqual(progress["current"], "P15")
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

    def test_public_start_updates_only_current_and_preserves_learner_records(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            shutil.copytree(ROOT / "bin", fixture / "bin")
            shutil.copytree(ROOT / "curriculum", fixture / "curriculum")
            shutil.copytree(self.folder, fixture / self.module["folder"])
            progress_file = fixture / ".learning/progress.json"
            progress_file.parent.mkdir(parents=True)
            original = {
                "current": "P12",
                "completed": {"P11": True},
                "notes": {"P11": "retain this note"},
            }
            progress_file.write_text(
                json.dumps(original, indent=2) + "\n", encoding="utf-8"
            )
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            started = subprocess.run(
                [str(fixture / "bin/learn"), "start", "P15"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertEqual(started.stderr, "")
            retained = json.loads(progress_file.read_text(encoding="utf-8"))
            self.assertEqual(retained["current"], "P15")
            self.assertEqual(retained["completed"], original["completed"])
            self.assertEqual(retained["notes"], original["notes"])


if __name__ == "__main__":
    unittest.main()
