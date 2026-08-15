from __future__ import annotations

import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
QUESTION = (
    "What inputs, observable effects, and failure modes matter when you model "
    "Sensor and Actuator Dynamics?"
)
SENSOR_TAU_VALUES = [0, 0.02, 0.05, 0.1, 0.2, 0.4]
ACTUATOR_TAU_VALUES = [0, 0.05, 0.1, 0.2, 0.4, 0.8]


def reference_run(
    actuator_tau: float = 0.2,
    sensor_tau: float = 0.1,
    half_period: float = 2,
    amplitude: float = 20,
    actuator_limit: float = 30,
    sensor_bias: float = 0,
    time_step: float = 0.02,
    duration: float = 8,
) -> dict[str, object]:
    allocated_count = round(duration / time_step) + 1
    samples_per_half_period = round(half_period / time_step)
    time = [index * time_step for index in range(allocated_count)]
    request = [
        amplitude
        * (1 - 2 * ((index // samples_per_half_period) % 2))
        for index in range(allocated_count)
    ]
    limited = [
        min(max(value, -actuator_limit), actuator_limit)
        for value in request
    ]
    actual = [0.0] * allocated_count
    sensor_dynamic = [0.0] * allocated_count
    actuator_decay = 0.0 if actuator_tau == 0 else math.exp(-time_step / actuator_tau)
    sensor_decay = 0.0 if sensor_tau == 0 else math.exp(-time_step / sensor_tau)
    if actuator_tau == 0:
        actual[0] = limited[0]
    if sensor_tau == 0:
        sensor_dynamic[0] = actual[0]

    for index in range(1, allocated_count):
        previous_interval_command = limited[index - 1]
        current_command = limited[index]
        previous_actual = actual[index - 1]
        previous_sensor = sensor_dynamic[index - 1]
        if actuator_tau == 0:
            actual[index] = current_command
        else:
            actual[index] = (
                actuator_decay * previous_actual
                + (1 - actuator_decay) * previous_interval_command
            )
        if sensor_tau == 0:
            sensor_dynamic[index] = actual[index]
        elif actuator_tau == 0:
            sensor_dynamic[index] = (
                sensor_decay * previous_sensor
                + (1 - sensor_decay) * previous_interval_command
            )
        else:
            equality_tolerance = math.sqrt(math.ulp(1.0)) * max(
                1.0, actuator_tau, sensor_tau
            )
            time_constant_difference = actuator_tau - sensor_tau
            if time_constant_difference == 0:
                coefficient = (
                    0.0
                    if actuator_decay == 0
                    else time_step / actuator_tau * actuator_decay
                )
            elif abs(time_constant_difference) <= equality_tolerance:
                if actuator_decay == 0 and sensor_decay == 0:
                    coefficient = 0.0
                else:
                    exponent_difference = (
                        time_step
                        / sensor_tau
                        * (time_constant_difference / actuator_tau)
                    )
                    coefficient = (
                        time_step
                        / sensor_tau
                        * actuator_decay
                        * (-math.expm1(-exponent_difference) / exponent_difference)
                    )
            else:
                coefficient = (
                    actuator_tau
                    / time_constant_difference
                    * (actuator_decay - sensor_decay)
                )
            sensor_dynamic[index] = (
                sensor_decay * previous_sensor
                + (1 - sensor_decay) * previous_interval_command
                + coefficient * (previous_actual - previous_interval_command)
            )

    measured = [value + sensor_bias for value in sensor_dynamic]
    actuator_error = [
        requested - applied for requested, applied in zip(request, actual)
    ]
    sensor_error = [
        applied - sensed for applied, sensed in zip(actual, sensor_dynamic)
    ]
    reported_error = [
        applied - sensed for applied, sensed in zip(actual, measured)
    ]
    tolerance = 64 * math.ulp(max(1.0, amplitude, actuator_limit))
    saturated = [
        abs(value) > actuator_limit + tolerance for value in request
    ]
    opposite = [
        requested * sensed < 0 and abs(sensed) > 0.01 * amplitude
        for requested, sensed in zip(request, sensor_dynamic)
    ]

    def rms(values: list[float]) -> float:
        return math.sqrt(sum(value**2 for value in values) / len(values))

    first_plateau_index = min(samples_per_half_period, allocated_count) - 1
    return {
        "actuator_tau": actuator_tau,
        "sensor_tau": sensor_tau,
        "half_period": half_period,
        "amplitude": amplitude,
        "actuator_limit": actuator_limit,
        "sensor_bias": sensor_bias,
        "time_step": time_step,
        "duration": duration,
        "allocated_count": allocated_count,
        "samples_per_half_period": samples_per_half_period,
        "time": time,
        "request": request,
        "limited": limited,
        "actual": actual,
        "sensor_dynamic": sensor_dynamic,
        "measured": measured,
        "actuator_error": actuator_error,
        "sensor_error": sensor_error,
        "reported_error": reported_error,
        "saturated": saturated,
        "opposite": opposite,
        "actuator_rms": rms(actuator_error),
        "sensor_rms": rms(sensor_error),
        "reported_rms": rms(reported_error),
        "saturation_duration": sum(saturated[:-1]) * time_step,
        "opposite_duration": sum(opposite[:-1]) * time_step,
        "peak_actual": max(abs(value) for value in actual),
        "peak_measured": max(abs(value) for value in measured),
        "first_plateau_actual": actual[first_plateau_index],
        "first_plateau_measured": measured[first_plateau_index],
    }


class P23ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P23"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(
            {
                "number": self.module["number"],
                "id": self.module["id"],
                "title": self.module["title"],
                "guiding_question": self.module["guiding_question"],
                "phase": self.module["phase"],
                "phase_title": self.module["phase_title"],
                "slug": self.module["slug"],
                "folder": self.module["folder"],
                "status": self.module["status"],
                "implementation_batch": self.module["implementation_batch"],
                "prerequisites": self.module["prerequisites"],
                "evidence_level": self.module["evidence_level"],
            },
            {
                "number": 23,
                "id": "P23",
                "title": "Model Sensor and Actuator Dynamics",
                "guiding_question": QUESTION,
                "phase": 6,
                "phase_title": "Guidance and HIL",
                "slug": "model-sensor-and-actuator-dynamics",
                "folder": "modules/23-model-sensor-and-actuator-dynamics",
                "status": "implemented",
                "implementation_batch": "P23",
                "prerequisites": ["P22"],
                "evidence_level": "simulated",
            },
        )
        prerequisite = next(
            module for module in self.manifest["modules"] if module["id"] == "P22"
        )
        self.assertEqual(prerequisite["status"], "implemented")

    def test_complete_artifact_set_and_clean_eof(self):
        required = (
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
        for name in required:
            with self.subTest(name=name):
                path = self.folder / name
                self.assertTrue(path.is_file(), name)
                content = path.read_bytes()
                self.assertTrue(content.endswith(b"\n"), name)
                self.assertFalse(content.endswith(b"\n\n"), name)

    def test_model_is_transparent_deterministic_and_resource_bounded(self):
        model = self.read("model.m")
        for marker in (
            "commandSign = 1-2*mod(floor(sampleIndex/samplesPerHalfPeriod),2)",
            "limitedCommandMPerSec2 = min(max(requestedAccelerationMPerSec2, ...",
            "actuatorDecay = exp(-timeStepSec/actuatorTimeConstantSec)",
            "sensorDecay = exp(-timeStepSec/sensorTimeConstantSec)",
            "actualAccelerationMPerSec2(k) = actuatorDecay* ...",
            "cascadeCoefficient = ...",
            "(timeStepSec/actuatorTimeConstantSec)*actuatorDecay",
            "(actuatorDecay-sensorDecay)",
            "maximumStepCount = 5001",
            "P23:ActuatorTimeConstantRange",
            "P23:SensorTimeConstantRange",
            "P23:CommandHalfPeriodRange",
            "P23:CommandAmplitudeRange",
            "P23:ActuatorLimitRange",
            "P23:SensorBiasRange",
            "P23:TimeStepRange",
            "P23:DurationRange",
            "P23:TimeGridMismatch",
            "P23:CommandGridMismatch",
            "P23:StepCountRange",
        ):
            self.assertIn(marker, model)
        self.assertLess(
            model.index("allocatedStepCount > maximumStepCount"),
            model.index("timeSec = (0:roundedDurationRatio)*timeStepSec"),
        )
        self.assertNotRegex(
            model.lower(),
            r"\b(?:plot|figure|uifigure|uiaxes|uislider|uidropdown|rng|rand|randn|"
            r"global|persistent|fopen|webread|webwrite|system|parfor)\s*\(?",
        )

    def test_independent_baseline_recurrence_and_analytic_step_limit(self):
        baseline_a = reference_run()
        baseline_b = reference_run()
        self.assertEqual(baseline_a, baseline_b)
        first_time = (baseline_a["samples_per_half_period"] - 1) * 0.02
        expected_actual = 20 * (1 - math.exp(-first_time / 0.2))
        expected_sensor = 20 * (
            1
            - (
                0.2 * math.exp(-first_time / 0.2)
                - 0.1 * math.exp(-first_time / 0.1)
            )
            / (0.2 - 0.1)
        )
        self.assertAlmostEqual(baseline_a["first_plateau_actual"], expected_actual)
        self.assertAlmostEqual(baseline_a["first_plateau_measured"], expected_sensor)
        self.assertAlmostEqual(baseline_a["first_plateau_actual"], 19.99899650635887)
        self.assertAlmostEqual(baseline_a["first_plateau_measured"], 19.997993063067714)
        self.assertAlmostEqual(baseline_a["actuator_rms"], 8.690359273336114)
        self.assertAlmostEqual(baseline_a["sensor_rms"], 3.287018981667333)
        self.assertAlmostEqual(baseline_a["opposite_duration"], 0.78)
        self.assertEqual(baseline_a["saturation_duration"], 0)
        self.assertTrue(all(abs(value) <= 30 for value in baseline_a["actual"]))
        self.assertTrue(all(abs(value) <= 30 for value in baseline_a["sensor_dynamic"]))
        reversal = baseline_a["samples_per_half_period"]
        self.assertEqual(baseline_a["request"][reversal], -20)
        self.assertGreater(
            baseline_a["actual"][reversal], baseline_a["actual"][reversal - 1]
        )
        self.assertGreater(
            baseline_a["sensor_dynamic"][reversal],
            baseline_a["sensor_dynamic"][reversal - 1],
        )
        self.assertAlmostEqual(
            baseline_a["actual"][reversal], 20 * (1 - math.exp(-2 / 0.2))
        )
        self.assertLess(
            baseline_a["actual"][reversal + 1], baseline_a["actual"][reversal]
        )

    def test_two_sweeps_are_independent_and_cross_dynamic_limits(self):
        baseline = reference_run()
        sensor_runs = [reference_run(sensor_tau=value) for value in SENSOR_TAU_VALUES]
        for run in sensor_runs:
            self.assertEqual(run["actuator_tau"], 0.2)
            self.assertEqual(run["half_period"], 2)
            self.assertEqual(run["request"], baseline["request"])
            self.assertEqual(run["actual"], baseline["actual"])
        sensor_errors = [run["sensor_rms"] for run in sensor_runs]
        self.assertEqual(sensor_errors[0], 0)
        self.assertTrue(all(a < b for a, b in zip(sensor_errors, sensor_errors[1:])))

        actuator_runs = [
            reference_run(actuator_tau=value) for value in ACTUATOR_TAU_VALUES
        ]
        for run in actuator_runs:
            self.assertEqual(run["sensor_tau"], 0.1)
            self.assertEqual(run["half_period"], 2)
            self.assertEqual(run["request"], baseline["request"])
        actuator_errors = [run["actuator_rms"] for run in actuator_runs]
        self.assertEqual(actuator_errors[0], 0)
        self.assertTrue(
            all(a < b for a, b in zip(actuator_errors, actuator_errors[1:]))
        )

    def test_limiting_broken_saturation_bias_recovery_and_resource_cases(self):
        ideal = reference_run(actuator_tau=0, sensor_tau=0)
        self.assertEqual(ideal["actual"], ideal["limited"])
        self.assertEqual(ideal["sensor_dynamic"], ideal["actual"])
        self.assertEqual(ideal["actuator_rms"], 0)
        self.assertEqual(ideal["sensor_rms"], 0)

        equal_tau = reference_run(actuator_tau=0.2, sensor_tau=0.2)
        near_equal_tau = reference_run(actuator_tau=0.2, sensor_tau=0.2 + 1e-10)
        decay = math.exp(-0.02 / 0.2)
        coefficient = 0.02 / 0.2 * decay
        expected_sensor_first = (1 - decay) * 20 + coefficient * (0 - 20)
        self.assertAlmostEqual(equal_tau["sensor_dynamic"][1], expected_sensor_first)
        self.assertTrue(all(math.isfinite(value) for value in equal_tau["sensor_dynamic"]))
        self.assertTrue(
            all(math.isfinite(value) for value in near_equal_tau["sensor_dynamic"])
        )
        self.assertLess(
            max(
                abs(near - exact)
                for near, exact in zip(
                    near_equal_tau["sensor_dynamic"], equal_tau["sensor_dynamic"]
                )
            ),
            2e-8,
        )

        saturated = reference_run(amplitude=50, actuator_limit=15)
        self.assertEqual(set(abs(value) for value in saturated["limited"]), {15})
        self.assertLessEqual(saturated["peak_actual"], 15)
        self.assertEqual(saturated["saturation_duration"], 8)

        baseline = reference_run()
        biased = reference_run(sensor_bias=5)
        self.assertEqual(biased["actual"], baseline["actual"])
        self.assertEqual(biased["sensor_dynamic"], baseline["sensor_dynamic"])
        self.assertTrue(
            all(
                abs(biased_value - baseline_value + 5) < 1e-12
                for biased_value, baseline_value in zip(
                    biased["reported_error"], baseline["reported_error"]
                )
            )
        )

        broken = reference_run(
            actuator_tau=0.8,
            sensor_tau=0.6,
            half_period=0.1,
            time_step=0.01,
            duration=4,
        )
        self.assertLess(broken["peak_actual"], 3)
        self.assertLess(broken["peak_measured"], 1)
        self.assertGreater(broken["opposite_duration"], 0.5)
        bandwidth_recovered = reference_run(
            actuator_tau=0.8,
            sensor_tau=0.6,
            half_period=4,
            time_step=0.01,
            duration=4,
        )
        self.assertGreater(bandwidth_recovered["peak_actual"], 19)
        self.assertGreater(bandwidth_recovered["peak_measured"], 19)
        self.assertEqual(bandwidth_recovered["opposite_duration"], 0)
        self.assertEqual(reference_run(), baseline)

        minimum = reference_run(time_step=0.05, duration=4)
        self.assertEqual(minimum["allocated_count"], 81)
        self.assertEqual(minimum["time"][-1], 4)
        maximum = reference_run(
            actuator_tau=1.5,
            sensor_tau=1.5,
            half_period=0.2,
            amplitude=80,
            actuator_limit=100,
            sensor_bias=20,
            time_step=0.004,
            duration=20,
        )
        self.assertEqual(maximum["allocated_count"], 5001)
        for field in ("actual", "sensor_dynamic", "measured"):
            self.assertTrue(all(math.isfinite(value) for value in maximum[field]))
        self.assertLessEqual(maximum["peak_actual"], 80)
        self.assertLessEqual(maximum["peak_measured"], 100)

    def test_smallest_positive_time_constants_have_finite_ideal_limit(self):
        smallest_positive = sys.float_info.min * sys.float_info.epsilon
        self.assertGreater(smallest_positive, 0)
        result = reference_run(
            actuator_tau=smallest_positive,
            sensor_tau=smallest_positive,
        )
        for field in ("actual", "sensor_dynamic", "measured"):
            self.assertTrue(all(math.isfinite(value) for value in result[field]))
        self.assertEqual(result["actual"], result["sensor_dynamic"])
        self.assertEqual(result["actual"][0], 0)
        self.assertEqual(result["actual"][1], 20)

        model = self.read("model.m")
        checks = self.read("run_checks.m")
        self.assertIn("if actuatorDecay == 0", model)
        self.assertIn("smallestPositiveTimeConstantSec = realmin*eps", checks)

    def test_experiment_has_ordered_flow_labels_metrics_sweeps_and_broken_case(self):
        experiment = self.read("experiment.m")
        ordered = (
            "%% Read:",
            "%% Make one prediction",
            "%% Visualize the deterministic baseline",
            "%% Read the mechanism:",
            "%% Move lever 1:",
            "%% Explain lever 1",
            "%% Reset, then move lever 2:",
            "%% Explain lever 2",
            "%% Deliberately broken case:",
            "%% Check, recover, and teach back",
        )
        positions = [experiment.index(marker) for marker in ordered]
        self.assertEqual(positions, sorted(positions))
        for marker in (
            "baseline = model(0.2,0.1,2,20,30,0,0.02,8)",
            "sensorTimeConstantValuesSec = [0 0.02 0.05 0.1 0.2 0.4]",
            "actuatorTimeConstantValuesSec = [0 0.05 0.1 0.2 0.4 0.8]",
            "changed = model(0.2,sensorTimeConstantValuesSec(k),2,20,30,0,0.02,8)",
            "changed = model(actuatorTimeConstantValuesSec(k),0.1,2,20,30,0,0.02,8)",
            "broken = model(0.8,0.6,0.1,20,30,0,0.01,4)",
            "recovered = model(0.2,0.1,2,20,30,0,0.02,8)",
            "Time (s)",
            "Lateral acceleration (m/s^2)",
            "Sensor time constant (s)",
            "Actuator time constant (s)",
            "Opposite-sign time (s)",
            "run_checks;",
        ):
            self.assertIn(marker, experiment)
        self.assertGreaterEqual(experiment.count("figure("), 5)
        self.assertEqual(experiment.count("%% Make one prediction"), 1)
        self.assertEqual(experiment.count("clear run_checks;"), 1)
        self.assertLess(
            experiment.index("clear run_checks;"),
            experiment.index("\nrun_checks;\n"),
        )

    def test_interactive_has_controls_reset_feedback_and_mechanism_precedence(self):
        interactive = self.read("interactive.m")
        for marker in (
            "function interactive",
            "uifigure(",
            "uiaxes(",
            "uislider(",
            "uispinner(",
            "Actuator time constant (s)",
            "Sensor time constant (s)",
            "Command half-period (s)",
            "Actuator limit (m/s^2)",
            "Sensor bias (m/s^2)",
            "ValueChangingFcn",
            "ValueChangedFcn",
            "ButtonPushedFcn",
            "resetBaseline",
            "redraw(0.2,0.1,2,30,0)",
            "result = modelFunction(actuatorTau,sensorTau,halfPeriod,20, ...",
            "magnitude-limited",
            "biased measurement",
            "bandwidth separation is weak",
            "Opposite-sign time",
            "Saturation time",
        ):
            self.assertIn(marker, interactive)
        self.assertGreaterEqual(interactive.count("uiaxes("), 2)
        self.assertLess(
            interactive.index("if result.saturationDurationSec > 0"),
            interactive.index("elseif abs(sensorBias) > 0"),
        )

    def test_checks_cover_oracles_limits_malformed_bounds_and_recovery(self):
        checks = self.read("run_checks.m")
        for marker in (
            "isequaln(baselineA,baselineB)",
            "expectedRequest",
            "expectedLimited",
            "expectedActual",
            "expectedSensor",
            "expectedFirstActuator",
            "expectedFirstSensor",
            "sensorTimeConstantValuesSec = [0 0.02 0.05 0.1 0.2 0.4]",
            "actuatorTimeConstantValuesSec = [0 0.05 0.1 0.2 0.4 0.8]",
            "ideal = model(0,0,2,20,30,0,0.02,8)",
            "equalTau = model(0.2,0.2,2,20,30,0,0.02,8)",
            "nearEqualTau = model(0.2,0.2+1e-10,2,20,30,0,0.02,8)",
            "smallestPositiveTimeConstantSec = realmin*eps",
            "saturated = model(0.2,0.1,2,50,15,0,0.02,8)",
            "biased = model(0.2,0.1,2,20,30,5,0.02,8)",
            "broken = model(0.8,0.6,0.1,20,30,0,0.01,4)",
            "bandwidthRecovered = model(0.8,0.6,4,20,30,0,0.01,4)",
            "shortDuration = model(0.2,0.1,2,20,30,0,0.05,4)",
            "recovered = model(0.2,0.1,2,20,30,0,0.02,8)",
            "P23:ActuatorTimeConstantRange",
            "P23:SensorTimeConstantRange",
            "P23:CommandGridMismatch",
            "P23:StepCountRange",
            "boundedHistory = model(1.5,1.5,0.2,80,100,20,0.004,20)",
            "assertAnyError",
            "assertErrorId",
        ):
            self.assertIn(marker, checks)

    def test_tutor_text_connects_prerequisite_and_preserves_claim_boundary(self):
        combined = "\n".join(
            self.read(name)
            for name in ("README.md", "lesson.md", "walkthrough.md", "checks.md")
        )
        for marker in (
            QUESTION,
            "P22",
            "requested",
            "applied",
            "measured",
            "actuator time constant",
            "sensor time constant",
            "actuator limit",
            "sensor bias",
            "bandwidth",
            "0.1 s",
            "0.8 s",
            "0.6 s",
            "exactly two sentences",
            "No MATLAB-runtime",
            "HIL",
        ):
            self.assertIn(marker.lower(), combined.lower())
        for placeholder in (
            "scaffolded",
            "placeholder",
            "todo",
            "not implemented",
            "planned learner sequence",
            "planned concept loop",
        ):
            self.assertNotIn(placeholder, combined.lower())
        opaque_calls = (
            r"\b(?:tf|ss|lsim|c2d|step|bode|ident|arx|greyest|ode45|ode23|"
            r"sim|inv|pinv|eig|fmincon|quadprog|solve)\s*\("
        )
        for name in (
            "model.m",
            "experiment.m",
            "interactive.m",
            "run_checks.m",
            "lesson.m",
        ):
            self.assertNotRegex(self.read(name), re.compile(opaque_calls, re.I))

    def test_learner_frontier_documents_include_permanent_p23_facts(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules/README.md").read_text(encoding="utf-8")
        self.assertIn("./bin/learn start P23", root_readme)
        self.assertIn("P23", start_here)
        p23_row = next(
            line for line in module_index.splitlines() if line.startswith("| P23 |")
        )
        self.assertTrue(p23_row.endswith("| implemented |"))

    def test_readme_path_scope_and_public_cli_state_isolation(self):
        readme = self.read("README.md")
        self.assertIn(
            'moduleFolder = fullfile(pwd,"modules","23-model-sensor-and-actuator-dynamics");',
            readme,
        )
        self.assertIn('addpath(moduleFolder,"-begin");', readme)
        self.assertIn("clear model interactive;", readme)
        self.assertEqual(readme.count("rmpath(moduleFolder);"), 2)
        self.assertIn("rethrow(exception)", readme)

        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            shutil.copytree(ROOT / "bin", fixture / "bin")
            shutil.copytree(ROOT / "curriculum", fixture / "curriculum")
            shutil.copytree(self.folder, fixture / self.module["folder"])
            progress_file = fixture / ".learning/progress.json"
            progress_file.parent.mkdir(parents=True)
            original = {
                "current": "P22",
                "completed": {"P21": True},
                "notes": {"P21": "preserve prior note"},
            }
            progress_file.write_text(
                json.dumps(original, indent=2) + "\n", encoding="utf-8"
            )
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"

            checked = subprocess.run(
                [str(fixture / "bin/learn"), "check", "P23"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(
                checked.stdout, "Run in MATLAB: run_module_checks('P23')\n"
            )
            self.assertEqual(json.loads(progress_file.read_text()), original)

            started = subprocess.run(
                [str(fixture / "bin/learn"), "start", "P23"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertIn(f"Guiding question: {QUESTION}", started.stdout)
            retained = json.loads(progress_file.read_text())
            self.assertEqual(retained["current"], "P23")
            self.assertEqual(retained["completed"], original["completed"])
            self.assertEqual(retained["notes"], original["notes"])

            continued = subprocess.run(
                [str(fixture / "bin/learn"), "continue"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(continued.returncode, 0, continued.stderr)
            self.assertEqual(continued.stdout, started.stdout)

            teach_back = (
                "Command timing and actuator tau separate the request from applied motion. "
                "Sensor tau and bias separate that motion from the reported measurement."
            )
            completed = subprocess.run(
                [
                    str(fixture / "bin/learn"),
                    "complete",
                    "P23",
                    "--note",
                    teach_back,
                ],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            retained = json.loads(progress_file.read_text())
            self.assertEqual(retained["completed"], {"P21": True, "P23": True})
            self.assertEqual(retained["notes"]["P21"], "preserve prior note")
            self.assertEqual(retained["notes"]["P23"], teach_back)


if __name__ == "__main__":
    unittest.main()
