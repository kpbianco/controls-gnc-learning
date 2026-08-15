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
    "What inputs, observable effects, and failure modes matter when you compare "
    "Nominal and Robust Designs?"
)
GAIN_VALUES = [0.5, 0.75, 1.0, 1.25, 1.5]
DRAG_VALUES = [0.5, 0.75, 1.0, 1.5, 2.0]
KP_VALUES = [0.5, 1.0, 1.5, 2.0]
KI_VALUES = [0.4, 0.8, 1.2]


def controller_poles(
    decay: float,
    input_coefficient: float,
    design: str,
    kp: float,
    ki: float,
    time_step: float,
) -> tuple[complex, complex, float]:
    if design == "nominal":
        pole = complex(decay - input_coefficient * kp)
        return pole, complex(math.nan), abs(pole)
    trace = decay - input_coefficient * kp + 1
    determinant = (
        decay
        - input_coefficient * kp
        + input_coefficient * ki * time_step
    )
    root = complex(trace * trace - 4 * determinant) ** 0.5
    pole_1 = (trace + root) / 2
    pole_2 = (trace - root) / 2
    return pole_1, pole_2, max(abs(pole_1), abs(pole_2))


def reference_run(
    actuator_gain_ratio: float = 1.0,
    drag_ratio: float = 1.0,
    actuator_sign: float = 1.0,
    reference_speed: float = 1.0,
    duration: float = 12.0,
    time_step: float = 0.02,
    design: str = "nominal",
    kp: float | None = None,
    ki: float | None = None,
    divergence_limit: float = 1000.0,
) -> dict[str, object]:
    if design == "nominal":
        kp = 1.5 if kp is None else kp
        ki = 0.0
    else:
        kp = 2.0 if kp is None else kp
        ki = 0.8 if ki is None else ki
    actual_drag = drag_ratio
    actual_gain = actuator_sign * actuator_gain_ratio
    decay = math.exp(-actual_drag * time_step)
    input_coefficient = actual_gain / actual_drag * (1 - decay)
    nominal_feedforward_gain = 1.0
    step_count = round(duration / time_step)
    time = [index * time_step for index in range(step_count + 1)]
    reference = [reference_speed if value >= 1 else 0.0 for value in time]
    speed = [0.0]
    integral = [0.0]
    command: list[float] = []
    feedback: list[float] = []
    terminated = False
    termination_index: int | None = None
    for index in range(step_count + 1):
        if terminated:
            speed.append(math.nan) if len(speed) <= index else None
            integral.append(math.nan) if len(integral) <= index else None
            command.append(math.nan)
            feedback.append(math.nan)
            continue
        error = reference[index] - speed[index]
        feedback_value = kp * error
        if design == "nominal":
            command_value = nominal_feedforward_gain * reference[index] + feedback_value
        else:
            command_value = feedback_value + ki * integral[index]
        feedback.append(feedback_value)
        command.append(command_value)
        if index < step_count:
            next_speed = decay * speed[index] + input_coefficient * command_value
            next_integral = integral[index] + time_step * error
            speed.append(next_speed)
            integral.append(next_integral)
            if not math.isfinite(next_speed) or abs(next_speed) > divergence_limit:
                terminated = True
                termination_index = index + 1
    if len(speed) < step_count + 1:
        speed.extend([math.nan] * (step_count + 1 - len(speed)))
        integral.extend([math.nan] * (step_count + 1 - len(integral)))
    errors = [target - value for target, value in zip(reference, speed)]
    valid_indices = [
        index
        for index in range(step_count)
        if math.isfinite(errors[index]) and math.isfinite(command[index])
    ]
    tracking_ise = time_step * sum(errors[index] ** 2 for index in valid_indices)
    command_effort = time_step * sum(
        command[index] ** 2 for index in valid_indices
    )
    pole_1, pole_2, pole_magnitude = controller_poles(
        decay, input_coefficient, design, kp, ki, time_step
    )
    stable = pole_magnitude < 1
    if stable and design == "nominal":
        steady_speed = (
            actual_gain * (1 + kp) * reference_speed / (actual_drag + actual_gain * kp)
        )
        steady_command = math.nan
    elif stable and actual_gain > 0:
        steady_speed = reference_speed
        steady_command = actual_drag / actual_gain * reference_speed
    else:
        steady_speed = math.nan
        steady_command = math.nan
    return {
        "actuator_gain_ratio": actuator_gain_ratio,
        "drag_ratio": drag_ratio,
        "actuator_sign": actuator_sign,
        "reference_speed": reference_speed,
        "duration": duration,
        "time_step": time_step,
        "decay": decay,
        "input": input_coefficient,
        "time": time,
        "reference": reference,
        "speed": speed,
        "integral": integral,
        "feedback": feedback,
        "command": command,
        "tracking_ise": tracking_ise,
        "command_effort": command_effort,
        "final_error": abs(errors[-1]) if stable and not terminated else math.nan,
        "pole_1": pole_1,
        "pole_2": pole_2,
        "pole_magnitude": pole_magnitude,
        "stable": stable,
        "terminated": terminated,
        "termination_index": termination_index,
        "steady_speed": steady_speed,
        "steady_command": steady_command,
    }


