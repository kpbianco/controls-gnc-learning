from __future__ import annotations

import json
import math
import subprocess
import unittest
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTION = (
    "What inputs, observable effects, and failure modes matter when you recover "
    "from Integrator Windup?"
)


@dataclass
class PathResult:
    output: list[float]
    integral: list[float]
    requested: list[float]
    applied: list[float]
    correction: list[float]


def make_grid(duration: float, horizon: float, time_step: float) -> list[float]:
    interval_count = math.floor(horizon / time_step)
    times = [index * time_step for index in range(interval_count + 1)]
    tolerance = 32 * math.ulp(max(1.0, duration, horizon, time_step))
    event_index = round(duration / time_step)
    event_on_grid = (
        event_index <= interval_count
        and abs(event_index * time_step - duration) <= tolerance
    )
    if event_on_grid:
        times[event_index] = duration
    else:
        times.append(duration)
    if interval_count == 0 or horizon - interval_count * time_step > tolerance:
        times.append(horizon)
    else:
        times[-1] = horizon
    return sorted(times)


def simulate(
    gain: float,
    duration: float,
    horizon: float,
    time_step: float,
    polarity: float = 1,
) -> tuple[list[float], list[float], PathResult, PathResult]:
    times = make_grid(duration, horizon, time_step)
    reference = [2.0 if time < duration else -0.5 for time in times]

    def one_path(protected: bool) -> PathResult:
        output = [0.0] * len(times)
        integral = [0.0] * len(times)
        requested = [0.0] * len(times)
        applied = [0.0] * len(times)
        correction = [0.0] * len(times)
        for index, time in enumerate(times):
            error = reference[index] - output[index]
            requested[index] = 2 * error + integral[index]
            applied[index] = max(-1, min(1, requested[index]))
            if protected:
                correction[index] = polarity * gain * (
                    applied[index] - requested[index]
                )
            if index + 1 < len(times):
                interval = times[index + 1] - time
                decay = math.exp(-interval)
                output[index + 1] = (
                    decay * output[index] + (1 - decay) * applied[index]
                )
                integral[index + 1] = integral[index] + interval * (
                    error + correction[index]
                )
        return PathResult(output, integral, requested, applied, correction)

    return times, reference, one_path(False), one_path(True)


def release_metrics(
    times: list[float], duration: float, result: PathResult
) -> tuple[float, float, float]:
    release_index = times.index(duration)
    reversal = next(
        (
            time - duration
            for time, applied in zip(
                times[release_index:], result.applied[release_index:]
            )
            if applied < 0
        ),
        math.nan,
    )
    error_area = sum(
        (right - left)
        * (abs(-0.5 - y_left) + abs(-0.5 - y_right))
        / 2
        for left, right, y_left, y_right in zip(
            times[release_index:],
            times[release_index + 1 :],
            result.output[release_index:],
            result.output[release_index + 1 :],
        )
    )
    return result.integral[release_index], reversal, error_area


