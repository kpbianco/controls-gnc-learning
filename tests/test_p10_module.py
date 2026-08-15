from __future__ import annotations

import cmath
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTION = (
    "What inputs, observable effects, and failure modes matter when you "
    "expose Delay and Sampling Limits?"
)
GAIN = 8.0


def timing_coefficients(
    sample_period: float, computation_delay: float
) -> tuple[float, float, float]:
    """Independent exact weights for old and new constant-command pieces."""
    plant_decay = math.exp(-sample_period)
    old_command_decay = math.exp(-computation_delay)
    new_command_decay = math.exp(-(sample_period - computation_delay))
    previous_weight = new_command_decay * (1 - old_command_decay)
    new_weight = 1 - new_command_decay
    return plant_decay, previous_weight, new_weight


def delayed_poles(sample_period: float, computation_delay: float) -> tuple[complex, complex]:
    """Independent poles of deviations [output, previous command]."""
    plant_decay, previous_weight, new_weight = timing_coefficients(
        sample_period, computation_delay
    )
    trace = plant_decay - GAIN * new_weight
    determinant = GAIN * previous_weight
    discriminant = trace**2 - 4 * determinant
    return (
        (trace + cmath.sqrt(discriminant)) / 2,
        (trace - cmath.sqrt(discriminant)) / 2,
    )


def sampled_response(
    sample_period: float, computation_delay: float, horizon: float
) -> tuple[list[float], list[float], list[float]]:
    """Independent sample recurrence for the delayed proportional loop."""
    decay, previous_weight, new_weight = timing_coefficients(
        sample_period, computation_delay
    )
    sample_count = math.floor(horizon / sample_period) + 1
    output = [0.0]
    computed: list[float] = []
    previous: list[float] = []
    previous_command = 0.0
    for index in range(sample_count):
        previous.append(previous_command)
        command = GAIN * (1 - output[index])
        computed.append(command)
        if index < sample_count - 1:
            output.append(
                decay * output[index]
                + previous_weight * previous_command
                + new_weight * command
            )
        previous_command = command
    return output, computed, previous


def reconstruct_output(
    sample_period: float,
    computation_delay: float,
    horizon: float,
    display_step: float,
) -> tuple[list[float], list[float], list[float]]:
    """Independent exact intersample output and applied-command reconstruction."""
    output_samples, computed, previous = sampled_response(
        sample_period, computation_delay, horizon
    )
    tolerance = 8 * math.ulp(max(horizon, display_step))
    regular_times = [
        index * display_step
        for index in range(math.floor(horizon / display_step) + 1)
    ]
    if horizon - regular_times[-1] > tolerance:
        regular_times.append(horizon)
    else:
        regular_times[-1] = horizon
    sample_times = [index * sample_period for index in range(len(output_samples))]
    switch_times = [
        min(sample_time + computation_delay, horizon)
        for sample_time in sample_times
        if sample_time + computation_delay <= horizon + tolerance
    ]
    candidates = sorted(
        [(time, False) for time in regular_times]
        + [(time, True) for time in sample_times + switch_times]
    )
    display_times: list[float] = []
    candidate_index = 0
    while candidate_index < len(candidates):
        cluster_end = candidate_index
        while (
            cluster_end + 1 < len(candidates)
            and candidates[cluster_end + 1][0] - candidates[candidate_index][0]
            <= tolerance
        ):
            cluster_end += 1
        cluster = candidates[candidate_index : cluster_end + 1]
        events = [time for time, is_event in cluster if is_event]
        display_times.append(events[-1] if events else cluster[0][0])
        candidate_index = cluster_end + 1

    output: list[float] = []
    applied: list[float] = []
    for time in display_times:
        sample_index = min(
            math.floor((time + tolerance) / sample_period),
            len(output_samples) - 1,
        )
        elapsed = time - sample_index * sample_period
        if elapsed < computation_delay - tolerance:
            command = previous[sample_index]
            value = command + (output_samples[sample_index] - command) * math.exp(
                -elapsed
            )
        else:
            switch_output = previous[sample_index] + (
                output_samples[sample_index] - previous[sample_index]
            ) * math.exp(-computation_delay)
            command = computed[sample_index]
            value = command + (switch_output - command) * math.exp(
                -(elapsed - computation_delay)
            )
        applied.append(command)
        output.append(value)
    return display_times, output, applied


