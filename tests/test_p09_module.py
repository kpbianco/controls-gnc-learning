from __future__ import annotations

import cmath
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTION = (
    "What inputs, observable effects, and failure modes matter when you "
    "discretize a Continuous Controller?"
)


def discrete_poles(sample_period: float, method: str) -> tuple[complex, complex]:
    """Independent poles for the exact held plant and an Euler PI update."""
    decay = math.exp(-sample_period)
    input_weight = 1 - decay
    a11 = decay - 2 * input_weight
    if method == "backward-euler":
        a11 -= input_weight * 4 * sample_period
    a12 = input_weight * 4
    a21 = -sample_period
    trace = a11 + 1
    determinant = a11 - a12 * a21
    discriminant = trace**2 - 4 * determinant
    return (
        (trace + cmath.sqrt(discriminant)) / 2,
        (trace - cmath.sqrt(discriminant)) / 2,
    )


def sampled_response(
    sample_period: float, method: str, horizon: float
) -> tuple[list[float], list[float], list[float]]:
    """Independent controller-sample simulation of the governing recurrences."""
    decay = math.exp(-sample_period)
    input_weight = 1 - decay
    sample_count = math.floor(horizon / sample_period) + 1
    output = [0.0]
    control: list[float] = []
    integral_used: list[float] = []
    integral = 0.0
    for index in range(sample_count):
        error = 1 - output[index]
        if method == "backward-euler":
            integral += sample_period * error
        integral_used.append(integral)
        control.append(2 * error + 4 * integral)
        if method == "forward-euler":
            integral += sample_period * error
        if index < sample_count - 1:
            output.append(decay * output[index] + input_weight * control[index])
    return output, control, integral_used


def continuous_target(time: float) -> float:
    """Independent closed-form output of the fixed continuous PI target."""
    alpha = 1.5
    beta = math.sqrt(7) / 2
    sine_weight = 0.5 / beta
    return 1 + math.exp(-alpha * time) * (
        -math.cos(beta * time) + sine_weight * math.sin(beta * time)
    )


