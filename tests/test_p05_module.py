from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTION = (
    "What inputs, observable effects, and failure modes matter when you close "
    "a Loop with Proportional Control?"
)


class P05ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P05"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 5)
        self.assertEqual(self.module["title"], "Close a Loop with Proportional Control")
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["prerequisites"], ["P04"])
        self.assertEqual(self.module["implementation_batch"], "P05")
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
            "loopGain = plantGainMPerCommand*proportionalGain",
            "closedLoopPolePerSec = (feedbackSign*loopGain-1)/plantTimeConstantSec",
            "inputRateMPerSec = loopGain*referenceM/plantTimeConstantSec",
            "controllerInputM = referenceM+feedbackSign*outputM",
            "controlCommand = proportionalGain*controllerInputM",
            "(-outputM+plantGainMPerCommand*controlCommand)/plantTimeConstantSec",
            "inputRateMPerSec*expm1(poleStep)/closedLoopPolePerSec",
        ):
            self.assertIn(formula, model)
        for validation in (
            "mustBeReal",
            "mustBeFinite",
            "mustBePositive",
            "mustBeNonnegative",
            "maxSamples = 20001",
            "maxPoleStep = 0.1",
            "maxGrowthExponent = log(1e8)",
            "P05:TimeResolution",
            "P05:ResponseBound",
            "P05:TooManySamples",
            "P05:FeedbackSign",
        ):
            self.assertIn(validation, model)
        self.assertNotRegex(
            model.lower(), r"\b(?:plot|figure|uifigure|uiaxes|uislider|uispinner)\s*\("
        )

    def test_independent_reference_arithmetic_and_limiting_cases(self):
        gain, plant_gain, tau, reference = 2.0, 1.0, 1.0, 1.0
        loop_gain = plant_gain * gain
        pole = -(1 + loop_gain) / tau
        time_constant = -1 / pole
        steady_output = loop_gain * reference / (1 + loop_gain)
        steady_error = reference / (1 + loop_gain)
        one_tau_output = steady_output * (1 - math.exp(-1))

        self.assertEqual(pole, -3.0)
        self.assertAlmostEqual(time_constant, 1 / 3)
        self.assertAlmostEqual(steady_output, 2 / 3)
        self.assertAlmostEqual(steady_error, 1 / 3)
        self.assertAlmostEqual(steady_output, plant_gain * gain * steady_error)
        self.assertAlmostEqual(one_tau_output, 0.4214137058857051)
        self.assertLess(1 / (1 + 8), 1 / (1 + 0.5))
        self.assertGreater(8 * reference, 0.5 * reference)
        self.assertAlmostEqual((3 / (1 + gain)) / (0.25 / (1 + gain)), 12)
        self.assertGreater(2 * (math.exp(4) - 1), 100)

        samples_at_limit = math.floor(20.0 / 0.001) + 1
        samples_over_limit = math.floor(20.001 / 0.001) + 1
        self.assertEqual(samples_at_limit, 20001)
        self.assertGreater(samples_over_limit, 20001)

    def test_nonzero_initial_output_behavioral_regression_is_executable(self):
        checks = self.read("run_checks.m")
        for marker in (
            "initializedAtReference = model(2,1,1,1,1,-1,1,0.01)",
            "expectedInitializedOutput = expectedSteadyOutput +",
            "(1-expectedSteadyOutput)*exp(expectedPole*initializedAtReference.t)",
            "initializedAtReference.initialControlCommand == 0",
            "initializedAtReference.initialOutputRateMPerSec+1",
            "homogeneous response and the forced closed-loop response",
        ):
            self.assertIn(marker, checks)

    def test_experiment_has_views_metrics_two_isolated_sweeps_and_recovery(self):
        experiment = self.read("experiment.m")
        lowered = experiment.lower()
        self.assertGreaterEqual(experiment.count("%%"), 11)
        self.assertIn("sweep 1 - move only proportional gain", lowered)
        self.assertIn(
            "sweep 2 - reset gain and move only plant time constant", lowered
        )
        self.assertIn(
            "broken case - add the measurement instead of subtracting it", lowered
        )
        self.assertIn("the violated assumption is negative feedback", lowered)
        self.assertIn("broken = model(2,1,1,1,0,1,4,0.005)", lowered)
        self.assertIn("recovered = model(2,1,1,1,0,-1,4,0.005)", lowered)
        self.assertIn(
            "model(proportionalgains(k),planttimeconstantsec", lowered
        )
        self.assertIn(
            "model(proportionalgain,planttimeconstantssec(k)", lowered
        )
        self.assertGreaterEqual(lowered.count("xlabel("), 6)
        self.assertGreaterEqual(lowered.count("ylabel("), 6)
        self.assertGreaterEqual(lowered.count("fprintf("), 2)
        for unit in ("(m)", "(s)", "(1/s)", "(command units)", "(command/m)"):
            self.assertIn(unit, lowered)

    def test_interactive_controls_are_meaningful_bounded_and_resettable(self):
        interactive = self.read("interactive.m")
        for marker in (
            "Proportional gain Kp (command/m)",
            "Plant time constant tau (s)",
            "Limits',[0 8]",
            "Limits',[0.25 3]",
            "Reset baseline",
            "gainControl.Value = 2",
            "timeControl.Value = 1",
            "modelFunction = @model",
            "viewDt = min(0.01,0.09*plantTimeConstantSec/(1+proportionalGain))",
            "result = modelFunction(",
            "proportionalGain,plantTimeConstantSec,1,1,0,-1,5,viewDt)",
            "Control command u (command units)",
        ):
            self.assertIn(marker, interactive)

    def test_checks_cover_invariants_limits_failures_recovery_and_resources(self):
        checks = self.read("run_checks.m")
        self.assertGreaterEqual(checks.count("assert("), 25)
        for marker in (
            "isequaln(baselineA,baselineB)",
            "expectedPole = -(1+1*2)/1",
            "expectedSteadyOutput = 2/3",
            "expectedSteadyError = 1/3",
            "expectedSteadyOutput +",
            "expectedSteadyOutput*(1-exp(-1))",
            "model(0.5,1,1,1,0,-1,5,0.005)",
            "model(8,1,1,1,0,-1,5,0.005)",
            "model(2,0.25,1,1,0,-1,5,0.005)",
            "model(2,3,1,1,0,-1,5,0.005)",
            "highGain.maxInterval == lowGain.maxInterval",
            "slowPlant.maxInterval == fastPlant.maxInterval",
            "model(0,1,1,1,0,-1,3,0.01)",
            "model(5,2,1,0,0,-1,3,0.01)",
            "model(0,2,1,0,1,-1,2,0.01)",
            "positiveReference.outputM+negativeReference.outputM",
            "model(1,1,1,1,0,1,2,0.01)",
            "nearMarginal = model(1+1e-10,1,1,1,0,1,2,0.01)",
            "expectedNearMarginalEnd",
            "aboveMarginal = model(1+eps,1,1,1,0,1,1,0.01)",
            "belowMarginal = model(1-eps,1,1,1,0,1,1,0.01)",
            "expectedAboveEnd",
            "expectedBelowEnd",
            "model(2,1,1,1,0,1,4,0.01)",
            "model(2,1,1,1,0,-1,4,0.01)",
            "broken.controlCommand-2*(1+broken.outputM)",
            "brokenPlantResidual",
            "model(NaN,1,1,1,0,-1,5,0.01)",
            "model(2,Inf,1,1,0,-1,5,0.01)",
            "model(2,1,1,[1 2],0,-1,5,0.01)",
            "P05:FeedbackSign",
            "P05:TimeResolution",
            "P05:ResponseBound",
            "all(diff(nonIntegerGrid.t) > 0)",
            "shortHorizon.maxInterval-0.02",
            "atResourceLimit.sampleCount == 20001",
            "P05:TooManySamples",
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
            r"\b(?:tf|step|lsim|initial|impulse|roots|eig|damp|c2d|ss|pole|expm|ode45|ode23|sim)\s*\(",
        )
        model_lowered = self.read("model.m").lower()
        self.assertNotRegex(
            model_lowered,
            r"\b(?:rng|rand|randn|load|save|fopen|readtable|writetable|webread|system|global|persistent|timer)\b",
        )
        for marker in (
            QUESTION,
            "P04",
            "teach-back",
            "mechanism",
            "negative feedback",
        ):
            self.assertIn(marker, combined)


if __name__ == "__main__":
    unittest.main()