def continuous_target(time: float) -> float:
    return GAIN / (1 + GAIN) * (1 - math.exp(-(1 + GAIN) * time))


class P10ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P10"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 10)
        self.assertEqual(self.module["title"], "Expose Delay and Sampling Limits")
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["phase"], 3)
        self.assertEqual(self.module["phase_title"], "Digital and constrained control")
        self.assertEqual(self.module["prerequisites"], ["P09"])
        self.assertEqual(self.module["implementation_batch"], "P10")
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
            "oldCommandDecay = exp(-computationDelaySec/plantTimeConstantSec)",
            "newCommandDurationSec = samplePeriodSec-computationDelaySec",
            "previousCommandWeight = newCommandDecay*(1-oldCommandDecay)",
            "newCommandWeight = 1-newCommandDecay",
            "computedCommandSamples(k) = proportionalGain*(",
            "previousCommandWeight*previousCommand+",
            "stateMatrix = [stateA11 stateA12; -proportionalGain 0]",
            "poleDiscriminant = poleTrace^2-4*poleDeterminant",
        ):
            self.assertIn(formula, model)
        for validation in (
            "mustBeReal",
            "mustBeFinite",
            "mustBePositive",
            "mustBeNonnegative",
            "maxControllerSamples = 10001",
            "maxDisplaySamples = 30001",
            "responseLimit = 1000",
            "P10:DelayRange",
            "P10:DisplayResolution",
            "P10:TooManyControllerSamples",
            "P10:TooManyDisplaySamples",
            "P10:ResponseBound",
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

    def test_independent_coefficients_poles_and_limiting_cases(self):
        decay, previous_weight, new_weight = timing_coefficients(0.05, 0.01)
        self.assertAlmostEqual(decay, 0.951229424500714)
        self.assertAlmostEqual(previous_weight, 0.009560014651609149)
        self.assertAlmostEqual(new_weight, 0.03921056084767682)
        self.assertAlmostEqual(decay + previous_weight + new_weight, 1)

        baseline_poles = delayed_poles(0.05, 0.01)
        self.assertAlmostEqual(max(map(abs, baseline_poles)), 0.47731511198762067)
        self.assertLess(max(map(abs, delayed_poles(0.1, 0.02))), 0.39)
        self.assertGreater(max(map(abs, delayed_poles(0.2, 0.18))), 1.13)
        self.assertLess(max(map(abs, delayed_poles(0.2, 0.02))), 0.37)

        zero_delay = timing_coefficients(0.05, 0)
        full_delay = timing_coefficients(0.05, 0.05)
        self.assertEqual(zero_delay[1], 0)
        self.assertAlmostEqual(zero_delay[2], 1 - math.exp(-0.05))
        self.assertAlmostEqual(full_delay[1], 1 - math.exp(-0.05))
        self.assertEqual(full_delay[2], 0)

    def test_independent_sampled_and_intersample_behavioral_regression(self):
        output, computed, previous = sampled_response(0.05, 0.01, 4)
        self.assertEqual(output[0], 0)
        self.assertEqual(computed[0], 8)
        self.assertEqual(previous[0], 0)
        self.assertAlmostEqual(output[1], 0.3136844867814146)
        self.assertAlmostEqual(output[2], 0.5901525605828551)
        self.assertAlmostEqual(computed[1], 5.490524105748683)
        self.assertEqual(previous[1], 8)
        self.assertAlmostEqual(output[-1], 8 / 9)

        times, displayed, applied = reconstruct_output(0.03, 0.01, 0.097, 0.005)
        sample_output, sample_commands, previous_commands = sampled_response(
            0.03, 0.01, 0.097
        )
        self.assertEqual(times[-1], 0.097)
        for display_index, sample_index in zip((0, 6, 12, 18), range(4)):
            self.assertAlmostEqual(displayed[display_index], sample_output[sample_index])
        self.assertEqual(applied[:2], [0, 0])
        self.assertEqual(applied[2:6], [sample_commands[0]] * 4)
        self.assertEqual(applied[-1], previous_commands[-1])
        expected_final = previous_commands[-1] + (
            sample_output[-1] - previous_commands[-1]
        ) * math.exp(-0.007)
        self.assertAlmostEqual(displayed[-1], expected_final)

        checks = self.read("run_checks.m")
        for marker in (
            "sampleTransitionResidual",
            "displayedAtSamples = baselineA.sampledOutput(1:10:end)",
            "expectedPostSwitchOutput = 8*(1-exp(-0.005))",
            "oldCommandActive = elapsed < computationDelaySec-timeTolerance",
            "expectedFinalDelayedOutput = nonIntegerGrid.previousCommandSamples(end)+("
        ):
            self.assertIn(marker, checks if marker != "oldCommandActive = elapsed < computationDelaySec-timeTolerance" else self.read("model.m"))

    def test_off_grid_sample_and_delay_events_are_behaviorally_retained(self):
        sample_period = 0.033
        computation_delay = 0.011
        times, displayed, applied = reconstruct_output(
            sample_period, computation_delay, 0.08, 0.01
        )
        sample_output, sample_commands, previous_commands = sampled_response(
            sample_period, computation_delay, 0.08
        )
        expected_events = (0.011, 0.033, 0.044, 0.066, 0.077)
        event_indices = []
        for event_time in expected_events:
            matching = [
                index
                for index, actual_time in enumerate(times)
                if actual_time == event_time
            ]
            self.assertEqual(matching, [matching[0]] if matching else [])
            self.assertTrue(matching, f"missing timing event {event_time}")
            event_indices.append(matching[0])

        first_switch, second_sample, second_switch, _, _ = event_indices
        self.assertEqual(applied[first_switch], sample_commands[0])
        self.assertEqual(displayed[first_switch], 0)
        self.assertEqual(displayed[second_sample], sample_output[1])
        self.assertEqual(applied[second_sample], previous_commands[1])
        self.assertEqual(applied[second_switch], sample_commands[1])
        expected_second_switch_output = previous_commands[1] + (
            sample_output[1] - previous_commands[1]
        ) * math.exp(-computation_delay)
        self.assertAlmostEqual(
            displayed[second_switch], expected_second_switch_output
        )

        model = self.read("model.m")
        checks = self.read("run_checks.m")
        for marker in (
            "mergeEventTimes(t,[sampleTimes; switchTimes],timeTolerance)",
            "offGridTiming = model(0.033,0.011,0.08,0.01)",
            "secondSwitchIndex = find(offGridTiming.t == secondSwitchTime,1)",
        ):
            self.assertIn(marker, model if marker.startswith("mergeEventTimes") else checks)

    def test_continuous_target_and_sweep_reference_arithmetic(self):
        self.assertEqual(continuous_target(0), 0)
        self.assertAlmostEqual(continuous_target(0.05), 0.3221083096695348)
        self.assertAlmostEqual(continuous_target(0.1), 0.5274936357861341)
        self.assertAlmostEqual(continuous_target(1), 0.8887791912852563)

        gaps = []
        for sample_period in (0.02, 0.05, 0.1, 0.15, 0.2):
            times, output, _ = reconstruct_output(sample_period, 0, 3, 0.005)
            gaps.append(
                max(
                    abs(actual - continuous_target(time))
                    for actual, time in zip(output, times)
                )
            )
        self.assertEqual(gaps, sorted(gaps))
        self.assertAlmostEqual(gaps[0], 0.028240041177620356)
        self.assertAlmostEqual(gaps[-1], 0.7081974315731113)

        delay_radii = [
            max(map(abs, delayed_poles(0.1, delay)))
            for delay in (0, 0.02, 0.04, 0.06, 0.08, 0.1)
        ]
        self.assertEqual(delay_radii, sorted(delay_radii))

    def test_experiment_has_views_metrics_two_isolated_sweeps_and_recovery(self):
        experiment = self.read("experiment.m")
        lowered = experiment.lower()
        self.assertGreaterEqual(experiment.count("%%"), 13)
        self.assertIn("sweep 1 - move only sample period", lowered)
        self.assertIn("sweep 2 - reset ts and move only computation delay", lowered)
        self.assertIn(
            "broken case - combine a long hold with nearly one-sample delay", lowered
        )
        self.assertIn(
            "sampleperiodssec = [0.02 0.05 0.1 0.15 0.2]", lowered
        )
        self.assertIn(
            "computationdelayssec = [0 0.02 0.04 0.06 0.08 0.1]", lowered
        )
        self.assertIn("broken = model(0.2,0.18,3,0.005)", lowered)
        self.assertIn("recovered = model(0.2,0.02,3,0.005)", lowered)
        self.assertGreaterEqual(lowered.count("xlabel("), 10)
        self.assertGreaterEqual(lowered.count("ylabel("), 10)
        self.assertGreaterEqual(lowered.count("fprintf("), 2)
        for unit in (
            "(s)",
            "(hz)",
            "(rad/s)",
            "(deg)",
            "(dimensionless)",
            "(output)",
        ):
            self.assertIn(unit, lowered)

    def test_interactive_controls_are_bounded_immediate_and_resettable(self):
        interactive = self.read("interactive.m")
        for marker in (
            "Sample period Ts (s)",
            "Computation delay Td / Ts (fraction)",
            "Limits',[0.02 0.2]",
            "Limits',[0 0.95]",
            "Reset baseline",
            "periodControl.Value = 0.05",
            "delayControl.Value = 0.2",
            "ValueChangingFcn",
            "ValueChangedFcn",
            "modelFunction = @model",
            "computationDelaySec = samplePeriodSec*delayFraction",
            "stairs(axCommand,result.t,result.appliedCommand,",
            "Nyquist ratio",
            "not strictly inside unit circle",
            "Time (s)",
        ):
            self.assertIn(marker, interactive)

    def test_checks_cover_limits_malformed_inputs_recovery_and_resources(self):
        checks = self.read("run_checks.m")
        self.assertGreaterEqual(checks.count("assert("), 30)
        for marker in (
            "isequaln(baselineA,baselineB)",
            "model(0.02,0,3,0.005)",
            "model(0.2,0,3,0.005)",
            "model(0.1,0.1,4,0.005)",
            "model(0.005,0,2,0.005)",
            "model(NaN,0.01,4,0.005)",
            "model(0.05,Inf,4,0.005)",
            "model(0.05,0.01,4,[0.005 0.01])",
            "P10:DelayRange",
            "P10:SamplePeriodRange",
            "P10:HorizonRange",
            "P10:DisplayResolution",
            "P10:TooManyControllerSamples",
            "P10:TooManyDisplaySamples",
            "P10:ResponseBound",
            "model(1e-12,0,30,1e-12)",
            "model(0.01,0,30,1e-12)",
            "model(0.0031,0.0007,30,0.0011)",
            "nonIntegerGrid = model(0.03,0.01,0.097,0.005)",
            "atControllerLimit.controllerSampleCount == 10001",
            "atDisplayLimit.displaySampleCount == 30001",
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
            "P07",
            "P09",
            "teach-back",
            "mechanism",
            "sample period",
            "computation delay",
            "previous command",
            "Nyquist",
            "pole magnitude",
            "unit circle",
        ):
            self.assertIn(marker, combined)


if __name__ == "__main__":
    unittest.main()
