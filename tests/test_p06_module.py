from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTION = (
    "What inputs, observable effects, and failure modes matter when you tune "
    "a PID by Observing Each Term?"
)


def reference_pid(
    integral_gain: float,
    derivative_gain: float,
    derivative_sign: float = -1.0,
    duration: float = 20.0,
    interval: float = 0.01,
) -> tuple[list[float], list[float], list[float]]:
    """Independent RK4 reference for the documented fixed P06 carriage."""
    state = [0.0, 0.0, 0.0]
    positions: list[float] = []
    derivative_forces: list[float] = []
    total_forces: list[float] = []

    def rate(current: list[float]) -> list[float]:
        position, velocity, integral_error = current
        error = 1.0 - position
        proportional = 4.0 * error
        integral = integral_gain * integral_error
        derivative = derivative_sign * derivative_gain * velocity
        total = proportional + integral + derivative
        acceleration = total - 1.0 - 0.5 * velocity
        return [velocity, acceleration, error]

    steps = round(duration / interval)
    for index in range(steps + 1):
        position, velocity, integral_error = state
        error = 1.0 - position
        proportional = 4.0 * error
        integral = integral_gain * integral_error
        derivative = derivative_sign * derivative_gain * velocity
        positions.append(position)
        derivative_forces.append(derivative)
        total_forces.append(proportional + integral + derivative)
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
    return positions, derivative_forces, total_forces


