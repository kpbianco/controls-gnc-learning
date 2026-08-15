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
    "What inputs, observable effects, and failure modes matter when you measure "
    "Sensitivity to Model Error?"
)


@dataclass
class ReferenceResult:
    actuator_gain_ratio: float
    drag_ratio: float
    actuator_sign: float
    reference_speed: float
    duration: float
    time_step: float
    nominal_decay: float
    nominal_input: float
    actual_decay: float
    actual_input: float
    nominal_pole: float
    actual_pole: float
    stable: bool
    time: list[float]
    reference: list[float]
    predicted: list[float]
    actual: list[float]
    nominal_feedforward: list[float]
    nominal_feedback: list[float]
    nominal_total: list[float]
    actual_feedforward: list[float]
    actual_feedback: list[float]
    actual_total: list[float]
    gap: list[float]
    gap_ise: float
    gap_rmse: float
    maximum_gap: float
    tracking_ise: float
    feedback_effort: float
    peak_command: float
    steady_speed: float
    gain_sensitivity: float
    drag_sensitivity: float


def reference_model(
    actuator_gain_ratio: float = 1.0,
    drag_ratio: float = 1.0,
    actuator_sign: float = 1.0,
    reference_speed: float = 1.0,
    duration: float = 10.0,
    time_step: float = 0.02,
) -> ReferenceResult:
    nominal_drag = 1.0
    nominal_gain = 1.0
    feedback_gain = 1.5
    actual_drag = drag_ratio * nominal_drag
    actual_gain = actuator_sign * actuator_gain_ratio * nominal_gain
    nominal_decay = math.exp(-nominal_drag * time_step)
    nominal_input = nominal_gain / nominal_drag * (1 - nominal_decay)
    actual_decay = math.exp(-actual_drag * time_step)
    actual_input = actual_gain / actual_drag * (1 - actual_decay)
    nominal_pole = nominal_decay - nominal_input * feedback_gain
    actual_pole = actual_decay - actual_input * feedback_gain
    stable = abs(actual_pole) < 1
    step_count = round(duration / time_step)
    time = [index * time_step for index in range(step_count + 1)]
    reference = [reference_speed if value >= 1 else 0.0 for value in time]
    predicted = [0.0]
    actual = [0.0]
    nominal_feedforward: list[float] = []
    nominal_feedback: list[float] = []
    nominal_total: list[float] = []
    actual_feedforward: list[float] = []
    actual_feedback: list[float] = []
    actual_total: list[float] = []

    for index in range(step_count + 1):
        feedforward = nominal_drag / nominal_gain * reference[index]
        predicted_feedback = feedback_gain * (reference[index] - predicted[index])
        measured_feedback = feedback_gain * (reference[index] - actual[index])
        predicted_command = feedforward + predicted_feedback
        measured_command = feedforward + measured_feedback
        nominal_feedforward.append(feedforward)
        nominal_feedback.append(predicted_feedback)
        nominal_total.append(predicted_command)
        actual_feedforward.append(feedforward)
        actual_feedback.append(measured_feedback)
        actual_total.append(measured_command)
        if index < step_count:
            predicted.append(
                nominal_decay * predicted[index] + nominal_input * predicted_command
            )
            actual.append(actual_decay * actual[index] + actual_input * measured_command)

    gap = [measured - prediction for measured, prediction in zip(actual, predicted)]
    tracking_error = [target - measured for target, measured in zip(reference, actual)]
    denominator = actual_drag + actual_gain * feedback_gain
    if stable:
        steady_speed = (
            actual_gain
            * (nominal_drag / nominal_gain + feedback_gain)
            * reference_speed
            / denominator
        )
        if actuator_sign > 0:
            gain_sensitivity = (
                actuator_sign
                * nominal_gain
                * (nominal_drag / nominal_gain + feedback_gain)
                * reference_speed
                * actual_drag
                / denominator**2
            )
            drag_sensitivity = (
                -actual_gain
                * (nominal_drag / nominal_gain + feedback_gain)
                * reference_speed
                * nominal_drag
                / denominator**2
            )
        else:
            gain_sensitivity = math.nan
            drag_sensitivity = math.nan
    else:
        steady_speed = math.nan
        gain_sensitivity = math.nan
        drag_sensitivity = math.nan
    return ReferenceResult(
        actuator_gain_ratio=actuator_gain_ratio,
        drag_ratio=drag_ratio,
        actuator_sign=actuator_sign,
        reference_speed=reference_speed,
        duration=duration,
        time_step=time_step,
        nominal_decay=nominal_decay,
        nominal_input=nominal_input,
        actual_decay=actual_decay,
        actual_input=actual_input,
        nominal_pole=nominal_pole,
        actual_pole=actual_pole,
        stable=stable,
        time=time,
        reference=reference,
        predicted=predicted,
        actual=actual,
        nominal_feedforward=nominal_feedforward,
        nominal_feedback=nominal_feedback,
        nominal_total=nominal_total,
        actual_feedforward=actual_feedforward,
        actual_feedback=actual_feedback,
        actual_total=actual_total,
        gap=gap,
        gap_ise=time_step * sum(value**2 for value in gap[:-1]),
        gap_rmse=math.sqrt(sum(value**2 for value in gap) / len(gap)),
        maximum_gap=max(abs(value) for value in gap),
        tracking_ise=time_step * sum(value**2 for value in tracking_error[:-1]),
        feedback_effort=time_step * sum(value**2 for value in actual_feedback[:-1]),
        peak_command=max(abs(value) for value in actual_total),
        steady_speed=steady_speed,
        gain_sensitivity=gain_sensitivity,
        drag_sensitivity=drag_sensitivity,
    )


