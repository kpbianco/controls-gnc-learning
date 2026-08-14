from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTION = (
    "What inputs, observable effects, and failure modes matter when you compare "
    "Linear and Nonlinear Pendulum Models?"
)


class P04ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P04"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 4)
        self.assertEqual(
            self.module["title"], "Compare Linear and Nonlinear Pendulum Models"
        )
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["prerequisites"], ["P03"])
        self.assertEqual(self.module["implementation_batch"], "P04")
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
            "naturalFrequencyRadPerSec = sqrt(gravityMPerSec2/lengthM)",
            "restoringAngle = sin(angle)",
            "restoringAngle = angle",
            "rateDerivative = -2*zeta*wn*rate-wn^2*restoringAngle",
            "nextAngle = angle + step*(k1Angle+2*k2Angle+2*k3Angle+k4Angle)/6",
            "gravityMPerSec2*lengthM*(1-cos(nonlinearAngleRad))",
            "2*pi/naturalFrequencyRadPerSec",
        ):
            self.assertIn(formula, model)
        for validation in (
            "mustBeReal",
            "mustBeFinite",
            "mustBePositive",
            "mustBeNonnegative",
            "maxSamples = 20001",
            "maxDimensionlessStep = 0.075",
            "P04:TooManySamples",
            "P04:TimeResolution",
            "P04:InitialAngleRange",
            "P04:NonfiniteOutput",
        ):
            self.assertIn(validation, model)
        self.assertNotRegex(
            model.lower(),
            r"\b(?:plot|figure|uifigure|uiaxes|uislider|uispinner)\s*\(",
        )

    def test_independent_reference_arithmetic_and_limiting_cases(self):
        gravity, length = 9.81, 1.0
        natural_frequency = math.sqrt(gravity / length)
        small_angle_period = 2 * math.pi / natural_frequency
        theta_20 = math.radians(20)
        theta_120 = math.radians(120)

        self.assertAlmostEqual(natural_frequency, math.sqrt(9.81))
        self.assertAlmostEqual(small_angle_period, 2.0060666807106475)
        self.assertGreater(math.sin(theta_20) / theta_20, 0.97)
        self.assertLess(math.sin(theta_120) / theta_120, 0.42)
        self.assertGreater(theta_120 / math.sin(theta_120), 2.4)
        self.assertAlmostEqual(
            2 * math.pi * math.sqrt(2.0 / gravity)
            / (2 * math.pi * math.sqrt(0.5 / gravity)),
            2.0,
        )
        self.assertAlmostEqual(math.sin(1e-6) / 1e-6, 1.0, places=11)

        samples_at_limit = math.floor(20.0 / 0.001) + 1
        samples_over_limit = math.floor(20.001 / 0.001) + 1
        self.assertEqual(samples_at_limit, 20001)
        self.assertGreater(samples_over_limit, 20001)

    def test_nonzero_initial_rate_behavioral_regression_is_executable(self):
        checks = self.read("run_checks.m")
        for marker in (
            "velocityDriven = model(0,30,9.81,0,pi/2,pi/4000)",
            "expectedQuarterAngle = pi/6",
            "velocityDriven.linearAngleRad(end)-expectedQuarterAngle",
            "velocityDriven.linearRateRadPerSec(end)",
            "nonzero initial rate must propagate",
        ):
            self.assertIn(marker, checks)

    def test_experiment_has_views_metrics_two_sweeps_and_broken_recovery(self):
        experiment = self.read("experiment.m")
        lowered = experiment.lower()
        self.assertGreaterEqual(experiment.count("%%"), 11)
        self.assertIn("sweep 1 - move only the release angle", lowered)
        self.assertIn(
            "sweep 2 - reset release angle and move only pendulum length", lowered
        )
        self.assertIn(
            "broken case - trust the small-angle model after a 120 degree release",
            lowered,
        )
        self.assertIn("violated assumption is |theta| << 1 rad", lowered)
        self.assertIn("recovered = model(5,0", lowered)
        self.assertIn(
            "model(releaseanglesdeg(k),initialratedegpersec,lengthm", lowered
        )
        self.assertIn(
            "model(initialangledeg,initialratedegpersec,lengthsm(k)", lowered
        )
        self.assertGreaterEqual(lowered.count("xlabel("), 5)
        self.assertGreaterEqual(lowered.count("ylabel("), 5)
        self.assertGreaterEqual(lowered.count("fprintf("), 2)
        for unit in ("(deg)", "(rad/s)", "(rad/s^2)", "(m)", "(s)"):
            self.assertIn(unit, lowered)

    def test_interactive_controls_are_physical_bounded_and_resettable(self):
        interactive = self.read("interactive.m")
        for marker in (
            "Release angle theta_0 (deg)",
            "Pendulum length L (m)",
            "Limits',[1 120]",
            "Limits',[0.3 2.5]",
            "Reset baseline",
            "angleControl.Value = 20",
            "lengthControl.Value = 1",
            "model(angleDeg,0,lengthM,0.02,12,0.01)",
            "Restoring acceleration (rad/s^2)",
        ):
            self.assertIn(marker, interactive)

    def test_checks_cover_invariants_limits_failures_recovery_and_resources(self):
        checks = self.read("run_checks.m")
        self.assertGreaterEqual(checks.count("assert("), 25)
        for marker in (
            "isequaln(baselineA,baselineB)",
            "baselineA.linearPolesPerSec.^2",
            "expectedLinearAcceleration = -9.81*initialAngleRad",
            "expectedNonlinearAcceleration = -9.81*sin(initialAngleRad)",
            "model(5,0,1,0.02,12,0.01)",
            "model(90,0,1,0.02,12,0.01)",
            "model(20,0,0.5,0.02,12,0.01)",
            "model(20,0,2,0.02,12,0.01)",
            "model(0.01,0,1,0,4,0.002)",
            "model(1e-14,0,1,0,1,0.001)",
            "model(0,0,1,0.02,4,0.01)",
            "model(30,15,1,0.02,4,0.01)",
            "model(-30,-15,1,0.02,4,0.01)",
            "rateCase = model(0,30,1,0.1,1,0.005)",
            "expectedDampingAcceleration = -2*0.1*sqrt(9.81)*expectedInitialRate",
            "rateCase.linearRateRadPerSec(1)-expectedInitialRate",
            "rateCase.initialNonlinearAccelerationRadPerSec2-",
            "velocityDriven = model(0,30,9.81,0,pi/2,pi/4000)",
            "velocityDriven.linearAngleRad(end)-expectedQuarterAngle",
            "velocityDriven.linearRateRadPerSec(end)",
            "rateDriven = model(0,720,1,0.02,1,0.005)",
            "max(abs(rateDriven.restoringAngleRad)) >= simulatedAngleLimit",
            "model(60,0,1,0,8,0.002)",
            "boundaryLengthM = 9.81*(0.01/0.074)^2",
            "acceptedResolution.linearFirstZeroSec-expectedQuarterPeriod",
            "acceptedResolution.linearSpecificEnergyJPerKg-",
            "model(120,0,1,0.02,12,0.01)",
            "model(NaN,0,1,0.02,12,0.01)",
            "model(20,Inf,1,0.02,12,0.01)",
            "model([10 20],0,1,0.02,12,0.01)",
            "P04:InitialAngleRange",
            "P04:TimeResolution",
            "all(diff(nonIntegerGrid.t) > 0)",
            "shortHorizon.maxInterval-0.02",
            "atResourceLimit.sampleCount == 20001",
            "P04:TooManySamples",
        ):
            self.assertIn(marker, checks)

    def test_model_is_isolated_and_uses_no_opaque_toolbox_path(self):
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
            r"\b(?:tf|step|lsim|initial|impulse|roots|eig|damp|c2d|ss|pole|expm|ode45|ode23|sim)\s*\(",
        )
        model_lowered = self.read("model.m").lower()
        self.assertNotRegex(
            model_lowered,
            r"\b(?:rng|rand|randn|load|save|fopen|readtable|writetable|webread|system|global|persistent|timer)\b",
        )
        for marker in (QUESTION, "P03", "teach-back", "mechanism", "small-angle"):
            self.assertIn(marker, combined)


if __name__ == "__main__":
    unittest.main()