class P12ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P12"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 12)
        self.assertEqual(self.module["title"], "Recover from Integrator Windup")
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["phase"], 3)
        self.assertEqual(self.module["phase_title"], "Digital and constrained control")
        self.assertEqual(self.module["prerequisites"], ["P11"])
        self.assertEqual(self.module["implementation_batch"], "P12")
        self.assertEqual(self.module["status"], "implemented")
        self.assertEqual(self.module["evidence_level"], "simulated")

    def test_public_check_route_resolves_p12_executable_checks(self):
        completed = subprocess.run(
            [str(ROOT / "bin/learn"), "check", "P12"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout,
            "Run in MATLAB: run_module_checks('P12')\n",
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
            "trackingError(k) = reference(k)-plantOutput(k)",
            "requestedControl(k) = proportionalTerm(k)+integralState(k)",
            "appliedControl(k) = max(-controlLimit,",
            "min(controlLimit,requestedControl(k))",
            "correctionTerm(k) = backCalculationSign*antiWindupGain*(",
            "appliedControl(k)-requestedControl(k)",
            "plantDecay = exp(-intervalDurationSec(k)/",
            "plantOutput(k+1) = plantDecay*plantOutput(k)+",
            "integratorDerivative = integralGainPerSec*",
            "integralState(k+1) = integralState(k)+",
        ):
            self.assertIn(formula, model)
        for validation in (
            "maxSampleCount = 30001",
            "responseLimit = 500",
            "maxTimeStepSec = 0.02",
            "P12:AntiWindupGainRange",
            "P12:DemandDurationRange",
            "P12:HorizonRange",
            "P12:DisplayResolution",
            "P12:BackCalculationSign",
            "P12:TooManySamples",
            "P12:ResponseBound",
        ):
            self.assertIn(validation, model)
        self.assertLess(
            model.index("projectedSampleCount > maxSampleCount"),
            model.index("t = (0:regularIntervalCount)'*timeStepSec"),
        )
        self.assertNotRegex(
            model.lower(), r"\b(?:plot|figure|uifigure|uiaxes|uislider|uidropdown)\s*\("
        )

    def test_independent_baseline_recurrences_and_recovery(self):
        times, reference, unprotected, protected = simulate(1, 3, 12, 0.01)
        self.assertEqual(times[0], 0)
        self.assertEqual(times[-1], 12)
        self.assertEqual(reference[times.index(3)], -0.5)
        self.assertEqual(unprotected.applied[0], 1)
        self.assertEqual(protected.applied[0], 1)
        self.assertAlmostEqual(unprotected.output[1], 1 - math.exp(-0.01))
        release_index = times.index(3)
        self.assertEqual(
            unprotected.output[: release_index + 1],
            protected.output[: release_index + 1],
        )
        self.assertEqual(
            unprotected.applied[:release_index], protected.applied[:release_index]
        )
        unprotected_integral, unprotected_reversal, unprotected_error = (
            release_metrics(times, 3, unprotected)
        )
        protected_integral, protected_reversal, protected_error = release_metrics(
            times, 3, protected
        )
        self.assertAlmostEqual(unprotected_integral, 3.9549719147182)
        self.assertAlmostEqual(protected_integral, -0.149732723111356)
        self.assertAlmostEqual(unprotected_reversal, 2.02)
        self.assertEqual(protected_reversal, 0)
        self.assertLess(protected_error, 0.25 * unprotected_error)
        self.assertTrue(all(abs(value) <= 1 for value in protected.applied))

    def test_event_alignment_limiting_case_and_actual_interval_updates(self):
        times, _, unprotected, protected = simulate(1, 2.005, 8.017, 0.019)
        self.assertIn(2.005, times)
        self.assertEqual(times[-1], 8.017)
        self.assertTrue(all(right > left for left, right in zip(times, times[1:])))
        for index, interval in enumerate(
            right - left for left, right in zip(times, times[1:])
        ):
            decay = math.exp(-interval)
            expected_output = (
                decay * protected.output[index]
                + (1 - decay) * protected.applied[index]
            )
            expected_integral = protected.integral[index] + interval * (
                (-0.5 if times[index] >= 2.005 else 2.0)
                - protected.output[index]
                + protected.correction[index]
            )
            self.assertAlmostEqual(protected.output[index + 1], expected_output)
            self.assertAlmostEqual(protected.integral[index + 1], expected_integral)

        _, _, zero_unprotected, zero_protected = simulate(0, 3, 12, 0.01, -1)
        self.assertEqual(zero_unprotected, zero_protected)

    def test_independent_sweeps_broken_case_and_recovery(self):
        gains = (0, 0.25, 0.5, 1, 2, 4, 8)
        release_integrals = []
        recovery_errors = []
        for gain in gains:
            times, _, _, protected = simulate(gain, 3, 12, 0.01)
            integral, _, error = release_metrics(times, 3, protected)
            release_integrals.append(integral)
            recovery_errors.append(error)
        self.assertTrue(
            all(right < left for left, right in zip(release_integrals, release_integrals[1:]))
        )
        self.assertEqual(recovery_errors.index(min(recovery_errors)), gains.index(1))

        duration_integrals = []
        duration_errors = []
        for duration in (1, 2, 3, 4, 5):
            times, _, unprotected, _ = simulate(1, duration, duration + 9, 0.01)
            integral, _, error = release_metrics(times, duration, unprotected)
            duration_integrals.append(integral)
            duration_errors.append(error)
        self.assertEqual(duration_integrals, sorted(duration_integrals))
        self.assertEqual(duration_errors, sorted(duration_errors))

        times, _, broken_unprotected, broken = simulate(0.5, 3, 8, 0.01, -1)
        _, _, recovered_unprotected, recovered = simulate(0.5, 3, 8, 0.01, 1)
        self.assertEqual(broken_unprotected, recovered_unprotected)
        self.assertGreater(broken.integral[-1], 100)
        self.assertEqual(broken.applied[-1], 1)
        self.assertLess(recovered.applied[-1], 0)
        self.assertLess(max(abs(value) for value in recovered.integral), 1)
        self.assertLess(
            release_metrics(times, 3, recovered)[2],
            release_metrics(times, 3, broken)[2],
        )

    def test_duration_lever_preserves_recovery_window_behaviorally(self):
        interactive = self.read("interactive.m")
        self.assertIn("recoveryViewSec = 9", interactive)
        self.assertRegex(
            interactive,
            r"modelFunction\(antiWindupGain,demandDurationSec,\s*\.\.\.\s*"
            r"demandDurationSec\+recoveryViewSec,0\.01\)",
        )

        recovery_errors = []
        for duration in (1, 3, 5):
            times, _, unprotected, _ = simulate(
                1, duration, duration + 9, 0.01
            )
            release_index = times.index(duration)
            self.assertEqual(times[-1] - times[release_index], 9)
            self.assertEqual(len(times[release_index:]), 901)
            recovery_errors.append(
                release_metrics(times, duration, unprotected)[2]
            )
        self.assertTrue(
            all(
                right > left
                for left, right in zip(recovery_errors, recovery_errors[1:])
            )
        )

    def test_experiment_has_views_metrics_two_isolated_sweeps_and_recovery(self):
        experiment = self.read("experiment.m")
        lowered = experiment.lower()
        self.assertGreaterEqual(experiment.count("%%"), 13)
        self.assertIn("sweep 1 - move only anti-windup gain", lowered)
        self.assertIn(
            "sweep 2 - reset gain and move only high-demand duration", lowered
        )
        self.assertIn("broken case - reverse the back-calculation sign", lowered)
        self.assertIn("antiwindupgains = [0 0.25 0.5 1 2 4 8]", lowered)
        self.assertIn("demanddurationssec = [1 2 3 4 5]", lowered)
        self.assertIn("broken = model(0.5,3,8,0.01,-1)", lowered)
        self.assertIn("recovered = model(0.5,3,8,0.01,1)", lowered)
        self.assertIn("stairs(baseline.t,baseline.reference", lowered)
        self.assertIn("stairs(broken.t,broken.reference", lowered)
        self.assertGreaterEqual(lowered.count("xlabel("), 10)
        self.assertGreaterEqual(lowered.count("ylabel("), 10)
        self.assertGreaterEqual(lowered.count("fprintf("), 2)
        for unit in ("(s)", "(1/s)", "(output)", "(actuator)", "(output*s)"):
            self.assertIn(unit, lowered)

    def test_interactive_controls_are_bounded_immediate_and_resettable(self):
        interactive = self.read("interactive.m")
        for marker in (
            "Anti-windup gain Kaw (1/s)",
            "High-demand duration (s)",
            "'Limits',[0 8]",
            "'Limits',[1 5]",
            "Reset baseline",
            "gainControl.Value = 1",
            "durationControl.Value = 3",
            "ValueChangingFcn",
            "ValueChangedFcn",
            "modelFunction = @model",
            "recoveryViewSec = 9",
            "result.unprotected.integralState",
            "result.protected.integralState",
            "result.protected.appliedControl",
            "Kaw=0: paths coincide",
            "stairs(axOutput,result.t,result.reference",
            "Time (s)",
        ):
            self.assertIn(marker, interactive)

    def test_checks_cover_limits_malformed_inputs_recovery_and_resources(self):
        checks = self.read("run_checks.m")
        self.assertGreaterEqual(checks.count("assert("), 30)
        for marker in (
            "isequaln(baselineA,baselineB)",
            "expectedApplied = max(-baselineA.controlLimit",
            "unprotectedPlantResidual",
            "protectedIntegralResidual",
            "highDemandMask",
            "model(0,3,12,0.01,1)",
            "antiWindupGains = [0 0.25 0.5 1 2 4 8]",
            "demandDurationsSec = [1 2 3 4 5]",
            "changed.horizonSec-changed.demandDurationSec == 9",
            "model(0.5,3,8,0.01,-1)",
            "model(0.5,3,8,0.01,1)",
            "model(NaN,3,12,0.01)",
            "model([1 2],3,12,0.01)",
            "P12:AntiWindupGainRange",
            "P12:DemandDurationRange",
            "P12:HorizonRange",
            "P12:DisplayResolution",
            "P12:BackCalculationSign",
            "P12:TooManySamples",
            "P12:ResponseBound",
            "boundedGrid.sampleCount == 20001",
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
        self.assertNotRegex(
            self.read("model.m").lower(),
            r"\b(?:rng|rand|randn|load|save|fopen|readtable|writetable|webread|"
            r"system|timer|pause|parfeval)\s*\(|\b(?:global|persistent)\b",
        )
        for marker in (
            QUESTION,
            "P05",
            "P06",
            "P09",
            "P10",
            "P11",
            "teach-back",
            "mechanism",
            "requested",
            "applied",
            "integral state",
            "back-calculation",
            "actuator authority",
        ):
            self.assertIn(marker, combined)


if __name__ == "__main__":
    unittest.main()
