from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTION = (
    "What inputs, observable effects, and failure modes matter when you see "
    "Stability Margin in Time and Frequency?"
)


def gain_crossover(loop_gain: float, actuator_lag: float) -> float:
    """Independent bisection of |L(jw)|=1 for the documented factors."""
    lower, upper = 0.0, loop_gain

    def denominator(omega: float) -> float:
        return (
            omega
            * math.sqrt(1 + omega**2)
            * math.sqrt(1 + (actuator_lag * omega) ** 2)
        )

    for _ in range(100):
        midpoint = (lower + upper) / 2
        if denominator(midpoint) < loop_gain:
            lower = midpoint
        else:
            upper = midpoint
    return (lower + upper) / 2


def reference_response(
    loop_gain: float,
    actuator_lag: float,
    duration: float,
    interval: float,
) -> list[float]:
    """Independent RK4 reference for the P07 state equations."""
    return [
        state[0]
        for state in reference_state_response(
            loop_gain, actuator_lag, duration, interval
        )
    ]


def reference_state_response(
    loop_gain: float,
    actuator_lag: float,
    duration: float,
    interval: float,
) -> list[tuple[float, ...]]:
    """Independent RK4 histories for every P07 propagated state."""
    state = [0.0, 0.0, 0.0] if actuator_lag else [0.0, 0.0]
    histories: list[tuple[float, ...]] = []

    def rate(current: list[float]) -> list[float]:
        output, velocity = current[:2]
        command = loop_gain * (1.0 - output)
        if actuator_lag:
            actuator = current[2]
            return [
                velocity,
                actuator - velocity,
                (command - actuator) / actuator_lag,
            ]
        return [velocity, command - velocity]

    steps = round(duration / interval)
    for index in range(steps + 1):
        histories.append(tuple(state))
        if index == steps:
            break
        k1 = rate(state)
        k2 = rate([value + interval * slope / 2 for value, slope in zip(state, k1)])
        k3 = rate([value + interval * slope / 2 for value, slope in zip(state, k2)])
        k4 = rate([value + interval * slope for value, slope in zip(state, k3)])
        state = [
            value + interval * (s1 + 2 * s2 + 2 * s3 + s4) / 6
            for value, s1, s2, s3, s4 in zip(state, k1, k2, k3, k4)
        ]
    return histories


