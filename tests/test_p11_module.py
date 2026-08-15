from __future__ import annotations

import json
import math
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTION = (
    "What inputs, observable effects, and failure modes matter when you drive "
    "an Actuator into Saturation?"
)


def simulate(
    reference: float,
    control_limit: float,
    horizon: float,
    time_step: float,
) -> tuple[list[float], list[float], list[float], list[float], list[bool]]:
    interval_count = math.floor(horizon / time_step)
    times = [index * time_step for index in range(interval_count + 1)]
    tolerance = 32 * math.ulp(max(1.0, horizon, time_step))
    if interval_count == 0 or horizon - times[-1] > tolerance:
        times.append(horizon)
    else:
        times[-1] = horizon

    output = [0.0] * len(times)
    unlimited = [0.0] * len(times)
    requested = [0.0] * len(times)
    applied = [0.0] * len(times)
    clipped = [False] * len(times)
    for index, time in enumerate(times):
        requested[index] = 4 * (reference - output[index])
        applied[index] = max(-control_limit, min(control_limit, requested[index]))
        clipped[index] = requested[index] != applied[index]
        if index + 1 < len(times):
            interval = times[index + 1] - time
            decay = math.exp(-interval)
            output[index + 1] = decay * output[index] + (1 - decay) * applied[index]
            unlimited_request = 4 * (reference - unlimited[index])
            unlimited[index + 1] = (
                decay * unlimited[index] + (1 - decay) * unlimited_request
            )
    return times, output, unlimited, applied, clipped


def saturation_fraction(
    times: list[float], clipped: list[bool], horizon: float
) -> float:
    duration = sum(
        (right - left) * is_clipped
        for left, right, is_clipped in zip(times, times[1:], clipped)
    )
    return duration / horizon