class P09ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P09"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 9)
        self.assertEqual(self.module["title"], "Discretize a Continuous Controller")
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["phase"], 3)
        self.assertEqual(self.module["phase_title"], "Digital and constrained control")
        self.assertEqual(self.module["prerequisites"], ["P08"])
        self.assertEqual(self.module["implementation_batch"], "P09")
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
            "plantDecay = exp(-samplePeriodSec/plantTimeConstantSec)",
            "plantInputWeight = 1-plantDecay",
            "integralState = integralState+samplePeriodSec*errorSamples(k)",
            "controlSamples(k) = proportionalGain*errorSamples(k)+",
            "plantDecay*digitalOutputSamples(k)+",
            "poleDiscriminant = poleTrace^2-4*poleDeterminant",
            "digitalOutput(active) = controlSamples(k)+("
        ):
            self.assertIn(formula, model)
        for validation in (
            "mustBeReal",
            "mustBeFinite",
            "mustBePositive",
            "maxControllerSamples = 10001",
            "maxDisplaySamples = 20001",
            "responseLimit = 1000",
            "P09:UnknownMethod",
            "P09:DisplayResolution",
            "P09:TooManyControllerSamples",
            "P09:TooManyDisplaySamples",
            "P09:ResponseBound",
        ):
            self.assertIn(validation, model)
        self.assertLess(
            model.index("controllerSampleCount > maxControllerSamples"),
            model.index("sampleTimes = (0:controllerIntervalCount)'"),
        )
        self.assertLess(
            model.index("regularDisplaySampleCount > maxDisplaySamples"),
            model.index("t = (0:displayIntervalCount)'"),
        )
        self.assertNotRegex(
            model.lower(), r"\b(?:plot|figure|uifigure|uiaxes|uislider|uidropdown)\s*\("
        )

    def test_independent_poles_limits_and_broken_recovery(self):
        forward_baseline = discrete_poles(0.05, "forward-euler")
        backward_baseline = discrete_poles(0.05, "backward-euler")
        broken = discrete_poles(0.8, "forward-euler")
        recovered = discrete_poles(0.05, "forward-euler")

        self.assertAlmostEqual(max(map(abs, forward_baseline)), 0.9292160075041751)
        self.assertAlmostEqual(max(map(abs, backward_baseline)), 0.9239525277318862)
        self.assertGreater(max(map(abs, broken)), 1.05)
        self.assertLess(max(map(abs, recovered)), 1)
        self.assertLess(max(map(abs, discrete_poles(0.005, "forward-euler"))), 1)
        self.assertLess(max(map(abs, discrete_poles(0.005, "backward-euler"))), 1)

        for method in ("forward-euler", "backward-euler"):
            with self.subTest(method=method):
                fine = discrete_poles(1e-6, method)
                continuous_poles = (-1.5 + math.sqrt(7) / 2j, -1.5 - math.sqrt(7) / 2j)
                mapped_rates = tuple(cmath.log(pole) / 1e-6 for pole in fine)
                for actual, expected in zip(mapped_rates, continuous_poles):
                    self.assertAlmostEqual(actual.real, expected.real, places=5)
                    self.assertAlmostEqual(abs(actual.imag), abs(expected.imag), places=4)

    def test_independent_sampled_state_behavioral_regression(self):
        forward_output, forward_control, forward_integral = sampled_response(
            0.05, "forward-euler", 12
        )
        backward_output, backward_control, backward_integral = sampled_response(
            0.05, "backward-euler", 12
        )
        broken_output, _, _ = sampled_response(0.8, "forward-euler", 12)

        self.assertEqual(forward_control[0], 2)
        self.assertEqual(forward_integral[0], 0)
        self.assertAlmostEqual(backward_control[0], 2.2)
        self.assertAlmostEqual(backward_integral[0], 0.05)
        self.assertAlmostEqual(forward_output[1], 2 * (1 - math.exp(-0.05)))
        self.assertAlmostEqual(
            backward_output[1], 2.2 * (1 - math.exp(-0.05))
        )
        self.assertAlmostEqual(forward_output[-1], 0.999999994700982, places=14)
        self.assertAlmostEqual(backward_output[-1], 1.000000005619583, places=14)
        self.assertAlmostEqual(broken_output[-1], 2.791121098500019, places=13)
        self.assertGreater(max(broken_output), 2.8)
        self.assertLess(min(broken_output), -0.9)

        checks = self.read("run_checks.m")
        for marker in (
            "sampleTransitionResidual",
            "expectedBackwardIntegral = 0.05*cumsum",
            "expectedForwardIntegral = [0; 0.05*cumsum(",
            "poleResidual = baselineA.discretePoles.^2-",
            "displayedAtSamples = baselineA.digitalOutput(1:5:end)",
            "broken = model(0.8,'forward-euler',12,0.01)",
            "recovered = model(0.05,'forward-euler',12,0.01)",
        ):
            self.assertIn(marker, checks)

    def test_partial_zero_order_hold_behavioral_regression(self):
        sample_period = 0.03
        horizon = 0.1
        sampled_output, control, _ = sampled_response(
            sample_period, "forward-euler", horizon
        )
        sample_times = [index * sample_period for index in range(len(control))]
        display_times = [index / 100 for index in range(11)]
        displayed_output: list[float] = []
        held_control: list[float] = []

        for time in display_times:
            active = max(
                index
                for index, sample_time in enumerate(sample_times)
                if sample_time <= time + 1e-15
            )
            elapsed = time - sample_times[active]
            command = control[active]
            held_control.append(command)
            displayed_output.append(
                command
                + (sampled_output[active] - command) * math.exp(-elapsed)
            )

        for display_index, sample_index in zip((0, 3, 6, 9), range(4)):
            self.assertAlmostEqual(
                displayed_output[display_index], sampled_output[sample_index]
            )
        self.assertEqual(held_control[:3], [control[0]] * 3)
        self.assertEqual(held_control[9:], [control[-1]] * 2)
        self.assertGreater(displayed_output[1], displayed_output[0])
        self.assertGreater(displayed_output[2], displayed_output[1])
        self.assertAlmostEqual(displayed_output[-1], 0.19031748451877695)

        checks = self.read("run_checks.m")
        for marker in (
            "lastHoldElapsedSec = nonIntegerGrid.t(end)-",
            "expectedFinalHeldOutput = nonIntegerGrid.controlSamples(end)+(",
            "all(nonIntegerGrid.heldControl(lastHold) ==",
            "abs(nonIntegerGrid.digitalOutput(end)-expectedFinalHeldOutput)",
        ):
            self.assertIn(marker, checks)

    def test_continuous_target_reference_arithmetic(self):
        self.assertEqual(continuous_target(0), 0)
        self.assertAlmostEqual(continuous_target(0.05), 0.09746189162278429)
        self.assertAlmostEqual(continuous_target(1), 1.0270030737413396)
        self.assertAlmostEqual(continuous_target(4), 0.9978593026452696)
        self.assertAlmostEqual(continuous_target(12), 1.0000000140649796)

        model = self.read("model.m")
        for marker in (
            "continuousDecayRatePerSec = (1+proportionalGain)/2",
            "continuousDampedFrequencyRadPerSec = sqrt(",
            "continuousOutput = reference+decayingEnvelope.*(",
            "continuousDerivative = decayingEnvelope.*(",
            "continuousControl = continuousOutput+continuousDerivative",
        ):
            self.assertIn(marker, model)

    def test_experiment_has_views_metrics_two_isolated_sweeps_and_recovery(self):
        experiment = self.read("experiment.m")
        lowered = experiment.lower()
        self.assertGreaterEqual(experiment.count("%%"), 13)
        self.assertIn("sweep 1 - move only sample period", lowered)
        self.assertIn(
            "sweep 2 - reset sample period and move only the integration rule",
            lowered,
        )
        self.assertIn(
            "broken case - violate the resolved-sampling assumption", lowered
        )
        self.assertIn("sampleperiodssec = [0.02 0.05 0.1 0.2 0.4]", lowered)
        self.assertIn(
            "discretizationmethods = {'forward-euler','backward-euler'}", lowered
        )
        self.assertIn("broken = model(0.8,'forward-euler',12,0.01)", lowered)
        self.assertIn("recovered = model(0.05,'forward-euler',12,0.01)", lowered)
        self.assertGreaterEqual(lowered.count("xlabel("), 9)
        self.assertGreaterEqual(lowered.count("ylabel("), 9)
        self.assertGreaterEqual(lowered.count("fprintf("), 2)
        for unit in ("(s)", "(1/s)", "(rad/s)", "(dimensionless)", "(output)"):
            self.assertIn(unit, lowered)

    def test_interactive_controls_are_bounded_immediate_and_resettable(self):
        interactive = self.read("interactive.m")
        for marker in (
            "Sample period Ts (s)",
            "Integral discretization rule",
            "Limits',[0.02 0.6]",
            "Items',{'backward-euler','forward-euler'}",
            "Reset baseline",
            "periodControl.Value = 0.05",
            "methodControl.Value = 'backward-euler'",
            "ValueChangingFcn",
            "ValueChangedFcn",
            "modelFunction = @model",
            "result = modelFunction(samplePeriodSec,discretizationMethod,12,0.01)",
            "stairs(axControl,result.t,result.heldControl,",
            "samples/period",
            "not strictly inside unit circle",
            "Time (s)",
        ):
            self.assertIn(marker, interactive)

    def test_checks_cover_limits_malformed_inputs_recovery_and_resources(self):
        checks = self.read("run_checks.m")
        self.assertGreaterEqual(checks.count("assert("), 28)
        for marker in (
            "isequaln(baselineA,baselineB)",
            "model(0.02,'backward-euler',8,0.01)",
            "model(0.4,'backward-euler',8,0.01)",
            "model(0.005,'forward-euler',4,0.005)",
            "model(NaN,'forward-euler',12,0.01)",
            "model(0.05,'forward-euler',Inf,0.01)",
            "model(0.05,'forward-euler',12,[0.01 0.02])",
            "model(0.05,7,12,0.01)",
            "P09:UnknownMethod",
            "P09:SamplePeriodRange",
            "P09:HorizonRange",
            "P09:DisplayResolution",
            "P09:TooManyControllerSamples",
            "P09:TooManyDisplaySamples",
            "P09:ResponseBound",
            "model(1e-12,'forward-euler',60,1e-12)",
            "model(0.05,'forward-euler',60,1e-12)",
            "nonIntegerGrid = model(0.03,'forward-euler',0.1,0.01)",
            "atControllerLimit.controllerSampleCount == 10001",
            "atDisplayLimit.displaySampleCount == 20001",
        ):
            self.assertIn(marker, checks)

    def test_content_is_concept_first_isolated_and_has_no_opaque_path(self):
        names = (
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
        combined = "\n".join(self.read(name) for name in names)
        lowered = combined.lower()
        self.assertNotIn("scaffolded", lowered)
        self.assertNotRegex(lowered, r"\b(?:todo|placeholder)\b")
        self.assertNotRegex(
            lowered,
            r"\b(?:c2d|d2c|tf|zpk|ss|feedback|step|lsim|initial|impulse|"
            r"roots|eig|expm|ode45|ode23|sim)\s*\(",
        )
        model_lowered = self.read("model.m").lower()
        self.assertNotRegex(
            model_lowered,
            r"\b(?:rng|rand|randn|load|save|fopen|readtable|writetable|webread|"
            r"system|timer|pause|parfeval)\s*\(|\b(?:global|persistent)\b",
        )
        for marker in (
            QUESTION,
            "P06",
            "P07",
            "P08",
            "teach-back",
            "mechanism",
            "zero-order hold",
            "sample period",
            "pole magnitude",
            "loss of asymptotic convergence",
        ):
            self.assertIn(marker, combined)
        self.assertNotIn("reaches one—growth", lowered)


if __name__ == "__main__":
    unittest.main()