def reference_selection() -> dict[str, object]:
    worst_ise = [[0.0 for _ in KI_VALUES] for _ in KP_VALUES]
    worst_effort = [[0.0 for _ in KI_VALUES] for _ in KP_VALUES]
    stable = [[True for _ in KI_VALUES] for _ in KP_VALUES]
    feasible = [[False for _ in KI_VALUES] for _ in KP_VALUES]
    selected_score = math.inf
    selected_kp = math.nan
    selected_ki = math.nan
    for kp_index, kp in enumerate(KP_VALUES):
        for ki_index, ki in enumerate(KI_VALUES):
            for gain_ratio in GAIN_VALUES:
                for drag_ratio in DRAG_VALUES:
                    result = reference_run(
                        gain_ratio,
                        drag_ratio,
                        design="robust",
                        kp=kp,
                        ki=ki,
                    )
                    worst_ise[kp_index][ki_index] = max(
                        worst_ise[kp_index][ki_index], result["tracking_ise"]
                    )
                    worst_effort[kp_index][ki_index] = max(
                        worst_effort[kp_index][ki_index], result["command_effort"]
                    )
                    stable[kp_index][ki_index] = (
                        stable[kp_index][ki_index] and result["stable"]
                    )
            feasible[kp_index][ki_index] = (
                stable[kp_index][ki_index]
                and worst_effort[kp_index][ki_index] <= 90
            )
            if feasible[kp_index][ki_index] and worst_ise[kp_index][ki_index] < selected_score:
                selected_score = worst_ise[kp_index][ki_index]
                selected_kp = kp
                selected_ki = ki
    return {
        "worst_ise": worst_ise,
        "worst_effort": worst_effort,
        "stable": stable,
        "feasible": feasible,
        "score": selected_score,
        "kp": selected_kp,
        "ki": selected_ki,
    }