class P07ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P07"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 7)
        self.assertEqual(
            self.module["title"], "See Stability Margin in Time and Frequency"
        )
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["prerequisites"], ["P06"])
        self.assertEqual(self.module["implementation_batch"], "P07")
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
            "controllerCommand = loopGain*trackingError",
            "accelerationPerSec2 = actuator-",
            "actuatorRatePerSec = (controllerCommand-actuator)/actuatorLagSec",
            "openLoopMagnitude = loopGain./(omegaRadPerSec.*",
            "atan(omegaRadPerSec/plantDampingRatePerSec)*180/pi-",
            "(1+plantDampingRatePerSec*actuatorLagSec)/actuatorLagSec",
            "state = state + step*(k1+2*k2+2*k3+k4)/6",
            "plantDampingRatePerSec = 1",
        ):
            self.assertIn(formula, model)
        for validation in (
            "mustBeReal",
            "mustBeFinite",
            "mustBePositive",
            "mustBeNonnegative",
            "maxSamples = 20001",
            "maxDimensionlessStep = 0.1",
            "responseLimit = 1e4",
            "P07:TimeResolution",
            "P07:ResponseBound",
            "P07:TooManySamples",
        ):
            self.assertIn(validation, model)
        self.assertNotRegex(
            model.lower(), r"\b(?:plot|figure|uifigure|uiaxes|uislider|uispinner)\s*\("
        )

    def test_independent_margin_arithmetic_sweeps_failure_and_limits(self):
        baseline_wc = gain_crossover(1.0, 0.2)
        baseline_pm = 90 - math.degrees(math.atan(baseline_wc)) - math.degrees(
            math.atan(0.2 * baseline_wc)
        )
        low_gain_wc = gain_crossover(0.5, 0.2)
        high_gain_wc = gain_crossover(5.5, 0.2)
        broken_wc = gain_crossover(4.0, 0.5)
        broken_pm = 90 - math.degrees(math.atan(broken_wc)) - math.degrees(
            math.atan(0.5 * broken_wc)
        )
        tiny_wc = gain_crossover(1e-30, 0.2)

        self.assertAlmostEqual(baseline_wc, 0.7793432004, places=9)
        self.assertAlmostEqual(baseline_pm, 43.2098453074, places=9)
        self.assertLess(low_gain_wc, baseline_wc)
        self.assertGreater(high_gain_wc, baseline_wc)
        self.assertAlmostEqual((1 + 0.2) / 0.2, 6.0)
        self.assertAlmostEqual(1 / math.sqrt(0.2), math.sqrt(5))
        self.assertAlmostEqual(20 * math.log10(6), 15.5630250077, places=9)
        self.assertLess(broken_pm, 0)
        self.assertLess(((1 + 0.5) / 0.5) / 4, 1)
        self.assertAlmostEqual(tiny_wc / 1e-30, 1.0, places=12)

        baseline = reference_response(1.0, 0.2, 20.0, 0.01)
        low_gain = reference_response(0.5, 0.2, 20.0, 0.01)
        high_gain = reference_response(5.5, 0.2, 30.0, 0.01)
        short_lag = reference_response(1.0, 0.05, 20.0, 0.005)
        long_lag = reference_response(1.0, 0.8, 30.0, 0.005)
        broken = reference_response(4.0, 0.5, 30.0, 0.005)
        recovered = reference_response(1.0, 0.5, 30.0, 0.005)
        self.assertAlmostEqual(max(baseline) - 1, 0.2536539408, places=8)
        self.assertLess(max(low_gain), max(baseline))
        self.assertGreater(max(high_gain), max(baseline))
        self.assertLess(max(short_lag), max(long_lag))
        self.assertGreater(max(abs(value) for value in broken), 10)
        self.assertLess(max(abs(value) for value in recovered), 1.5)

        samples_at_limit = math.floor(20.0 / 0.001) + 1
        samples_over_limit = math.floor(20.001 / 0.001) + 1
        self.assertEqual(samples_at_limit, 20001)
        self.assertGreater(samples_over_limit, 20001)

    def test_experiment_has_views_metrics_two_isolated_sweeps_and_recovery(self):
        experiment = self.read("experiment.m")
        lowered = experiment.lower()
        self.assertGreaterEqual(experiment.count("%%"), 11)
        self.assertIn("sweep 1 - move only loop gain", lowered)
        self.assertIn("sweep 2 - reset gain and move only actuator lag", lowered)
        self.assertIn(
            "broken case - trust an instantaneous actuator at high gain", lowered
        )
        self.assertIn("the violated assumption is omitted actuator lag", lowered)
        self.assertIn("optimistic = model(4,0,20,0.005)", lowered)
        self.assertIn("broken = model(4,0.5,30,0.005)", lowered)
        self.assertIn("recovered = model(1,0.5,30,0.005)", lowered)
        self.assertIn("model(loopgains(k),actuatorlagsec,30,0.01)", lowered)
        self.assertIn("model(loopgain,actuatorlagssec(k),30,0.004)", lowered)
        self.assertGreaterEqual(lowered.count("xlabel("), 7)
        self.assertGreaterEqual(lowered.count("ylabel("), 7)
        self.assertGreaterEqual(lowered.count("fprintf("), 3)
        for unit in ("(s)", "(1/s^2)", "(rad/s)", "(db)", "(deg)", "normalized"):
            self.assertIn(unit, lowered)

    def test_independent_coupled_state_behavioral_regression(self):
        interval = 0.002
        histories = reference_state_response(0.15, 0.8, 4.0, interval)
        maximum_errors = [0.0, 0.0, 0.0]
        for index, (output, velocity, actuator) in enumerate(histories):
            time = index * interval
            expected = (
                1
                + 1.5 * math.exp(-0.5 * time)
                - 0.1 * math.exp(-1.5 * time)
                - 2.4 * math.exp(-0.25 * time),
                -0.75 * math.exp(-0.5 * time)
                + 0.15 * math.exp(-1.5 * time)
                + 0.6 * math.exp(-0.25 * time),
                -0.375 * math.exp(-0.5 * time)
                - 0.075 * math.exp(-1.5 * time)
                + 0.45 * math.exp(-0.25 * time),
            )
            maximum_errors = [
                max(maximum, abs(actual - exact))
                for maximum, actual, exact in zip(
                    maximum_errors, (output, velocity, actuator), expected
                )
            ]

        self.assertTrue(all(error < 1e-11 for error in maximum_errors))

    def test_matlab_checks_retain_coupled_state_behavioral_regression(self):
        checks = self.read("run_checks.m")
        for marker in (
            "factoredPoleCase = model(0.15,0.8,4,0.002)",
            "s^3+2.25*s^2+1.25*s+0.1875=(s+0.25)*(s+0.5)*(s+1.5)",
            "expectedFactoredOutput = 1+1.5*exp(-0.5*factoredPoleCase.t)-",
            "expectedFactoredVelocity = -0.75*exp(-0.5*factoredPoleCase.t)+",
            "expectedFactoredActuator = -0.375*exp(-0.5*factoredPoleCase.t)-",
            "factoredPoleCase.output-expectedFactoredOutput",
            "factoredPoleCase.velocityPerSec-expectedFactoredVelocity",
            "factoredPoleCase.actuator-expectedFactoredActuator",
            "independently factored three-pole",
        ):
            self.assertIn(marker, checks)

    def test_interactive_controls_are_meaningful_bounded_and_resettable(self):
        interactive = self.read("interactive.m")
        for marker in (
            "Loop gain K (1/s^2)",
            "Actuator lag tau (s)",
            "Limits',[0.25 5.5]",
            "Limits',[0.05 0.8]",
            "Reset baseline",
            "gainControl.Value = 1",
            "lagControl.Value = 0.2",
            "modelFunction = @model",
            "viewDt = min(0.01,0.08/max([1 sqrt(loopGain) 1/actuatorLagSec]))",
            "result = modelFunction(loopGain,actuatorLagSec,20,viewDt)",
            "Angular frequency (rad/s)",
            "Open-loop phase (deg)",
        ):
            self.assertIn(marker, interactive)

    def test_checks_cover_invariants_limits_failures_recovery_and_resources(self):
        checks = self.read("run_checks.m")
        self.assertGreaterEqual(checks.count("assert("), 25)
        for marker in (
            "isequaln(baselineA,baselineB)",
            "plantResidual",
            "actuatorResidual",
            "expectedMagnitude",
            "expectedPhase",
            "tinyGain = model(1e-30,0.2,1,0.01)",
            "baselineA.phaseCrossoverRadPerSec-sqrt(5)",
            "abs(baselineA.criticalLoopGain-6) < tolerance",
            "model(0.5,0.2,30,0.01)",
            "model(5.5,0.2,30,0.01)",
            "model(1,0.05,30,0.004)",
            "model(1,0.8,30,0.004)",
            "model(0,0.2,3,0.01)",
            "model(4,0,20,0.005)",
            "critical = model(3,0.5,20,0.005)",
            "broken = model(4,0.5,30,0.005)",
            "recovered = model(1,0.5,30,0.005)",
            "model(NaN,0.2,20,0.01)",
            "model(1,Inf,20,0.01)",
            "model(1,0.2,[10 20],0.01)",
            "P07:TimeResolution",
            "P07:ResponseBound",
            "coarse = model(1,0.2,5,0.01)",
            "fine = model(1,0.2,5,0.005)",
            "all(diff(nonIntegerGrid.t) > 0)",
            "shortHorizon.maxInterval-0.02",
            "atResourceLimit.sampleCount == 20001",
            "P07:TooManySamples",
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
            "teach-back",
            "mechanism",
            "actuator lag",
            "gain crossover",
        ):
            self.assertIn(marker, combined)


if __name__ == "__main__":
    unittest.main()