class P06ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P06"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 6)
        self.assertEqual(self.module["title"], "Tune a PID by Observing Each Term")
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["prerequisites"], ["P05"])
        self.assertEqual(self.module["implementation_batch"], "P06")
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
            "trackingErrorM = referenceM-positionM",
            "proportionalControlN = proportionalGain*trackingErrorM",
            "integralControlN = integralGain*integralErrorMSeconds",
            "derivativeControlN = derivativeSign*derivativeGain*velocityMPerSec",
            "totalControlN = proportionalControlN+integralControlN+derivativeControlN",
            "accelerationMPerSec2 = (totalControlN+loadForceN-",
            "rate = [velocityMPerSec;accelerationMPerSec2;trackingErrorM]",
            "state = state + step*(k1+2*k2+2*k3+k4)/6",
        ):
            self.assertIn(formula, model)
        for validation in (
            "mustBeReal",
            "mustBeFinite",
            "mustBePositive",
            "mustBeNonnegative",
            "maxSamples = 20001",
            "maxDimensionlessStep = 0.15",
            "responseLimit = 1e6",
            "P06:TimeResolution",
            "P06:ResponseBound",
            "P06:TooManySamples",
            "P06:DerivativeSign",
        ):
            self.assertIn(validation, model)
        self.assertNotRegex(
            model.lower(), r"\b(?:plot|figure|uifigure|uiaxes|uislider|uispinner)\s*\("
        )

    def test_independent_reference_arithmetic_sweeps_failure_and_limits(self):
        baseline, baseline_d, baseline_u = reference_pid(1.0, 3.0)
        no_integral, _, _ = reference_pid(0.0, 3.0)
        high_integral, _, _ = reference_pid(2.0, 3.0)
        no_derivative, no_derivative_d, _ = reference_pid(1.0, 0.0)
        broken, broken_d, _ = reference_pid(0.5, 3.0, 1.0, 4.0)
        recovered, recovered_d, _ = reference_pid(0.5, 3.0, -1.0, 4.0)

        self.assertAlmostEqual(baseline[-1], 1.0000443007, places=8)
        self.assertAlmostEqual(max(baseline) - 1.0, 0.0100110452, places=8)
        self.assertEqual(baseline_u[0], 4.0)
        self.assertEqual(baseline_d[0], 0.0)
        self.assertAlmostEqual(no_integral[-1], 0.75, places=9)
        self.assertAlmostEqual(1.0 - no_integral[-1], -(-1.0) / 4.0, places=9)
        self.assertGreater(max(high_integral) - 1.0, 0.15)
        self.assertGreater(max(no_derivative) - 1.0, 0.4)
        self.assertTrue(all(force == 0.0 for force in no_derivative_d))
        self.assertGreater(max(abs(value) for value in broken), 100.0)
        self.assertLess(max(abs(value) for value in recovered), 1.0)
        self.assertGreater(max(abs(value) for value in broken_d), 100.0)
        self.assertLess(min(recovered_d), 0.0)

        samples_at_limit = math.floor(20.0 / 0.001) + 1
        samples_over_limit = math.floor(20.001 / 0.001) + 1
        self.assertEqual(samples_at_limit, 20001)
        self.assertGreater(samples_over_limit, 20001)

    def test_coupled_pid_state_behavioral_regression_is_executable(self):
        checks = self.read("run_checks.m")
        for marker in (
            "factoredPoleCase = model(11,6,5.5,0,-1,1,0.002)",
            "s^3+6*s^2+11*s+6=(s+1)*(s+2)*(s+3)",
            "expectedFactoredPosition = 1+2.5*exp(-factoredPoleCase.t)-",
            "expectedFactoredVelocity = -2.5*exp(-factoredPoleCase.t)+",
            "expectedFactoredIntegral = 2.5*exp(-factoredPoleCase.t)-",
            "factoredPoleCase.positionM-expectedFactoredPosition",
            "factoredPoleCase.velocityMPerSec-expectedFactoredVelocity",
            "factoredPoleCase.integralErrorMSeconds-",
            "independently factored",
        ):
            self.assertIn(marker, checks)

    def test_experiment_has_views_metrics_two_isolated_sweeps_and_recovery(self):
        experiment = self.read("experiment.m")
        lowered = experiment.lower()
        self.assertGreaterEqual(experiment.count("%%"), 11)
        self.assertIn("sweep 1 - move only integral gain", lowered)
        self.assertIn(
            "sweep 2 - reset integral gain and move only derivative gain", lowered
        )
        self.assertIn("broken case - reinforce velocity instead of opposing it", lowered)
        self.assertIn("the violated assumption is derivative polarity", lowered)
        self.assertIn("broken = model(4,0.5,3,-1,1,4,0.01)", lowered)
        self.assertIn("recovered = model(4,0.5,3,-1,-1,4,0.01)", lowered)
        self.assertIn(
            "model(proportionalgain,integralgains(k),derivativegain", lowered
        )
        self.assertIn(
            "model(proportionalgain,integralgain,derivativegains(k)", lowered
        )
        self.assertGreaterEqual(lowered.count("xlabel("), 6)
        self.assertGreaterEqual(lowered.count("ylabel("), 6)
        self.assertGreaterEqual(lowered.count("fprintf("), 2)
        for unit in ("(m)", "(s)", "(n)", "(n/m)", "(n/(m*s))", "(n*s/m)"):
            self.assertIn(unit, lowered)

    def test_interactive_controls_are_meaningful_bounded_and_resettable(self):
        interactive = self.read("interactive.m")
        for marker in (
            "Kp proportional (N/m)",
            "Ki integral (N/(m*s))",
            "Kd derivative (N*s/m)",
            "Limits',[4 8]",
            "Limits',[0 2]",
            "Limits',[0 5]",
            "Reset baseline",
            "proportionalControl.Value = 4",
            "integralControl.Value = 1",
            "derivativeControl.Value = 3",
            "modelFunction = @model",
            "result = modelFunction(",
            "proportionalGain,integralGain,derivativeGain,-1,-1,20,0.01)",
            "Controller force (N)",
        ):
            self.assertIn(marker, interactive)

    def test_checks_cover_invariants_limits_failures_recovery_and_resources(self):
        checks = self.read("run_checks.m")
        self.assertGreaterEqual(checks.count("assert("), 25)
        for marker in (
            "isequaln(baselineA,baselineB)",
            "controllerResidual",
            "plantResidual",
            "errorDerivativeMPerSec+",
            "integralControlN(end)+baselineA.loadForceN",
            "model(4,0,3,-1,-1,20,0.01)",
            "model(4,2,3,-1,-1,20,0.01)",
            "model(4,1,0,-1,-1,20,0.01)",
            "model(4,1,1.5,-1,-1,20,0.01)",
            "model(0,0,0,0,-1,3,0.01)",
            "model(4,0.5,3,-1,1,4,0.01)",
            "model(4,0.5,3,-1,-1,20,0.01)",
            "broken.derivativeControlN-",
            "model(NaN,1,3,-1,-1,20,0.01)",
            "model(4,Inf,3,-1,-1,20,0.01)",
            "model(4,1,3,[0 -1],-1,20,0.01)",
            "P06:DerivativeSign",
            "P06:TimeResolution",
            "P06:ResponseBound",
            "noDerivativeWrongSign",
            "noIntegral.positionLoopStable",
            "~noIntegral.internalStateAsymptoticallyStable",
            "coarse = model(4,1,3,-1,-1,5,0.02)",
            "fine = model(4,1,3,-1,-1,5,0.01)",
            "all(diff(nonIntegerGrid.t) > 0)",
            "shortHorizon.maxInterval-0.02",
            "atResourceLimit.sampleCount == 20001",
            "P06:TooManySamples",
        ):
            self.assertIn(marker, checks)

    def test_content_is_concept_first_isolated_and_has_no_opaque_path(self):
        combined = "\n".join(
            self.read(name)
            for name in (
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
        )
        lowered = combined.lower()
        self.assertNotIn("scaffolded", lowered)
        self.assertNotRegex(lowered, r"\b(?:todo|placeholder)\b")
        self.assertNotRegex(
            lowered,
            r"\b(?:tf|pid|feedback|step|lsim|initial|impulse|roots|eig|damp|c2d|ss|pole|expm|ode45|ode23|sim)\s*\(",
        )
        model_lowered = self.read("model.m").lower()
        self.assertNotRegex(
            model_lowered,
            r"\b(?:rng|rand|randn|load|save|fopen|readtable|writetable|webread|system|timer|pause|parfeval)\s*\(|\b(?:global|persistent)\b",
        )
        for marker in (
            QUESTION,
            "P05",
            "teach-back",
            "mechanism",
            "derivative-on-measurement",
        ):
            self.assertIn(marker, combined)


if __name__ == "__main__":
    unittest.main()
