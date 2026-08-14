from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTION = (
    "What inputs, observable effects, and failure modes matter when you build "
    "Intuition for Integrators and First-Order Systems?"
)


class P02ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P02"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 2)
        self.assertEqual(
            self.module["title"],
            "Build Intuition for Integrators and First-Order Systems",
        )
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["prerequisites"], ["P01"])
        self.assertEqual(self.module["implementation_batch"], "P02")
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

    def test_model_is_deterministic_transparent_and_resource_bounded(self):
        model = self.read("model.m")
        for formula in (
            "integrator = stepAmplitude*t",
            "firstOrderSteady = gain*stepAmplitude",
            "1-exp(-t/tau)",
            "interval*(gain*u(k)-eulerFirstOrder(k))/tau",
        ):
            self.assertIn(formula, model)
        for validation in (
            "mustBeReal",
            "mustBeFinite",
            "mustBePositive",
            "maxSamples = 20001",
            "P02:TooManySamples",
        ):
            self.assertIn(validation, model)
        self.assertNotRegex(
            model.lower(),
            r"\b(?:plot|figure|uifigure|uiaxes|uislider|uispinner)\s*\(",
        )

    def test_time_grid_behavioral_regression_is_executable(self):
        checks = self.read("run_checks.m")
        for marker in (
            "model(1,1,1,0.033,0.011)",
            "nonIntegerGrid.sampleCount == 4",
            "all(diff(nonIntegerGrid.t) > 0)",
            "nonIntegerGrid.t(end) == 0.033",
            "shortHorizon.sampleCount == 2",
            "shortHorizon.maxInterval-0.5",
            "shortHorizon.eulerRatio-0.5",
        ):
            self.assertIn(marker, checks)

    def test_independent_numerical_limits_match_governing_equations(self):
        amplitude, tau, gain, horizon = 1.5, 2.0, 0.8, 10.0
        integrator_final = amplitude * horizon
        equilibrium = gain * amplitude
        at_one_tau = equilibrium * (1 - math.exp(-1))
        self.assertAlmostEqual(integrator_final, 15.0)
        self.assertAlmostEqual(equilibrium, 1.2)
        self.assertAlmostEqual(at_one_tau / equilibrium, 1 - math.exp(-1))
        self.assertEqual(0.0 * horizon, 0.0)

        ratio = 3.0
        error_multiplier = 1.0 - ratio
        self.assertEqual(error_multiplier, -2.0)
        self.assertGreater(abs(error_multiplier), 1.0)
        samples_at_limit = math.ceil(20.0 / 0.001) + 1
        samples_over_limit = math.ceil(20.001 / 0.001) + 1
        self.assertEqual(samples_at_limit, 20001)
        self.assertGreater(samples_over_limit, 20001)

    def test_experiment_has_metrics_two_sweeps_and_named_broken_case(self):
        experiment = self.read("experiment.m")
        lowered = experiment.lower()
        self.assertGreaterEqual(experiment.count("%%"), 8)
        self.assertIn("sweep 1 - move only input amplitude", lowered)
        self.assertIn("sweep 2 - reset amplitude and move only time constant", lowered)
        self.assertIn("broken case", lowered)
        self.assertIn("dt/tau = 3", lowered)
        self.assertIn("calculation interval resolves the dynamics", lowered)
        self.assertGreaterEqual(lowered.count("xlabel("), 4)
        self.assertGreaterEqual(lowered.count("ylabel("), 4)
        self.assertGreaterEqual(lowered.count("fprintf("), 2)

    def test_interactive_controls_are_meaningful_and_bounded(self):
        interactive = self.read("interactive.m")
        self.assertIn("Input amplitude A (normalized)", interactive)
        self.assertIn("Time constant tau (s)", interactive)
        self.assertIn("Limits',[-2 2]", interactive)
        self.assertIn("Limits',[0.2 5]", interactive)
        self.assertIn("Reset baseline", interactive)
        self.assertIn("model(amplitudeControl.Value,tauValue,1,10,0.02)", interactive)

    def test_checks_cover_limits_malformed_inputs_and_broken_regression(self):
        checks = self.read("run_checks.m")
        self.assertGreaterEqual(checks.count("assert("), 15)
        for marker in (
            "1-exp(-1)",
            "model(0,2,3,10,0.02)",
            "model(NaN,2,1,10,0.02)",
            "model(1,2,Inf,10,0.02)",
            "model(1+1i,2,1,10,0.02)",
            "model([1 2],2,1,10,0.02)",
            "model(1,2,1,-10,0.02)",
            "model(1,2,1,10,0)",
            "model(1,1,1,0.033,0.011)",
            "all(diff(nonIntegerGrid.t) > 0)",
            "shortHorizon.maxInterval-0.5",
            "atResourceLimit.sampleCount == 20001",
            "P02:TooManySamples",
            "broken.eulerRatio > 2",
            "broken.maxAbsEuler > 10",
        ):
            self.assertIn(marker, checks)

    def test_content_is_concept_first_and_has_no_opaque_toolbox_path(self):
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
            r"\b(?:tf|step|lsim|c2d|ode45|sim)\s*\(",
        )
        for marker in (QUESTION, "P01", "teach-back", "mechanism"):
            self.assertIn(marker, combined)


if __name__ == "__main__":
    unittest.main()
