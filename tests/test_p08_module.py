from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTION = (
    "What inputs, observable effects, and failure modes matter when you reject "
    "a Disturbance with Feedback?"
)


def step_equilibrium(
    gain: float, disturbance: float, sensor_bias: float
) -> tuple[float, float, float]:
    """Independent equilibrium of -y-K(y+b)+d=0."""
    true_output = (disturbance - gain * sensor_bias) / (1 + gain)
    measured_output = true_output + sensor_bias
    control_effort = -gain * measured_output
    return true_output, measured_output, control_effort


def frequency_metrics(gain: float, omega: float) -> tuple[float, float, float]:
    """Independent tau=1 disturbance amplitude, phase, and feedback ratio."""
    amplitude = 1 / math.sqrt((1 + gain) ** 2 + omega**2)
    phase_deg = -math.degrees(math.atan2(omega, 1 + gain))
    ratio = math.sqrt(1 + omega**2) / math.sqrt((1 + gain) ** 2 + omega**2)
    return amplitude, phase_deg, ratio


def exact_step_output(gain: float, disturbance: float, elapsed: float) -> float:
    """Independent zero-state response after an unbiased step begins."""
    return disturbance / (1 + gain) * (1 - math.exp(-(1 + gain) * elapsed))


def exact_sine_output(
    gain: float, disturbance: float, omega: float, elapsed: float
) -> float:
    """Independent zero-state response after a zero-phase sine begins."""
    rate = 1 + gain
    return disturbance * (
        rate * math.sin(omega * elapsed)
        - omega * math.cos(omega * elapsed)
        + omega * math.exp(-rate * elapsed)
    ) / (rate**2 + omega**2)


def reference_rk4_step(
    gain: float, disturbance: float, times: list[float], start: float = 1.0
) -> list[float]:
    """Independent RK4 history with an explicit split at disturbance onset."""
    state = 0.0
    history = [state]

    def rate(current: float) -> float:
        return -(1 + gain) * current + disturbance

    for interval_start, interval_end in zip(times, times[1:]):
        if interval_end <= start:
            history.append(state)
            continue
        integration_start = max(interval_start, start)
        step = interval_end - integration_start
        k1 = rate(state)
        k2 = rate(state + step * k1 / 2)
        k3 = rate(state + step * k2 / 2)
        k4 = rate(state + step * k3)
        state += step * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        history.append(state)
    return history