class P20ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P20"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 20)
        self.assertEqual(self.module["title"], "Compare Nominal and Robust Designs")
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["phase"], 5)
        self.assertEqual(self.module["phase_title"], "Optimal and robust control")
        self.assertEqual(
            self.module["folder"],
            "modules/20-compare-nominal-and-robust-designs",
        )
        self.assertEqual(self.module["slug"], "compare-nominal-and-robust-designs")
        self.assertEqual(self.module["prerequisites"], ["P19"])
        self.assertEqual(self.module["implementation_batch"], "P20")
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
            "actualDecay = exp(-actualDragPerSec*timeStepSec)",
            "actualInputCoefficient = actualActuatorGain/actualDragPerSec* ...",
            "nominalFeedforwardGainPerSec = nominalDragPerSec/nominalActuatorGain",
            "proportionalGainCandidatesPerSec = [0.5 1 1.5 2]",
            "integralGainCandidatesPerSec2 = [0.4 0.8 1.2]",
            "candidateWorstEffort <= commandEffortLimitM2PerSec3",
            "candidateWorstTracking < selectedScore",
            "speedMPerSec(k+1) = nextSpeed",
            "errorIntegralM(k+1) = nextIntegral",
            "squareRoot = sqrt(complex(discriminant,0))",
            "feedforwardGainPerSec*referenceSpeed(k)",
        ):
            self.assertIn(formula, model)
        for marker in (
            "maximumStepCount = 5000",
            "maximumDesignTransitionCount",
            "divergenceLimitMPerSec = 1000",
            "P20:ActuatorGainRatioRange",
            "P20:DragRatioRange",
            "P20:ActuatorSign",
            "P20:ReferenceSpeedRange",
            "P20:DurationRange",
            "P20:DisplayResolution",
            "P20:GridAlignment",
            "P20:EventAlignment",
            "P20:TooManySteps",
            "P20:NoFeasibleRobustDesign",
        ):
            self.assertIn(marker, model)
        self.assertLess(
            model.index("rawStepCount > maximumStepCount"),
            model.index("timeSec = (0:stepCount)*timeStepSec"),
        )
        self.assertNotRegex(
            model.lower(),
            r"\b(?:plot|figure|uifigure|uiaxes|uislider|uidropdown|rng|rand|randn|global|persistent)\s*\(?",
        )
        self.assertIn("'trackingIntegralM2PerSec'", model)
        self.assertIn("'comparisonCostM2PerSec'", model)
        self.assertNotIn("M2Sec", model)

    def test_independent_baseline_recurrences_metrics_and_limits(self):
        nominal = reference_run(design="nominal")
        robust = reference_run(design="robust")
        self.assertAlmostEqual(nominal["decay"], 0.9801986733067553)
        self.assertAlmostEqual(nominal["input"], 0.019801326693244747)
        for index in range(len(nominal["time"]) - 1):
            expected_reference = 1.0 if nominal["time"][index] >= 1 else 0.0
            nominal_error = expected_reference - nominal["speed"][index]
            robust_error = expected_reference - robust["speed"][index]
            nominal_feedforward_gain = 1.0
            expected_nominal_command = (
                nominal_feedforward_gain * expected_reference + 1.5 * nominal_error
            )
            expected_robust_command = 2 * robust_error + 0.8 * robust["integral"][index]
            self.assertEqual(nominal["reference"][index], expected_reference)
            self.assertAlmostEqual(nominal["command"][index], expected_nominal_command)
            self.assertAlmostEqual(robust["command"][index], expected_robust_command)
            self.assertAlmostEqual(
                nominal["speed"][index + 1],
                nominal["decay"] * nominal["speed"][index]
                + nominal["input"] * expected_nominal_command,
            )
            self.assertAlmostEqual(
                robust["integral"][index + 1],
                robust["integral"][index] + 0.02 * robust_error,
            )
        self.assertAlmostEqual(nominal["tracking_ise"], 0.20713356588115908)
        self.assertAlmostEqual(robust["tracking_ise"], 0.38021285022257995)
        self.assertLess(nominal["tracking_ise"], robust["tracking_ise"])
        self.assertAlmostEqual(nominal["command_effort"], 12.678090522965032)
        self.assertAlmostEqual(robust["command_effort"], 10.755342628367382)
        self.assertAlmostEqual(nominal["steady_speed"], 1)
        self.assertAlmostEqual(robust["steady_speed"], 1)
        self.assertAlmostEqual(robust["steady_command"], 1)
        self.assertTrue(nominal["stable"])
        self.assertTrue(robust["stable"])

    def test_independent_finite_design_selection_and_worst_case(self):
        selection = reference_selection()
        self.assertEqual(selection["kp"], 2)
        self.assertEqual(selection["ki"], 0.8)
        self.assertAlmostEqual(selection["score"], 1.76331826901075, places=12)
        self.assertLessEqual(
            max(
                selection["worst_effort"][kp_index][ki_index]
                for kp_index in range(len(KP_VALUES))
                for ki_index in range(len(KI_VALUES))
                if selection["feasible"][kp_index][ki_index]
            ),
            90,
        )
        selected_kp_index = KP_VALUES.index(2)
        selected_ki_index = KI_VALUES.index(0.8)
        self.assertAlmostEqual(
            selection["worst_effort"][selected_kp_index][selected_ki_index],
            84.54677730094271,
            places=11,
        )
        nominal_worst = reference_run(0.5, 2, design="nominal")
        robust_worst = reference_run(0.5, 2, design="robust")
        self.assertAlmostEqual(nominal_worst["tracking_ise"], 3.4960569186739505)
        self.assertAlmostEqual(robust_worst["tracking_ise"], selection["score"])
        self.assertLess(robust_worst["tracking_ise"], nominal_worst["tracking_ise"])
        self.assertGreater(
            robust_worst["command_effort"], nominal_worst["command_effort"]
        )
        self.assertAlmostEqual(nominal_worst["steady_speed"], 5 / 11)
        self.assertEqual(robust_worst["steady_speed"], 1)
        self.assertEqual(robust_worst["steady_command"], 4)
        self.assertGreater(robust_worst["final_error"], 0.14)

    def test_two_sweeps_are_independent_and_cross(self):
        gain_nominal = [
            reference_run(value, 1, design="nominal") for value in GAIN_VALUES
        ]
        gain_robust = [
            reference_run(value, 1, design="robust") for value in GAIN_VALUES
        ]
        self.assertTrue(all(run["drag_ratio"] == 1 for run in gain_nominal))
        self.assertAlmostEqual(gain_nominal[0]["tracking_ise"], 1.2833666492520681)
        self.assertAlmostEqual(gain_robust[-1]["tracking_ise"], 0.23438217453580218)
        self.assertLess(gain_nominal[2]["tracking_ise"], gain_robust[2]["tracking_ise"])
        self.assertGreater(gain_nominal[0]["tracking_ise"], gain_robust[0]["tracking_ise"])
        self.assertGreater(gain_nominal[-1]["tracking_ise"], gain_robust[-1]["tracking_ise"])

        drag_nominal = [
            reference_run(1, value, design="nominal") for value in DRAG_VALUES
        ]
        drag_robust = [
            reference_run(1, value, design="robust") for value in DRAG_VALUES
        ]
        self.assertTrue(
            all(run["actuator_gain_ratio"] == 1 for run in drag_nominal)
        )
        self.assertAlmostEqual(drag_nominal[0]["tracking_ise"], 0.7739874042026641)
        self.assertAlmostEqual(drag_robust[-1]["tracking_ise"], 0.7499735115322869)
        self.assertEqual(
            [run["steady_command"] for run in drag_robust], DRAG_VALUES
        )

    def test_broken_case_zero_limit_recovery_and_maximum_grid(self):
        broken_nominal = reference_run(actuator_sign=-1, design="nominal")
        broken_robust = reference_run(actuator_sign=-1, design="robust")
        self.assertFalse(broken_nominal["stable"])
        self.assertFalse(broken_robust["stable"])
        self.assertGreater(broken_nominal["pole_magnitude"], 1)
        self.assertGreater(broken_robust["pole_magnitude"], 1)
        self.assertTrue(broken_nominal["terminated"])
        self.assertTrue(broken_robust["terminated"])
        recovered_nominal_a = reference_run(design="nominal")
        recovered_nominal_b = reference_run(design="nominal")
        recovered_robust_a = reference_run(design="robust")
        recovered_robust_b = reference_run(design="robust")
        self.assertEqual(recovered_nominal_a["speed"], recovered_nominal_b["speed"])
        self.assertEqual(
            recovered_nominal_a["command"], recovered_nominal_b["command"]
        )
        self.assertEqual(recovered_robust_a["speed"], recovered_robust_b["speed"])
        self.assertEqual(recovered_robust_a["command"], recovered_robust_b["command"])

        for design in ("nominal", "robust"):
            zero = reference_run(1.5, 2, reference_speed=0, design=design)
            self.assertEqual(max(abs(value) for value in zero["speed"]), 0)
            self.assertEqual(max(abs(value) for value in zero["command"]), 0)
            self.assertEqual(zero["tracking_ise"], 0)
            bounded = reference_run(
                1.5,
                2,
                reference_speed=2,
                duration=20,
                time_step=0.004,
                design=design,
            )
            self.assertEqual(len(bounded["time"]), 5001)
            self.assertTrue(bounded["stable"])
            self.assertFalse(bounded["terminated"])
            self.assertTrue(all(math.isfinite(value) for value in bounded["speed"]))

    def test_zero_reference_is_unexcited_and_not_reported_as_a_design_win(self):
        for gain_ratio in GAIN_VALUES:
            for drag_ratio in DRAG_VALUES:
                for actuator_sign in (-1, 1):
                    for design in ("nominal", "robust"):
                        with self.subTest(
                            gain_ratio=gain_ratio,
                            drag_ratio=drag_ratio,
                            actuator_sign=actuator_sign,
                            design=design,
                        ):
                            result = reference_run(
                                gain_ratio,
                                drag_ratio,
                                actuator_sign=actuator_sign,
                                reference_speed=0,
                                design=design,
                            )
                            self.assertEqual(result["tracking_ise"], 0)
                            self.assertEqual(result["command_effort"], 0)
                            self.assertEqual(max(abs(value) for value in result["speed"]), 0)
                            self.assertEqual(max(abs(value) for value in result["command"]), 0)
                            self.assertFalse(result["terminated"])

        interactive = self.read("interactive.m")
        zero_branch = "if referenceSpeed == 0"
        broken_branch = "elseif actuatorSign < 0"
        matched_branch = "elseif gainRatio == 1 && dragRatio == 1"
        comparison_branch = (
            "elseif result.robust.trackingIntegralM2PerSec < ..."
        )
        self.assertIn(
            "zero reference: both designs remain at rest",
            interactive,
        )
        self.assertLess(interactive.index(zero_branch), interactive.index(broken_branch))
        self.assertLess(interactive.index(zero_branch), interactive.index(matched_branch))
        self.assertLess(interactive.index(zero_branch), interactive.index(comparison_branch))

    def test_experiment_has_ordered_flow_labels_metrics_sweeps_and_broken_case(self):
        experiment = self.read("experiment.m")
        ordered = (
            "%% Read:",
            "%% Make one prediction",
            "%% Visualize the deterministic baseline",
            "%% Read the robust selection mechanism",
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
            "actuatorGainRatioValues = [0.5 0.75 1 1.25 1.5]",
            "dragRatioValues = [0.5 0.75 1 1.5 2]",
            "changed = model(actuatorGainRatioValues(k),1,1,1,12,0.02)",
            "changed = model(1,dragRatioValues(k),1,1,12,0.02)",
            "worstCorner = model(0.5,2,1,1,12,0.02)",
            "broken = model(1,1,-1,1,12,0.02)",
            "recovered = model(1,1,1,1,12,0.02)",
            "Speed (m/s)",
            "Acceleration command (m/s^2)",
            "Tracking ISE (m^2/s)",
            "Command effort integral (m^2/s^3)",
            "Final absolute tracking error (m/s)",
            "Closed-loop pole magnitude (dimensionless)",
            "run_checks;",
        ):
            self.assertIn(marker, experiment)
        self.assertGreaterEqual(experiment.count("figure("), 6)
        self.assertEqual(experiment.count("%% Make one prediction"), 1)

    def test_interactive_has_meaningful_controls_reset_and_immediate_feedback(self):
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
            "Reference speed (m/s; 1 used for design)",
            "Reversed (broken)",
            "ValueChangingFcn",
            "ValueChangedFcn",
            "ButtonPushedFcn",
            "resetBaseline",
            "redraw(1,1,1,'Positive sign')",
            "result = modelFunction(gainRatio,dragRatio,actuatorSign, ...",
            "matched point: nominal wins tracking ISE",
            "worst-case improvement is not pointwise dominance",
            "design conditions: 1 m/s, 12 s, dt=0.02 s",
        ):
            self.assertIn(marker, interactive)
        self.assertGreaterEqual(interactive.count("uiaxes("), 2)

    def test_checks_cover_oracles_limits_malformed_recovery_and_bounds(self):
        checks = self.read("run_checks.m")
        for marker in (
            "isequaln(baselineA,baselineB)",
            "expectedDecay = exp(-0.02)",
            "expectedNominalSpeed",
            "expectedRobustIntegral",
            "independentCandidate",
            "independentWorstIse",
            "independentSelectedKp == 2",
            "worstCorner = model(0.5,2,1,1,12,0.02)",
            "actuatorGainRatioValues = [0.5 0.75 1 1.25 1.5]",
            "dragRatioValues = [0.5 0.75 1 1.5 2]",
            "matchedRatio = model(0.5,0.5,1,1,12,0.02)",
            "zeroReference = model(1.5,2,1,0,12,0.02)",
            "broken = model(1,1,-1,1,12,0.02)",
            "recovered = model(1,1,1,1,12,0.02)",
            "P20:ActuatorGainRatioRange",
            "P20:DragRatioRange",
            "P20:ActuatorSign",
            "P20:ReferenceSpeedRange",
            "P20:DurationRange",
            "P20:DisplayResolution",
            "P20:GridAlignment",
            "P20:EventAlignment",
            "P20:TooManySteps",
            "boundedGrid = model(1.5,2,1,2,20,0.004)",
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
            "P19",
            "actuator effectiveness",
            "drag",
            "nominal",
            "robust",
            "12 visible",
            "25 positive",
            "1 m/s",
            "dt=0.02 s",
            "worst-case",
            "command effort",
            "positive actuator",
            "reversed polarity",
            "exactly two sentences",
            "No MATLAB-runtime",
        ):
            self.assertIn(marker.lower(), combined.lower())
        for placeholder in ("scaffolded", "placeholder", "todo"):
            self.assertNotIn(placeholder, combined.lower())
        opaque_calls = (
            r"\b(?:lqr|dlqr|dare|idare|ss|c2d|lsim|tf|step|sim|inv|pinv|eig|"
            r"hinfsyn|mixsyn|musyn|systune|looptune|ureal|uss|robstab|robgain|"
            r"wcgain|augw|makeweight|feedback)\s*\("
        )
        for name in ("model.m", "experiment.m", "interactive.m", "run_checks.m", "lesson.m"):
            self.assertNotRegex(self.read(name).lower(), opaque_calls)

    def test_learner_frontier_documents_include_permanent_p20_facts(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("./bin/learn start P20", root_readme)
        self.assertIn("P20", start_here)
        p20_row = next(line for line in module_index.splitlines() if line.startswith("| P20 |"))
        self.assertTrue(p20_row.endswith("| implemented |"))

    def test_readme_path_scope_and_public_cli_state_isolation(self):
        readme = self.read("README.md")
        self.assertIn(
            'moduleFolder = fullfile(pwd,"modules","20-compare-nominal-and-robust-designs");',
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
                "current": "P19",
                "completed": {"P18": True},
                "notes": {"P18": "preserve prior note"},
            }
            progress_file.write_text(
                json.dumps(original, indent=2) + "\n", encoding="utf-8"
            )
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"

            checked = subprocess.run(
                [str(fixture / "bin/learn"), "check", "P20"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(checked.stdout, "Run in MATLAB: run_module_checks('P20')\n")
            self.assertEqual(json.loads(progress_file.read_text()), original)

            started = subprocess.run(
                [str(fixture / "bin/learn"), "start", "P20"],
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
            self.assertEqual(retained["current"], "P20")
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
                "Actuator gain and drag change tracking ISE and command effort, so the "
                "nominal matched advantage trades against robust worst-grid behavior. "
                "The finite grid assumes positive gain; reversed polarity diverges."
            )
            completed = subprocess.run(
                [
                    str(fixture / "bin/learn"),
                    "complete",
                    "P20",
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
            self.assertEqual(retained["completed"], {"P18": True, "P20": True})
            self.assertEqual(retained["notes"]["P18"], "preserve prior note")
            self.assertEqual(retained["notes"]["P20"], teach_back)


if __name__ == "__main__":
    unittest.main()
