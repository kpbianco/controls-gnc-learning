from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTION = (
    "What inputs, observable effects, and failure modes matter when you relate "
    "Poles to Visible Motion?"
)


class P03ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P03"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 3)
        self.assertEqual(self.module["title"], "Relate Poles to Visible Motion")
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["prerequisites"], ["P02"])
        self.assertEqual(self.module["implementation_batch"], "P03")
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

    def test_model_is_transparent_deterministic_and_presentation_free(self):
        model = self.read("model.m")
        for formula in (
            "repeatedCoefficient = initialVelocity-poleReal*initialPosition",
            "sineCoefficient = repeatedCoefficient/poleImag",
            "position = exponential.*(initialPosition*cosineTerm",
            "position = exponential.*(initialPosition+repeatedCoefficient*t)",
            "velocity = exponential.*(initialVelocity+",
            "acceleration = 2*poleReal*velocity-naturalFrequency^2*position",
            "energy = 0.5*velocity.^2 + 0.5*naturalFrequency^2*position.^2",
            "[poleReal+1i*poleImag; poleReal-1i*poleImag]",
        ):
            self.assertIn(formula, model)
        for validation in (
            "mustBeReal",
            "mustBeFinite",
            "mustBeNonnegative",
            "mustBePositive",
            "maxSamples = 20001",
            "maxAbsExponent = 300",
            "P03:TooManySamples",
            "P03:ExponentRange",
            "P03:NonfiniteOutput",
        ):
            self.assertIn(validation, model)
        self.assertNotRegex(
            model.lower(),
            r"\b(?:plot|figure|uifigure|uiaxes|uislider|uispinner)\s*\(",
        )

    def test_independent_reference_arithmetic_and_limiting_cases(self):
        sigma, omega, x0, v0 = -0.5, 2.0, 1.0, 0.0
        period = 2 * math.pi / omega
        coefficient = (v0 - sigma * x0) / omega
        initial_envelope = math.hypot(x0, coefficient)
        natural_frequency = math.hypot(sigma, omega)
        self.assertAlmostEqual(period, math.pi)
        self.assertAlmostEqual(coefficient, 0.25)
        self.assertAlmostEqual(initial_envelope, math.sqrt(1.0625))
        self.assertAlmostEqual(natural_frequency, math.sqrt(4.25))
        self.assertAlmostEqual(-sigma / natural_frequency, 1 / math.sqrt(17))
        self.assertAlmostEqual(math.exp(sigma * period), math.exp(-math.pi / 2))

        repeated_final = math.exp(-1) * (1 + 0.5 * 2)
        self.assertAlmostEqual(repeated_final, 2 * math.exp(-1))
        double_zero_position = x0 + 3.0 * 4.0
        self.assertEqual(double_zero_position, 13.0)
        self.assertGreater(math.exp(0.25 * 12), 20)
        self.assertLess(math.exp(-0.25 * 12), 0.05)

    def test_nonzero_initial_velocity_behavioral_regression_is_executable(self):
        checks = self.read("run_checks.m")
        for marker in (
            "phaseCase = model(-0.5,2,1.25,-0.75,pi/4,pi/4000)",
            "expectedPhaseScale = exp(-pi/8)",
            "expectedQuarterPosition = -0.0625*expectedPhaseScale",
            "expectedQuarterVelocity = -2.46875*expectedPhaseScale",
            "phaseCase.position(1)-1.25",
            "phaseCase.velocity(1)+0.75",
            "phaseCase.position(end)-expectedQuarterPosition",
            "phaseCase.velocity(end)-expectedQuarterVelocity",
        ):
            self.assertIn(marker, checks)

    def test_experiment_has_views_metrics_two_sweeps_and_broken_recovery(self):
        experiment = self.read("experiment.m")
        lowered = experiment.lower()
        self.assertGreaterEqual(experiment.count("%%"), 10)
        self.assertIn("sweep 1 - move only the pole real part", lowered)
        self.assertIn("sweep 2 - reset real part and move only imaginary magnitude", lowered)
        self.assertIn("broken case - move the pair into the right half-plane", lowered)
        self.assertIn("violated assumption", lowered)
        self.assertIn("recovered = model(-0.25", lowered)
        self.assertIn(
            "model(realparts(k),poleimag,initialposition,initialvelocity,tend,dt)",
            lowered,
        )
        self.assertIn(
            "model(polereal,imaginaryparts(k),initialposition,initialvelocity,tend,dt)",
            lowered,
        )
        self.assertGreaterEqual(lowered.count("xlabel("), 5)
        self.assertGreaterEqual(lowered.count("ylabel("), 5)
        self.assertGreaterEqual(lowered.count("fprintf("), 2)
        for unit in ("(1/s)", "(rad/s)", "(s)", "(m)", "(j)"):
            self.assertIn(unit, lowered)

    def test_interactive_coordinates_are_meaningful_bounded_and_resettable(self):
        interactive = self.read("interactive.m")
        for marker in (
            "Pole real part sigma (1/s)",
            "Pole imaginary magnitude omega (rad/s)",
            "Limits',[-1.2 -0.05]",
            "Limits',[0.2 4]",
            "Reset baseline",
            "realControl.Value = -0.5",
            "imagControl.Value = 2",
            "model(realControl.Value,imagValue,1,0,12,0.01)",
            "Real part (1/s)",
            "Imaginary part (rad/s)",
        ):
            self.assertIn(marker, interactive)

    def test_checks_cover_invariants_limits_failures_recovery_and_resources(self):
        checks = self.read("run_checks.m")
        self.assertGreaterEqual(checks.count("assert("), 22)
        for marker in (
            "isequaln(baselineA,baselineB)",
            "baselineA.poles.^2",
            "baselineA.position)-baselineA.envelope",
            "all(diff(baselineA.energy) <= tolerance)",
            "fastDecay.oscillationPeriod-slowDecay.oscillationPeriod",
            "fastOscillation.exponentialScaleRatio-",
            "model(0,2,1,0,4*pi,pi/1000)",
            "model(-0.5,0,1,0,2,0.01)",
            "model(0,0,1,3,4,0.01)",
            "model(-0.5,2,0,0,12,0.01)",
            "model(0.25,2,1,0,12,0.01)",
            "model(-0.25,2,1,0,12,0.01)",
            "all(diff(broken.energy) >= -tolerance)",
            "model(NaN,2,1,0,12,0.01)",
            "model(-0.5,Inf,1,0,12,0.01)",
            "model(-0.5,-1,1,0,12,0.01)",
            "model(-0.5,2,1+1i,0,12,0.01)",
            "model(-0.5,2,1,Inf,12,0.01)",
            "model(-0.5,2,1,[0 1],12,0.01)",
            "model([-0.5 -1],2,1,0,12,0.01)",
            "model(-0.5,2,1,0,0.033,0.011)",
            "all(diff(nonIntegerGrid.t) > 0)",
            "shortHorizon.maxInterval-0.5",
            "atResourceLimit.sampleCount == 20001",
            "P03:TooManySamples",
            "P03:ExponentRange",
            "P03:NonfiniteOutput",
            "model(-100,2,1,0,4,0.01)",
        ):
            self.assertIn(marker, checks)

    def test_grid_and_resource_reference_bounds(self):
        samples_at_limit = math.ceil(20.0 / 0.001) + 1
        samples_over_limit = math.ceil(20.001 / 0.001) + 1
        self.assertEqual(samples_at_limit, 20001)
        self.assertGreater(samples_over_limit, 20001)
        self.assertEqual([index * 0.011 for index in range(4)][-1], 0.033)
        self.assertGreater(100 * 4, 300)

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
            r"\b(?:tf|step|lsim|initial|impulse|roots|eig|damp|c2d|ss|pole|expm|ode45|sim)\s*\(",
        )
        model_lowered = self.read("model.m").lower()
        self.assertNotRegex(
            model_lowered,
            r"\b(?:rng|rand|randn|load|save|fopen|readtable|writetable|webread|system|global|persistent)\b",
        )
        for marker in (QUESTION, "P02", "teach-back", "mechanism", "right half-plane"):
            self.assertIn(marker, combined)


if __name__ == "__main__":
    unittest.main()
