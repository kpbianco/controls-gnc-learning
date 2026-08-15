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
    "What inputs, observable effects, and failure modes matter when you use "
    "Feedforward and Feedback Together?"
)
GAIN = (1.9644942427723904, 1.7703588392280174)


def matrix_vector(matrix: tuple[tuple[float, float], tuple[float, float]], vector: list[float]) -> list[float]:
    return [
        matrix[row][0] * vector[0] + matrix[row][1] * vector[1]
        for row in range(2)
    ]


def two_state_poles(matrix: tuple[tuple[float, float], tuple[float, float]]) -> tuple[complex, complex]:
    trace = matrix[0][0] + matrix[1][1]
    determinant = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    root = complex(trace * trace - 4 * determinant, 0) ** 0.5
    return ((trace + root) / 2, (trace - root) / 2)


@dataclass
class ReferenceResult:
    discrete_a: tuple[tuple[float, float], tuple[float, float]]
    discrete_b: tuple[float, float]
    error_a: tuple[tuple[float, float], tuple[float, float]]
    poles: tuple[complex, complex]
    time: list[float]
    reference: list[list[float]]
    actual: list[list[float]]
    error: list[list[float]]
    plan: list[float]
    disturbance: list[float]
    feedforward: list[float]
    feedback: list[float]
    total: list[float]
    position_ise: float
    rate_ise: float
    position_rmse: float
    feedforward_effort: float
    feedback_effort: float
    total_effort: float
    maximum_position_error: float
    maximum_feedback: float
    maximum_total: float
    recovery_time: float


def reference_model(
    feedforward_scale: float = 1.0,
    feedback_scale: float = 1.0,
    feedforward_sign: float = 1.0,
    plan_amplitude: float = 0.6,
    disturbance_magnitude: float = 0.4,
    duration: float = 12.0,
    time_step: float = 0.02,
) -> ReferenceResult:
    decay = math.exp(-0.5 * time_step)
    position_from_rate = (1 - decay) / 0.5
    position_from_acceleration = (time_step - position_from_rate) / 0.5
    discrete_a = ((1.0, position_from_rate), (0.0, decay))
    discrete_b = (position_from_acceleration, position_from_rate)
    error_a = (
        (
            discrete_a[0][0] - feedback_scale * discrete_b[0] * GAIN[0],
            discrete_a[0][1] - feedback_scale * discrete_b[0] * GAIN[1],
        ),
        (
            discrete_a[1][0] - feedback_scale * discrete_b[1] * GAIN[0],
            discrete_a[1][1] - feedback_scale * discrete_b[1] * GAIN[1],
        ),
    )
    step_count = round(duration / time_step)
    time = [index * time_step for index in range(step_count + 1)]
    reference = [[0.0, 0.0]]
    actual = [[0.0, 0.0]]
    error: list[list[float]] = []
    plan: list[float] = []
    disturbance: list[float] = []
    feedforward: list[float] = []
    feedback: list[float] = []
    total: list[float] = []

    for index, time_value in enumerate(time):
        plan_value = plan_amplitude * math.sin(0.6 * time_value)
        disturbance_value = (
            -disturbance_magnitude if 4.0 <= time_value < 5.0 else 0.0
        )
        error_value = [
            reference[index][axis] - actual[index][axis] for axis in range(2)
        ]
        feedforward_value = feedforward_sign * feedforward_scale * plan_value
        feedback_value = feedback_scale * sum(
            GAIN[axis] * error_value[axis] for axis in range(2)
        )
        total_value = feedforward_value + feedback_value
        plan.append(plan_value)
        disturbance.append(disturbance_value)
        error.append(error_value)
        feedforward.append(feedforward_value)
        feedback.append(feedback_value)
        total.append(total_value)
        if index < step_count:
            reference_prediction = matrix_vector(discrete_a, reference[index])
            actual_prediction = matrix_vector(discrete_a, actual[index])
            reference.append(
                [
                    reference_prediction[axis] + discrete_b[axis] * plan_value
                    for axis in range(2)
                ]
            )
            actual.append(
                [
                    actual_prediction[axis]
                    + discrete_b[axis] * (total_value + disturbance_value)
                    for axis in range(2)
                ]
            )

    position_ise = time_step * sum(value[0] ** 2 for value in error[:-1])
    rate_ise = time_step * sum(value[1] ** 2 for value in error[:-1])
    feedforward_effort = time_step * sum(value**2 for value in feedforward[:-1])
    feedback_effort = time_step * sum(value**2 for value in feedback[:-1])
    total_effort = time_step * sum(value**2 for value in total[:-1])
    outside = [abs(value[0]) > 0.02 or abs(value[1]) > 0.02 for value in error]
    last_outside = next(
        (
            index
            for index in range(len(time) - 1, -1, -1)
            if time[index] >= 5.0 and outside[index]
        ),
        None,
    )
    if last_outside is None:
        recovery_time = 0.0
    elif last_outside == step_count:
        recovery_time = math.inf
    else:
        recovery_time = time[last_outside + 1] - 5.0
    return ReferenceResult(
        discrete_a=discrete_a,
        discrete_b=discrete_b,
        error_a=error_a,
        poles=two_state_poles(error_a),
        time=time,
        reference=reference,
        actual=actual,
        error=error,
        plan=plan,
        disturbance=disturbance,
        feedforward=feedforward,
        feedback=feedback,
        total=total,
        position_ise=position_ise,
        rate_ise=rate_ise,
        position_rmse=math.sqrt(sum(value[0] ** 2 for value in error) / len(error)),
        feedforward_effort=feedforward_effort,
        feedback_effort=feedback_effort,
        total_effort=total_effort,
        maximum_position_error=max(abs(value[0]) for value in error),
        maximum_feedback=max(abs(value) for value in feedback),
        maximum_total=max(abs(value) for value in total),
        recovery_time=recovery_time,
    )