class P08ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P08"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 8)
        self.assertEqual(self.module["title"], "Reject a Disturbance with Feedback")
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["phase"], 2)
        self.assertEqual(self.module["prerequisites"], ["P07"])
        self.assertEqual(self.module["implementation_batch"], "P08")
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
            "controlEffort = -feedbackGain*measuredOutput",
            "rate = (-trueOutput+controlEffort+disturbance)/plantTimeConstantSec",
            "state = state + step*(k1+2*k2+2*k3+k4)/6",
            "closedLoopDisturbanceMagnitude = 1./sqrt((1+feedbackGain)^2+",
            "feedbackRejectionRatio = sqrt(1+",
            "disturbanceDcTrueOutput = disturbanceAmplitude/(1+feedbackGain)",
            "biasTrueOffset = -feedbackGain*sensorBias/(1+feedbackGain)",
            "integrationStart = max(intervalStart,disturbanceStartSec)",
            "plantTimeConstantSec = 1",
        ):
            self.assertIn(formula, model)
        for validation in (
            "mustBeReal",
            "mustBeFinite",
            "mustBePositive",
            "mustBeNonnegative",
            "maxSamples = 20001",
            "maxDimensionlessStep = 0.1",
            "responseLimit = 9",
            "P08:TimeResolution",
            "P08:ResponseBound",
            "P08:TooManySamples",
        ):
            self.assertIn(validation, model)
        self.assertNotRegex(
            model.lower(), r"\b(?:plot|figure|uifigure|uiaxes|uislider|uispinner)\s*\("
        )

    def test_independent_equilibrium_frequency_and_limiting_arithmetic(self):
        baseline = step_equilibrium(4, 1, 0)
        no_feedback = step_equilibrium(0, 1, 0)
        broken = step_equilibrium(9, 0, 0.5)
        high_gain_bias = step_equilibrium(20, 0, 0.5)
        recovered = step_equilibrium(9, 0, 0)

        self.assertEqual(baseline, (0.2, 0.2, -0.8))
        self.assertEqual(no_feedback, (1.0, 1.0, 0.0))
        for actual, expected in zip(broken, (-0.45, 0.05, -0.45)):
            self.assertAlmostEqual(actual, expected)
        self.assertEqual(recovered, (0.0, 0.0, 0.0))
        self.assertGreater(abs(high_gain_bias[0]), abs(broken[0]))
        self.assertLess(abs(high_gain_bias[1]), abs(broken[1]))

        dc = frequency_metrics(4, 0)
        medium = frequency_metrics(4, 1)
        fast = frequency_metrics(4, 15)
        self.assertEqual(dc, (0.2, -0.0, 0.2))
        self.assertAlmostEqual(medium[0], 1 / math.sqrt(26), places=14)
        self.assertAlmostEqual(medium[1], -math.degrees(math.atan(0.2)), places=14)
        self.assertAlmostEqual(fast[0], 1 / math.sqrt(250), places=14)
        self.assertLess(dc[0], medium[0] + 0.01)
        self.assertGreater(medium[0], fast[0])
        self.assertLess(dc[2], medium[2])
        self.assertLess(medium[2], fast[2])
        self.assertLess(fast[2], 1)
        self.assertEqual(frequency_metrics(0, 7)[2], 1)

        self.assertAlmostEqual(exact_step_output(4, 1, 0.05), 0.0442398434, places=9)
        self.assertAlmostEqual(exact_step_output(4, 1, 4), 0.2, places=8)
        self.assertAlmostEqual(1 / (1 + 4), 0.2)
        self.assertAlmostEqual(4 / (1 + 4), 0.8)

    def test_sinusoidal_time_response_behavioral_regression(self):
        self.assertEqual(exact_sine_output(4, 1, 1, 0), 0)
        self.assertAlmostEqual(
            exact_sine_output(4, 1, 1, 0.25), 0.021331237362391, places=14
        )
        self.assertAlmostEqual(
            exact_sine_output(4, 1, 1, 1), 0.141299637121940, places=14
        )
        self.assertAlmostEqual(
            exact_sine_output(4, 1, 1, 3), 0.065215109338542, places=14
        )

        checks = self.read("run_checks.m")
        for marker in (
            "sineBehavior = model(4,1,1,0,4,0.005)",
            "expectedSineOutput = zeros(size(sineBehavior.t))",
            "5*sin(sineElapsed(sineActive))-cos(sineElapsed(sineActive))+",
            "sineBehavior.trueOutput-expectedSineOutput",
            "independent transient",
        ):
            self.assertIn(marker, checks)

    def test_independent_rk4_history_and_onset_crossing_regression(self):
        regular_times = [index * 0.01 for index in range(401)]
        regular_history = reference_rk4_step(4, 1, regular_times)
        maximum_error = max(
            abs(actual - (0 if time <= 1 else exact_step_output(4, 1, time - 1)))
            for time, actual in zip(regular_times, regular_history)
        )
        self.assertLess(maximum_error, 2e-7)

        crossing_times = [index * 0.018 for index in range(57)]
        self.assertLess(crossing_times[-2], 1)
        self.assertGreater(crossing_times[-1], 1)
        crossing_history = reference_rk4_step(4, 1, crossing_times)
        expected = exact_step_output(4, 1, crossing_times[-1] - 1)
        self.assertAlmostEqual(crossing_history[-1], expected, places=9)
        self.assertTrue(
            all(
                output == 0
                for time, output in zip(crossing_times, crossing_history)
                if time <= 1
            )
        )

    def test_experiment_has_views_metrics_two_isolated_sweeps_and_recovery(self):
        experiment = self.read("experiment.m")
        lowered = experiment.lower()
        self.assertGreaterEqual(experiment.count("%%"), 12)
        self.assertIn("sweep 1 - move only feedback gain", lowered)
        self.assertIn(
            "sweep 2 - reset gain and move only disturbance frequency", lowered
        )
        self.assertIn(
            "broken case - treat sensor bias as a plant-input disturbance", lowered
        )
        self.assertIn(
            "the violated assumption is that measured output equals true output",
            lowered,
        )
        self.assertIn("feedbackgains = [0 1 4 9]", lowered)
        self.assertIn(
            "disturbancefrequenciesradpersec = [0.2 1 5 15]", lowered
        )
        self.assertIn("broken = model(9,0,0,0.5,8,0.005)", lowered)
        self.assertIn("recovered = model(9,0,0,0,8,0.005)", lowered)
        self.assertGreaterEqual(lowered.count("xlabel("), 8)
        self.assertGreaterEqual(lowered.count("ylabel("), 8)
        self.assertGreaterEqual(lowered.count("fprintf("), 2)
        for unit in ("(s)", "(rad/s)", "(dimensionless)", "(output)", "(db)"):
            self.assertIn(unit, lowered)

    def test_interactive_controls_are_bounded_immediate_and_resettable(self):
        interactive = self.read("interactive.m")
        for marker in (
            "Feedback gain K (dimensionless)",
            "Disturbance frequency omega (rad/s; 0 = step)",
            "Limits',[0 10]",
            "Reset baseline",
            "gainControl.Value = 4",
            "frequencyControl.Value = 0",
            "ValueChangingFcn",
            "ValueChangedFcn",
            "modelFunction = @model",
            "viewDt = min(0.01,0.08/max(1+feedbackGain,",
            "result = modelFunction(feedbackGain,1,",
            "With-feedback / no-feedback ratio",
            "Time (s)",
        ):
            self.assertIn(marker, interactive)

    def test_checks_cover_invariants_limits_failures_recovery_and_resources(self):
        checks = self.read("run_checks.m")
        self.assertGreaterEqual(checks.count("assert("), 27)
        for marker in (
            "isequaln(baselineA,baselineB)",
            "plantResidual",
            "expectedOpenMagnitude",
            "expectedClosedMagnitude",
            "expectedStepOutput",
            "model(0,1,0,0,8,0.01)",
            "model(9,1,0,0,8,0.005)",
            "model(4,1,0.2,0,16,0.005)",
            "model(4,1,15,0,16,0.005)",
            "model(4,0,3,0,4,0.01)",
            "model(4,-1,0,0,8,0.01)",
            "broken = model(9,0,0,0.5,8,0.005)",
            "recovered = model(9,0,0,0,8,0.005)",
            "model(NaN,1,0,0,12,0.01)",
            "model(4,Inf,0,0,12,0.01)",
            "model(4,1,0,0,[10 12],0.01)",
            "P08:TimeResolution",
            "P08:ResponseBound",
            "coarse = model(4,1,0,0,4,0.01)",
            "fine = model(4,1,0,0,4,0.005)",
            "crossingGrid = model(4,1,0,0,1.008,0.018)",
            "all(diff(nonIntegerGrid.t) > 0)",
            "shortHorizon.sampleCount == 2",
            "atResourceLimit.sampleCount == 20001",
            "P08:TooManySamples",
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
            r"\b(?:tf|margin|bode|freqresp|feedback|step|lsim|initial|impulse|roots|eig|damp|c2d|ss|pole|expm|ode45|ode23|sim)\s*\(",
        )
        model_lowered = self.read("model.m").lower()
        self.assertNotRegex(
            model_lowered,
            r"\b(?:rng|rand|randn|load|save|fopen|readtable|writetable|webread|system|timer|pause|parfeval)\s*\(|\b(?:global|persistent)\b",
        )
        for marker in (
            QUESTION,
            "P06",
            "P07",
            "teach-back",
            "mechanism",
            "plant-input disturbance",
            "sensor bias",
        ):
            self.assertIn(marker, combined)


if __name__ == "__main__":
    unittest.main()