class P11ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P11"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 11)
        self.assertEqual(self.module["title"], "Drive an Actuator into Saturation")
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["phase"], 3)
        self.assertEqual(self.module["phase_title"], "Digital and constrained control")
        self.assertEqual(self.module["prerequisites"], ["P10"])
        self.assertEqual(self.module["implementation_batch"], "P11")
        self.assertEqual(self.module["status"], "implemented")
        self.assertEqual(self.module["evidence_level"], "simulated")

    def test_public_check_route_resolves_p11_executable_checks(self):
        completed = subprocess.run(
            [str(ROOT / "bin/learn"), "check", "P11"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout,
            "Run in MATLAB: run_module_checks('P11')\n",
        )
        self.assertEqual(completed.stderr, "")

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
            "requestedControl(k) = proportionalGain*(reference-plantOutput(k))",
            "appliedControl(k) = max(-controlLimit,",
            "min(controlLimit,requestedControl(k))",
            "plantDecay = exp(-intervalDurationSec(k)/plantTimeConstantSec)",
            "inputWeight = 1-plantDecay",
            "plantOutput(k+1) = plantDecay*plantOutput(k)+",
            "clippingGap = requestedControl-appliedControl",
            "saturationDurationSec = sum(intervalDurationSec.*",
            "loopGain = plantStaticGainOutputPerActuator*proportionalGain",
            "linearEquilibriumOutput = loopGain/(1+loopGain)*reference",
        ):
            self.assertIn(formula, model)
        for validation in (
            "mustBeReal",
            "mustBeFinite",
            "mustBePositive",
            "maxSampleCount = 30001",
            "responseLimit = 100",
            "P11:ReferenceRange",
            "P11:ControlLimitRange",
            "P11:HorizonRange",
            "P11:DisplayResolution",
            "P11:TooManySamples",
            "P11:ResponseBound",
        ):
            self.assertIn(validation, model)
        self.assertLess(
            model.index("projectedSampleCount > maxSampleCount"),
            model.index("t = (0:regularIntervalCount)'*timeStepSec"),
        )
        self.assertNotRegex(
            model.lower(), r"\b(?:plot|figure|uifigure|uiaxes|uislider|uidropdown)\s*\("
        )

    def test_independent_baseline_clamp_and_exact_transition(self):
        times, output, unlimited, applied, clipped = simulate(1, 2, 5, 0.01)
        self.assertEqual(times[0], 0)
        self.assertEqual(times[-1], 5)
        self.assertEqual(applied[0], 2)
        self.assertTrue(clipped[0])
        self.assertAlmostEqual(output[1], 2 * (1 - math.exp(-0.01)))
        self.assertAlmostEqual(output[2], 2 * (1 - math.exp(-0.02)))
        self.assertAlmostEqual(unlimited[1], 4 * (1 - math.exp(-0.01)))
        self.assertAlmostEqual(output[-1], 0.8, places=9)
        self.assertAlmostEqual(unlimited[-1], 0.8, places=9)
        self.assertAlmostEqual(saturation_fraction(times, clipped, 5), 0.058)
        release_indices = [
            index
            for index in range(1, len(clipped))
            if clipped[index - 1] and not clipped[index]
        ]
        self.assertEqual(release_indices, [29])
        self.assertAlmostEqual(times[release_indices[0]], 0.29)

    def test_independent_limiting_symmetry_and_partial_interval_cases(self):
        times, output, unlimited, applied, clipped = simulate(0, 2, 2, 0.01)
        self.assertTrue(all(value == 0 for value in output + unlimited + applied))
        self.assertFalse(any(clipped))

        _, output, unlimited, _, clipped = simulate(1, 10, 2, 0.01)
        self.assertFalse(any(clipped))
        self.assertEqual(output, unlimited)

        _, positive, _, positive_applied, positive_clipped = simulate(1, 1.2, 3, 0.01)
        _, negative, _, negative_applied, negative_clipped = simulate(-1, 1.2, 3, 0.01)
        for positive_value, negative_value in zip(positive, negative):
            self.assertAlmostEqual(positive_value, -negative_value)
        for positive_value, negative_value in zip(positive_applied, negative_applied):
            self.assertAlmostEqual(positive_value, -negative_value)
        self.assertEqual(positive_clipped, negative_clipped)

        times, output, _, applied, clipped = simulate(1, 2, 0.097, 0.03)
        self.assertEqual(times, [0, 0.03, 0.06, 0.09, 0.097])
        final_interval = times[-1] - times[-2]
        expected = math.exp(-final_interval) * output[-2] + (
            1 - math.exp(-final_interval)
        ) * applied[-2]
        self.assertAlmostEqual(output[-1], expected)
        self.assertTrue(clipped[0])

        tiny_times, _, _, _, _ = simulate(1, 2, 1e-16, 0.01)
        self.assertEqual(tiny_times, [0, 1e-16])

        release_times, _, _, _, release_clipped = simulate(1, 2, 0.29, 0.01)
        self.assertTrue(all(release_clipped[:-1]))
        self.assertFalse(release_clipped[-1])
        self.assertLess(0.8, 2)
        self.assertEqual(release_times[-1], 0.29)

        _, _, _, _, eventual_clipped = simulate(1, 0.801, 5, 0.01)
        self.assertTrue(all(eventual_clipped))
        self.assertLess(0.8, 0.801)

    def test_independent_sweeps_broken_case_and_recovery(self):
        reference_fractions = []
        for reference in (0.25, 0.5, 1, 1.5, 2):
            times, _, _, _, clipped = simulate(reference, 2, 5, 0.01)
            reference_fractions.append(saturation_fraction(times, clipped, 5))
        self.assertEqual(reference_fractions, sorted(reference_fractions))
        self.assertEqual(reference_fractions[:2], [0, 0])
        self.assertGreater(reference_fractions[-1], 0.25)

        limit_fractions = []
        for control_limit in (0.4, 0.6, 0.8, 1.2, 2):
            times, _, _, _, clipped = simulate(1, control_limit, 5, 0.01)
            limit_fractions.append(saturation_fraction(times, clipped, 5))
        self.assertEqual(limit_fractions, sorted(limit_fractions, reverse=True))
        self.assertEqual(limit_fractions[:3], [1, 1, 1])
        self.assertLess(limit_fractions[-1], 0.1)

        times, broken, broken_unlimited, broken_applied, broken_clipped = simulate(
            1.5, 0.6, 5, 0.01
        )
        _, recovered, recovered_unlimited, _, recovered_clipped = simulate(
            1.5, 2, 5, 0.01
        )
        self.assertTrue(all(broken_clipped[:-1]))
        self.assertTrue(all(value == 0.6 for value in broken_applied))
        expected_broken = [0.6 * (1 - math.exp(-time)) for time in times]
        for actual, expected in zip(broken, expected_broken):
            self.assertAlmostEqual(actual, expected)
        self.assertGreater(1.5 - broken[-1], 0.9)
        self.assertFalse(all(recovered_clipped[:-1]))
        self.assertLess(1.5 - recovered[-1], 0.31)
        self.assertLess(
            max(abs(a - b) for a, b in zip(recovered, recovered_unlimited)),
            max(abs(a - b) for a, b in zip(broken, broken_unlimited)),
        )

    def test_experiment_has_views_metrics_two_isolated_sweeps_and_recovery(self):
        experiment = self.read("experiment.m")
        lowered = experiment.lower()
        self.assertGreaterEqual(experiment.count("%%"), 13)
        self.assertIn("sweep 1 - move only reference amplitude", lowered)
        self.assertIn("sweep 2 - reset reference and move only actuator limit", lowered)
        self.assertIn(
            "broken case - demand more output than maximum actuation can support", lowered
        )
        self.assertIn("references = [0.25 0.5 1 1.5 2]", lowered)
        self.assertIn("controllimits = [0.4 0.6 0.8 1.2 2]", lowered)
        self.assertIn("broken = model(1.5,0.6,5,0.01)", lowered)
        self.assertIn("recovered = model(1.5,2,5,0.01)", lowered)
        self.assertIn("stairs(baseline.t,baseline.clippinggap", lowered)
        self.assertGreaterEqual(lowered.count("xlabel("), 10)
        self.assertGreaterEqual(lowered.count("ylabel("), 10)
        self.assertGreaterEqual(lowered.count("fprintf("), 2)
        for unit in ("(s)", "(%)", "(output)", "(actuator)", "(output*s)"):
            self.assertIn(unit, lowered)

    def test_interactive_controls_are_bounded_immediate_and_resettable(self):
        interactive = self.read("interactive.m")
        for marker in (
            "Reference r (output)",
            "Actuator limit uLimit (actuator)",
            "Limits',[-2 2]",
            "Limits',[0.25 3]",
            "Reset baseline",
            "referenceControl.Value = 1",
            "limitControl.Value = 2",
            "ValueChangingFcn",
            "ValueChangedFcn",
            "modelFunction = @model",
            "result.requestedControl",
            "result.appliedControl",
            "persistent saturation",
            "still clipped at 5 s; eventual release",
            "stairs(axControl,result.t,result.requestedControl",
            "stairs(axControl,result.t,result.appliedControl",
            "Time (s)",
        ):
            self.assertIn(marker, interactive)

    def test_checks_cover_limits_malformed_inputs_recovery_and_resources(self):
        checks = self.read("run_checks.m")
        self.assertGreaterEqual(checks.count("assert("), 30)
        for marker in (
            "isequaln(baselineA,baselineB)",
            "expectedApplied = max(-baselineA.controlLimit",
            "plantResidual",
            "unlimitedResidual",
            "model(0,2,2,0.01)",
            "model(-1,1.2,3,0.01)",
            "model(1,0.4,3,0.01)",
            "model(1.5,0.6,5,0.01)",
            "model(1.5,2,5,0.01)",
            "model(NaN,2,5,0.01)",
            "model(1,Inf,5,0.01)",
            "model([1 2],2,5,0.01)",
            "P11:ReferenceRange",
            "P11:ControlLimitRange",
            "P11:HorizonRange",
            "P11:DisplayResolution",
            "P11:TooManySamples",
            "model(1,2,30,1e-12)",
            "atSampleLimit.sampleCount == 30001",
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
            "P05",
            "P10",
            "P12",
            "teach-back",
            "mechanism",
            "requested",
            "applied",
            "clipping",
            "actuator limit",
            "authority",
            "no integral state",
        ):
            self.assertIn(marker, combined)


if __name__ == "__main__":
    unittest.main()