class P18ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P18"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 18)
        self.assertEqual(self.module["title"], "Use Feedforward and Feedback Together")
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["phase"], 5)
        self.assertEqual(self.module["phase_title"], "Optimal and robust control")
        self.assertEqual(
            self.module["folder"],
            "modules/18-use-feedforward-and-feedback-together",
        )
        self.assertEqual(self.module["slug"], "use-feedforward-and-feedback-together")
        self.assertEqual(self.module["prerequisites"], ["P17"])
        self.assertEqual(self.module["implementation_batch"], "P18")
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
            "discreteA = [1 positionFromRateSec;0 decay]",
            "discreteB = [positionFromAccelerationSec2;positionFromRateSec]",
            "referenceState(:,k+1) = discreteA*referenceState(:,k)+ ...",
            "feedforwardCommandMPerSec2(k) = feedforwardSign* ...",
            "feedbackCommandMPerSec2(k) = feedbackScale*feedbackGain* ...",
            "totalCommandMPerSec2(k) = feedforwardCommandMPerSec2(k)+ ...",
            "actualState(:,k+1) = discreteA*actualState(:,k)+ ...",
            "errorClosedLoopA = discreteA-feedbackScale*discreteB*feedbackGain",
            "expectedErrorNext = errorClosedLoopA*trackingError(:,k)+ ...",
        ):
            self.assertIn(formula, model)
        for marker in (
            "maximumStepCount = 5000",
            "P18:FeedforwardScaleRange",
            "P18:FeedbackScaleRange",
            "P18:FeedforwardSign",
            "P18:PlanAmplitudeRange",
            "P18:DisturbanceMagnitudeRange",
            "P18:DurationRange",
            "P18:DisplayResolution",
            "P18:GridAlignment",
            "P18:EventAlignment",
            "P18:TooManySteps",
        ):
            self.assertIn(marker, model)
        self.assertLess(model.index("rawStepCount > maximumStepCount"), model.index("referenceState = zeros"))
        self.assertNotRegex(
            model.lower(),
            r"\b(?:plot|figure|uifigure|uiaxes|uislider|uidropdown|rng|rand|randn)\s*\(",
        )
        self.assertNotRegex(
            model.lower(),
            r"\b(?:lqr|dlqr|dare|idare|ss|c2d|lsim|tf|step|sim|inv|pinv|eig)\s*\(",
        )

    def test_independent_baseline_recurrence_decomposition_and_metrics(self):
        result = reference_model()
        self.assertAlmostEqual(result.discrete_a[1][1], 0.9900498337491681)
        self.assertAlmostEqual(result.discrete_a[0][1], 0.019900332501663787)
        self.assertAlmostEqual(result.discrete_b[0], 0.00019933499667242678)
        self.assertAlmostEqual(result.discrete_b[1], 0.019900332501663787)
        self.assertLess(max(abs(pole) for pole in result.poles), 1)
        for index in range(len(result.time) - 1):
            expected_reference = matrix_vector(result.discrete_a, result.reference[index])
            expected_actual = matrix_vector(result.discrete_a, result.actual[index])
            expected_reference = [
                expected_reference[axis] + result.discrete_b[axis] * result.plan[index]
                for axis in range(2)
            ]
            expected_actual = [
                expected_actual[axis]
                + result.discrete_b[axis]
                * (result.total[index] + result.disturbance[index])
                for axis in range(2)
            ]
            self.assertEqual(result.total[index], result.feedforward[index] + result.feedback[index])
            for axis in range(2):
                self.assertAlmostEqual(result.reference[index + 1][axis], expected_reference[axis])
                self.assertAlmostEqual(result.actual[index + 1][axis], expected_actual[axis])
                self.assertAlmostEqual(
                    result.error[index][axis],
                    result.reference[index][axis] - result.actual[index][axis],
                )
        self.assertAlmostEqual(result.position_ise, 0.0161739933608727, places=13)
        self.assertAlmostEqual(result.rate_ise, 0.01669464795376342, places=13)
        self.assertAlmostEqual(result.position_rmse, 0.036682286326667535, places=13)
        self.assertAlmostEqual(result.feedback_effort, 0.11474509167732859, places=13)
        self.assertAlmostEqual(result.total_effort, 2.246753457456084, places=13)
        self.assertAlmostEqual(result.maximum_position_error, 0.11172189006637057, places=13)
        self.assertAlmostEqual(result.recovery_time, 2.6, places=13)

    def test_combined_architecture_beats_each_single_path(self):
        combined = reference_model()
        feedback_only = reference_model(feedforward_scale=0)
        feedforward_only = reference_model(feedback_scale=0)
        self.assertLess(combined.position_ise, feedback_only.position_ise)
        self.assertLess(combined.position_ise, feedforward_only.position_ise)

    def test_unplanned_load_does_not_rewrite_plan_or_feedforward_path(self):
        undisturbed = reference_model(disturbance_magnitude=0)
        disturbed = reference_model(disturbance_magnitude=0.4)
        self.assertEqual(disturbed.plan, undisturbed.plan)
        self.assertEqual(disturbed.reference, undisturbed.reference)
        self.assertEqual(disturbed.feedforward, undisturbed.feedforward)
        through_disturbance_start = [
            index for index, time_value in enumerate(disturbed.time) if time_value <= 4.0
        ]
        self.assertEqual(
            [disturbed.actual[index] for index in through_disturbance_start],
            [undisturbed.actual[index] for index in through_disturbance_start],
        )
        self.assertEqual(
            [disturbed.feedback[index] for index in through_disturbance_start],
            [undisturbed.feedback[index] for index in through_disturbance_start],
        )
        self.assertEqual(max(abs(value) for value in undisturbed.feedback), 0)
        self.assertGreater(max(abs(value) for value in disturbed.feedback), 0.3)

    def test_two_sweeps_are_independent_with_expected_limits(self):
        alpha_values = [0, 0.5, 1, 1.5]
        alpha_runs = [
            reference_model(feedforward_scale=value, disturbance_magnitude=0)
            for value in alpha_values
        ]
        self.assertGreater(alpha_runs[0].position_ise, alpha_runs[1].position_ise)
        self.assertEqual(alpha_runs[2].position_ise, 0)
        self.assertEqual(alpha_runs[2].feedback_effort, 0)
        self.assertAlmostEqual(alpha_runs[1].position_ise, alpha_runs[3].position_ise)
        self.assertAlmostEqual(alpha_runs[1].feedback_effort, alpha_runs[3].feedback_effort)
        for run in alpha_runs:
            self.assertEqual(run.disturbance, [0.0] * len(run.time))

        beta_values = [0, 0.25, 0.5, 1, 1.5, 2]
        beta_runs = [reference_model(feedback_scale=value) for value in beta_values]
        self.assertTrue(
            all(
                beta_runs[index + 1].position_ise < beta_runs[index].position_ise
                for index in range(len(beta_runs) - 1)
            )
        )
        self.assertTrue(
            all(
                beta_runs[index + 1].feedback_effort > beta_runs[index].feedback_effort
                for index in range(len(beta_runs) - 1)
            )
        )
        self.assertTrue(math.isinf(beta_runs[0].recovery_time))
        self.assertTrue(
            all(
                beta_runs[index + 1].recovery_time < beta_runs[index].recovery_time
                for index in range(1, len(beta_runs) - 1)
            )
        )

    def test_feedforward_only_pulse_limit_broken_case_and_recovery(self):
        baseline = reference_model()
        feedforward_only = reference_model(feedback_scale=0)
        self.assertAlmostEqual(feedforward_only.error[-1][0], 0.7809892087462634)
        self.assertAlmostEqual(feedforward_only.error[-1][1], 0.009505395626867573)
        self.assertAlmostEqual(max(abs(pole) for pole in feedforward_only.poles), 1)
        broken = reference_model(feedforward_sign=-1)
        self.assertGreater(broken.position_ise, 100 * baseline.position_ise)
        self.assertGreater(broken.feedback_effort, 50 * baseline.feedback_effort)
        self.assertGreater(broken.maximum_position_error, 0.5)
        self.assertTrue(math.isinf(broken.recovery_time))
        recovered = reference_model(feedforward_sign=1)
        self.assertEqual(recovered, baseline)

    def test_zero_equilibrium_and_maximum_grid_are_finite(self):
        zero = reference_model(
            feedback_scale=2,
            plan_amplitude=0,
            disturbance_magnitude=0,
        )
        self.assertEqual(max(abs(value) for state in zero.reference for value in state), 0)
        self.assertEqual(max(abs(value) for state in zero.actual for value in state), 0)
        self.assertEqual(max(abs(value) for value in zero.total), 0)
        bounded = reference_model(
            feedback_scale=2,
            plan_amplitude=1,
            disturbance_magnitude=0.8,
            duration=20,
            time_step=0.004,
        )
        self.assertEqual(len(bounded.time), 5001)
        self.assertTrue(
            all(
                math.isfinite(value)
                for series in (
                    bounded.plan,
                    bounded.disturbance,
                    bounded.feedforward,
                    bounded.feedback,
                    bounded.total,
                )
                for value in series
            )
        )
        self.assertLess(max(abs(pole) for pole in bounded.poles), 1)

    def test_experiment_has_ordered_flow_labels_metrics_sweeps_and_broken_case(self):
        experiment = self.read("experiment.m")
        ordered = (
            "%% Read:",
            "%% Make one prediction",
            "%% Visualize the deterministic baseline",
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
            "feedforwardScaleValues = [0 0.5 1 1.5]",
            "feedbackScaleValues = [0 0.25 0.5 1 1.5 2]",
            "changed = model(feedforwardScaleValues(k),1,1,0.6,0,12,0.02)",
            "changed = model(1,feedbackScaleValues(k),1,0.6,0.4,12,0.02)",
            "broken = model(1,1,-1,0.6,0.4,12,0.02)",
            "recovered = model(1,1,1,0.6,0.4,12,0.02)",
            "Position (m)",
            "Position error (m)",
            "Rate error (m/s)",
            "Plant-input acceleration (m/s^2)",
            "Position-error integral (m^2 s)",
            "Feedback effort integral (m^2/s^3)",
            "run_checks;",
        ):
            self.assertIn(marker, experiment)

    def test_interactive_has_meaningful_controls_reset_and_feedback(self):
        interactive = self.read("interactive.m")
        for marker in (
            "uifigure(",
            "uiaxes(",
            "uislider(",
            "uispinner(",
            "uidropdown(",
            "Feedforward scale alpha",
            "Feedback scale beta",
            "Disturbance magnitude (m/s^2)",
            "Reversed feedforward sign (broken)",
            "ValueChangingFcn",
            "ValueChangedFcn",
            "ButtonPushedFcn",
            "resetBaseline",
            "redraw(1,1,0.4,'Correct feedforward sign')",
            "result = modelFunction(feedforwardScale,feedbackScale, ...",
            "broken: feedforward polarity is reversed",
            "limit: feedforward cannot remove disturbance error",
            "matched plan: feedback correction is zero",
        ):
            self.assertIn(marker, interactive)
        self.assertGreaterEqual(interactive.count("uiaxes("), 2)

    def test_checks_cover_invariants_limits_malformed_recovery_and_bounds(self):
        checks = self.read("run_checks.m")
        for marker in (
            "isequaln(baselineA,baselineB)",
            "expectedA = [1 expectedPositionFromRate;0 expectedDecay]",
            "expectedGain = [1.9644942427723904 1.7703588392280174]",
            "expectedReferenceNext",
            "expectedActualNext",
            "feedbackOnly = model(0,1,1,0.6,0.4,12,0.02)",
            "feedforwardOnly = model(1,0,1,0.6,0.4,12,0.02)",
            "undisturbedBaseline = model(1,1,1,0.6,0,12,0.02)",
            "throughDisturbanceStart",
            "feedforwardScaleValues = [0 0.5 1 1.5]",
            "matchedPlan = feedforwardRuns{3}",
            "feedbackScaleValues = [0 0.25 0.5 1 1.5 2]",
            "broken = model(1,1,-1,0.6,0.4,12,0.02)",
            "recovered = model(1,1,1,0.6,0.4,12,0.02)",
            "zeroMotion = model(1,2,1,0,0,12,0.02)",
            "model(-0.01,1,1,0.6,0.4,12,0.02)",
            "model(1,-0.01,1,0.6,0.4,12,0.02)",
            "model(1,1,1,-0.01,0.4,12,0.02)",
            "model(1,1,1,0.6,-0.01,12,0.02)",
            "P18:FeedforwardScaleRange",
            "P18:FeedbackScaleRange",
            "P18:FeedforwardSign",
            "P18:PlanAmplitudeRange",
            "P18:DisturbanceMagnitudeRange",
            "P18:DurationRange",
            "P18:DisplayResolution",
            "P18:GridAlignment",
            "P18:EventAlignment",
            "P18:TooManySteps",
            "boundedGrid = model(1,2,1,1,0.8,20,0.004)",
            "assertAnyError",
            "assertErrorId",
        ):
            self.assertIn(marker, checks)

    def test_tutor_text_connects_prerequisites_and_keeps_claim_boundary(self):
        combined = "\n".join(
            self.read(name)
            for name in ("README.md", "lesson.md", "walkthrough.md", "checks.md")
        )
        for marker in (
            QUESTION,
            "P17",
            "P16",
            "LQR",
            "state estimate",
            "feasible reference",
            "planned plant input",
            "tracking error",
            "cross term",
            "two sentences",
            "No MATLAB-runtime",
            "m^2/s^3",
        ):
            self.assertIn(marker.lower(), combined.lower())
        for placeholder in ("scaffolded", "placeholder", "todo"):
            self.assertNotIn(placeholder, combined.lower())
        for name in ("model.m", "experiment.m", "interactive.m", "run_checks.m", "lesson.m"):
            self.assertNotRegex(
                self.read(name).lower(),
                r"\b(?:lqr|dlqr|dare|idare|ss|c2d|lsim|tf|step|sim|inv|pinv|eig)\s*\(",
            )

    def test_readme_scopes_interactive_path_and_public_cli_is_isolated(self):
        readme = self.read("README.md")
        self.assertIn(
            'moduleFolder = fullfile(pwd,"modules","18-use-feedforward-and-feedback-together");',
            readme,
        )
        self.assertIn('addpath(moduleFolder,"-begin");', readme)
        self.assertIn("clear model interactive;", readme)
        self.assertEqual(readme.count("rmpath(moduleFolder);"), 2)
        self.assertIn("catch exception", readme)
        self.assertIn("rethrow(exception)", readme)

        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            shutil.copytree(ROOT / "bin", fixture / "bin")
            shutil.copytree(ROOT / "curriculum", fixture / "curriculum")
            shutil.copytree(self.folder, fixture / self.module["folder"])
            progress_file = fixture / ".learning/progress.json"
            progress_file.parent.mkdir(parents=True)
            original = {
                "current": "P17",
                "completed": {"P16": True},
                "notes": {"P16": "retain this note"},
            }
            progress_file.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            checked = subprocess.run(
                [str(fixture / "bin/learn"), "check", "P18"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(checked.stdout, "Run in MATLAB: run_module_checks('P18')\n")
            self.assertEqual(json.loads(progress_file.read_text()), original)
            started = subprocess.run(
                [str(fixture / "bin/learn"), "start", "P18"],
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
            self.assertEqual(retained["current"], "P18")
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


if __name__ == "__main__":
    unittest.main()