class P19ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P19"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 19)
        self.assertEqual(self.module["title"], "Measure Sensitivity to Model Error")
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["phase"], 5)
        self.assertEqual(self.module["phase_title"], "Optimal and robust control")
        self.assertEqual(
            self.module["folder"],
            "modules/19-measure-sensitivity-to-model-error",
        )
        self.assertEqual(self.module["slug"], "measure-sensitivity-to-model-error")
        self.assertEqual(self.module["prerequisites"], ["P18"])
        self.assertEqual(self.module["implementation_batch"], "P19")
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
            "actualDragPerSec = dragRatio*nominalDragPerSec",
            "actualActuatorGain = actuatorSign*actuatorGainRatio* ...",
            "nominalDecay = exp(-nominalDragPerSec*timeStepSec)",
            "actualDecay = exp(-actualDragPerSec*timeStepSec)",
            "nominalClosedLoopPole = nominalDecay- ...",
            "actualClosedLoopPole = actualDecay- ...",
            "predictedSpeedMPerSec(k+1) = nominalDecay* ...",
            "actualSpeedMPerSec(k+1) = actualDecay*actualSpeedMPerSec(k)+ ...",
            "speedPredictionGapMPerSec = actualSpeedMPerSec-predictedSpeedMPerSec",
            "actuatorGainSensitivityMPerSecPerFraction = actuatorSign* ...",
            "dragSensitivityMPerSecPerFraction = -actualActuatorGain* ...",
        ):
            self.assertIn(formula, model)
        for marker in (
            "maximumStepCount = 5000",
            "P19:ActuatorGainRatioRange",
            "P19:DragRatioRange",
            "P19:ActuatorSign",
            "P19:ReferenceSpeedRange",
            "P19:DurationRange",
            "P19:DisplayResolution",
            "P19:GridAlignment",
            "P19:EventAlignment",
            "P19:TooManySteps",
        ):
            self.assertIn(marker, model)
        self.assertLess(
            model.index("rawStepCount > maximumStepCount"),
            model.index("predictedSpeedMPerSec = zeros"),
        )
        self.assertNotRegex(
            model.lower(),
            r"\b(?:plot|figure|uifigure|uiaxes|uislider|uidropdown|rng|rand|randn)\s*\(",
        )
        self.assertNotRegex(
            model.lower(),
            r"\b(?:lqr|dlqr|dare|idare|ss|c2d|lsim|tf|step|sim|inv|pinv|eig)\s*\(",
        )

    def test_independent_baseline_recurrence_and_matched_limit(self):
        result = reference_model()
        self.assertAlmostEqual(result.nominal_decay, 0.9801986733067553)
        self.assertAlmostEqual(result.nominal_input, 0.019801326693244747)
        self.assertAlmostEqual(result.nominal_pole, 0.9504966832668882)
        self.assertLess(abs(result.actual_pole), 1)
        for index in range(len(result.time) - 1):
            expected_reference = 1.0 if result.time[index] >= 1 else 0.0
            expected_feedforward = expected_reference
            expected_nominal_feedback = 1.5 * (
                expected_reference - result.predicted[index]
            )
            expected_actual_feedback = 1.5 * (
                expected_reference - result.actual[index]
            )
            expected_nominal_total = expected_feedforward + expected_nominal_feedback
            expected_actual_total = expected_feedforward + expected_actual_feedback
            expected_prediction = (
                result.nominal_decay * result.predicted[index]
                + result.nominal_input * expected_nominal_total
            )
            expected_actual = (
                result.actual_decay * result.actual[index]
                + result.actual_input * expected_actual_total
            )
            self.assertEqual(result.reference[index], expected_reference)
            self.assertAlmostEqual(result.nominal_total[index], expected_nominal_total)
            self.assertAlmostEqual(result.actual_total[index], expected_actual_total)
            self.assertAlmostEqual(result.predicted[index + 1], expected_prediction)
            self.assertAlmostEqual(result.actual[index + 1], expected_actual)
        self.assertEqual(result.predicted, result.actual)
        self.assertEqual(result.gap, [0.0] * len(result.time))
        self.assertEqual(result.gap_ise, 0)
        self.assertEqual(result.gap_rmse, 0)
        self.assertEqual(result.maximum_gap, 0)
        self.assertEqual(result.steady_speed, 1)
        self.assertAlmostEqual(result.gain_sensitivity, 0.4)
        self.assertAlmostEqual(result.drag_sensitivity, -0.4)

    def test_independent_nonnominal_metrics_and_sensitivity_derivatives(self):
        weaker = reference_model(actuator_gain_ratio=0.8)
        self.assertAlmostEqual(weaker.actual_input, 0.0158410613545958)
        self.assertAlmostEqual(weaker.actual_pole, 0.9564370812748616)
        self.assertAlmostEqual(weaker.gap_ise, 0.07788234685631548, places=13)
        self.assertAlmostEqual(weaker.gap_rmse, 0.08825636091170849, places=13)
        self.assertAlmostEqual(weaker.maximum_gap, 0.11304306795345398, places=13)
        self.assertAlmostEqual(weaker.steady_speed, 10 / 11)
        self.assertAlmostEqual(weaker.gain_sensitivity, 0.5165289256198347)
        self.assertAlmostEqual(weaker.drag_sensitivity, -0.4132231404958677)

        increment = 1e-5
        gain_plus = reference_model(actuator_gain_ratio=0.8 + increment).steady_speed
        gain_minus = reference_model(actuator_gain_ratio=0.8 - increment).steady_speed
        gain_difference = (gain_plus - gain_minus) / (2 * increment)
        drag_plus = reference_model(
            actuator_gain_ratio=0.8, drag_ratio=1 + increment
        ).steady_speed
        drag_minus = reference_model(
            actuator_gain_ratio=0.8, drag_ratio=1 - increment
        ).steady_speed
        drag_difference = (drag_plus - drag_minus) / (2 * increment)
        self.assertAlmostEqual(gain_difference, weaker.gain_sensitivity, places=8)
        self.assertAlmostEqual(drag_difference, weaker.drag_sensitivity, places=8)

    def test_two_sweeps_are_independent_with_expected_limits(self):
        gain_values = [0.6, 0.8, 1, 1.2, 1.4]
        gain_runs = [reference_model(actuator_gain_ratio=value) for value in gain_values]
        self.assertTrue(
            all(
                gain_runs[index + 1].steady_speed > gain_runs[index].steady_speed
                for index in range(len(gain_runs) - 1)
            )
        )
        self.assertEqual(gain_runs[2].gap_rmse, 0)
        self.assertTrue(all(run.drag_ratio == 1 for run in gain_runs))
        self.assertTrue(all(run.actuator_sign == 1 for run in gain_runs))
        self.assertAlmostEqual(gain_runs[0].steady_speed, 15 / 19)
        self.assertAlmostEqual(gain_runs[-1].steady_speed, 35 / 31)

        drag_values = [0.5, 0.75, 1, 1.5, 2]
        drag_runs = [reference_model(drag_ratio=value) for value in drag_values]
        self.assertTrue(
            all(
                drag_runs[index + 1].steady_speed < drag_runs[index].steady_speed
                for index in range(len(drag_runs) - 1)
            )
        )
        self.assertEqual(drag_runs[2].gap_rmse, 0)
        self.assertTrue(all(run.actuator_gain_ratio == 1 for run in drag_runs))
        self.assertTrue(all(run.actuator_sign == 1 for run in drag_runs))
        self.assertAlmostEqual(drag_runs[0].steady_speed, 1.25)
        self.assertAlmostEqual(drag_runs[-1].steady_speed, 5 / 7)

    def test_broken_case_zero_limit_recovery_and_maximum_grid(self):
        baseline = reference_model()
        broken = reference_model(actuator_sign=-1)
        self.assertFalse(broken.stable)
        self.assertGreater(abs(broken.actual_pole), 1)
        self.assertGreater(broken.maximum_gap, 400)
        self.assertGreater(broken.feedback_effort, 300_000)
        self.assertTrue(math.isnan(broken.steady_speed))
        self.assertTrue(math.isnan(broken.gain_sensitivity))
        self.assertTrue(math.isnan(broken.drag_sensitivity))
        self.assertEqual(reference_model(), baseline)

        stable_reversed = reference_model(
            actuator_gain_ratio=0.5, drag_ratio=2, actuator_sign=-1
        )
        self.assertTrue(stable_reversed.stable)
        self.assertAlmostEqual(stable_reversed.steady_speed, -1)
        self.assertTrue(math.isnan(stable_reversed.gain_sensitivity))
        self.assertTrue(math.isnan(stable_reversed.drag_sensitivity))

        zero = reference_model(
            actuator_gain_ratio=1.5, drag_ratio=2, reference_speed=0
        )
        self.assertEqual(max(abs(value) for value in zero.reference), 0)
        self.assertEqual(max(abs(value) for value in zero.predicted), 0)
        self.assertEqual(max(abs(value) for value in zero.actual), 0)
        self.assertEqual(max(abs(value) for value in zero.actual_total), 0)
        self.assertEqual(zero.gap_ise, 0)

        bounded = reference_model(
            actuator_gain_ratio=1.5,
            drag_ratio=2,
            reference_speed=2,
            duration=20,
            time_step=0.004,
        )
        self.assertEqual(len(bounded.time), 5001)
        self.assertTrue(bounded.stable)
        self.assertTrue(
            all(
                math.isfinite(value)
                for series in (
                    bounded.predicted,
                    bounded.actual,
                    bounded.actual_feedback,
                    bounded.actual_total,
                )
                for value in series
            )
        )

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
            "actuatorGainRatioValues = [0.6 0.8 1 1.2 1.4]",
            "dragRatioValues = [0.5 0.75 1 1.5 2]",
            "changed = model(actuatorGainRatioValues(k),1,1,1,10,0.02)",
            "changed = model(1,dragRatioValues(k),1,1,10,0.02)",
            "broken = model(1,1,-1,1,10,0.02)",
            "recovered = model(1,1,1,1,10,0.02)",
            "Speed (m/s)",
            "Prediction gap (m/s)",
            "Acceleration command (m/s^2)",
            "Prediction-gap RMSE (m/s)",
            "Local sensitivity (m/s per fraction)",
            "run_checks;",
        ):
            self.assertIn(marker, experiment)
        self.assertGreaterEqual(experiment.count("figure("), 5)

    def test_interactive_has_meaningful_controls_reset_and_feedback(self):
        interactive = self.read("interactive.m")
        for marker in (
            "function interactive",
            "uifigure(",
            "uiaxes(",
            "uislider(",
            "uispinner(",
            "uidropdown(",
            "Actuator gain ratio (actual / nominal)",
            "Drag ratio (actual / nominal)",
            "Reference speed (m/s)",
            "Reversed sign (broken)",
            "ValueChangingFcn",
            "ValueChangedFcn",
            "ButtonPushedFcn",
            "resetBaseline",
            "redraw(1,1,1,'Correct sign')",
            "result = modelFunction(gainRatio,dragRatio,actuatorSign, ...",
            "broken: reversed actuator polarity",
            "matched limit: nominal and actual histories",
            "local gain sensitivity",
            "local drag sensitivity",
        ):
            self.assertIn(marker, interactive)
        self.assertGreaterEqual(interactive.count("uiaxes("), 2)

    def test_checks_cover_invariants_limits_malformed_recovery_and_bounds(self):
        checks = self.read("run_checks.m")
        for marker in (
            "isequaln(baselineA,baselineB)",
            "expectedNominalDecay = exp(-0.02)",
            "expectedNominalPole",
            "expectedPredictedNext",
            "expectedActualNext",
            "weaker = model(0.8,1,1,1,10,0.02)",
            "expectedGapIse",
            "actuatorGainRatioValues = [0.6 0.8 1 1.2 1.4]",
            "dragRatioValues = [0.5 0.75 1 1.5 2]",
            "broken = model(1,1,-1,1,10,0.02)",
            "recovered = model(1,1,1,1,10,0.02)",
            "zeroReference = model(1.5,2,1,0,10,0.02)",
            "stableReversed = model(0.5,2,-1,1,10,0.02)",
            "model(-1,1,1,1,10,0.02)",
            "model(1,-1,1,1,10,0.02)",
            "model(1,1,1,-1,10,0.02)",
            "P19:ActuatorGainRatioRange",
            "P19:DragRatioRange",
            "P19:ActuatorSign",
            "P19:ReferenceSpeedRange",
            "P19:DurationRange",
            "P19:DisplayResolution",
            "P19:GridAlignment",
            "P19:EventAlignment",
            "P19:TooManySteps",
            "boundedGrid = model(1.5,2,1,2,20,0.004)",
            "assertAnyError",
            "assertErrorId",
        ):
            self.assertIn(marker, checks)

    def test_tutor_text_connects_prerequisite_and_keeps_claim_boundary(self):
        combined = "\n".join(
            self.read(name)
            for name in ("README.md", "lesson.md", "walkthrough.md", "checks.md")
        )
        for marker in (
            QUESTION,
            "P18",
            "feedforward",
            "feedback",
            "prediction gap",
            "actuator effectiveness",
            "drag",
            "fractional parameter change",
            "closed-loop pole",
            "P20",
            "exactly two sentences",
            "No MATLAB-runtime",
            "m/s per fraction",
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
            'moduleFolder = fullfile(pwd,"modules","19-measure-sensitivity-to-model-error");',
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
                "current": "P18",
                "completed": {"P17": True},
                "notes": {"P17": "retain this note"},
            }
            progress_file.write_text(
                json.dumps(original, indent=2) + "\n", encoding="utf-8"
            )
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            checked = subprocess.run(
                [str(fixture / "bin/learn"), "check", "P19"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(
                checked.stdout, "Run in MATLAB: run_module_checks('P19')\n"
            )
            self.assertEqual(json.loads(progress_file.read_text()), original)
            started = subprocess.run(
                [str(fixture / "bin/learn"), "start", "P19"],
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
            self.assertEqual(retained["current"], "P19")
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

    def test_public_cli_completion_preserves_progress_and_records_teach_back(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            shutil.copytree(ROOT / "bin", fixture / "bin")
            shutil.copytree(ROOT / "curriculum", fixture / "curriculum")
            fixture_manifest = json.loads(
                (fixture / "curriculum/modules.json").read_text(encoding="utf-8")
            )
            implemented_count = sum(
                module["status"] == "implemented"
                for module in fixture_manifest["modules"]
            )
            progress_file = fixture / ".learning/progress.json"
            progress_file.parent.mkdir(parents=True)
            original = {
                "current": "P18",
                "completed": {"P17": True},
                "notes": {"P17": "retain this note"},
            }
            progress_file.write_text(
                json.dumps(original, indent=2) + "\n", encoding="utf-8"
            )
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            teach_back = (
                "Actuator effectiveness and drag are the uncertain inputs, and the "
                "prediction gap reveals their effects. A matched limit has zero gap, "
                "while reversed polarity breaks the feedback assumption."
            )
            completed = subprocess.run(
                [
                    str(fixture / "bin/learn"),
                    "complete",
                    "P19",
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
            self.assertEqual(completed.stdout, "Marked P19 complete.\n")

            retained = json.loads(progress_file.read_text(encoding="utf-8"))
            self.assertEqual(retained["current"], "P19")
            self.assertEqual(retained["completed"], {"P17": True, "P19": True})
            self.assertEqual(
                retained["notes"],
                {"P17": "retain this note", "P19": teach_back},
            )

            status = subprocess.run(
                [str(fixture / "bin/learn"), "status"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertIn(
                f"24 total, {implemented_count} implemented, 2 completed",
                status.stdout,
            )
            self.assertIn("Current: P19", status.stdout)

            listing = subprocess.run(
                [str(fixture / "bin/learn"), "list"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(listing.returncode, 0, listing.stderr)
            p19_line = next(
                line for line in listing.stdout.splitlines() if " P19 " in line
            )
            self.assertTrue(p19_line.startswith("✓ P19"))


if __name__ == "__main__":
    unittest.main()
