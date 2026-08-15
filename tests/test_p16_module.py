from __future__ import annotations

from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
QUESTION = (
    "What inputs, observable effects, and failure modes matter when you fuse "
    "Noisy Sensors with a Kalman Filter?"
)

Matrix = list[list[float]]
Vector = list[float]


def transpose(matrix: Matrix) -> Matrix:
    return [list(column) for column in zip(*matrix)]


def matrix_multiply(left: Matrix, right: Matrix) -> Matrix:
    return [
        [
            sum(left[row][index] * right[index][column] for index in range(len(right)))
            for column in range(len(right[0]))
        ]
        for row in range(len(left))
    ]


def matrix_vector(matrix: Matrix, vector: Vector) -> Vector:
    return [
        sum(matrix[row][column] * vector[column] for column in range(len(vector)))
        for row in range(len(matrix))
    ]


def matrix_add(left: Matrix, right: Matrix) -> Matrix:
    return [
        [left[row][column] + right[row][column] for column in range(len(left[0]))]
        for row in range(len(left))
    ]


def matrix_subtract(left: Matrix, right: Matrix) -> Matrix:
    return [
        [left[row][column] - right[row][column] for column in range(len(left[0]))]
        for row in range(len(left))
    ]


def inverse_two_by_two(matrix: Matrix) -> Matrix:
    determinant = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    return [
        [matrix[1][1] / determinant, -matrix[0][1] / determinant],
        [-matrix[1][0] / determinant, matrix[0][0] / determinant],
    ]


def outer(vector: Vector) -> Matrix:
    return [[left * right for right in vector] for left in vector]


def sequential_sensor_update(
    prior: Vector,
    prior_covariance: Matrix,
    measurement: Vector,
    measurement_covariance: Matrix,
    order: tuple[int, int],
) -> tuple[Vector, Matrix]:
    """Fuse independent scalar sensors in the requested order."""
    estimate = prior[:]
    covariance = [row[:] for row in prior_covariance]
    measurement_row = [[1.0, 0.0]]
    identity = [[1.0, 0.0], [0.0, 1.0]]
    for sensor_index in order:
        predicted = matrix_vector(measurement_row, estimate)[0]
        innovation = measurement[sensor_index] - predicted
        innovation_variance = matrix_multiply(
            matrix_multiply(measurement_row, covariance), transpose(measurement_row)
        )[0][0] + measurement_covariance[sensor_index][sensor_index]
        gain_matrix = matrix_multiply(covariance, transpose(measurement_row))
        gain = [row[0] / innovation_variance for row in gain_matrix]
        estimate = [
            estimate[row] + gain[row] * innovation for row in range(len(estimate))
        ]
        gain_column = [[value] for value in gain]
        correction = matrix_subtract(
            identity, matrix_multiply(gain_column, measurement_row)
        )
        covariance = matrix_add(
            matrix_multiply(
                matrix_multiply(correction, covariance), transpose(correction)
            ),
            [
                [
                    gain[left]
                    * measurement_covariance[sensor_index][sensor_index]
                    * gain[right]
                    for right in range(2)
                ]
                for left in range(2)
            ],
        )
    return estimate, covariance


def deterministic_normal(value_count: int, seed: int) -> list[float]:
    modulus = 2_147_483_647
    multiplier = 16_807
    state = seed
    values: list[float] = []
    while len(values) < value_count:
        state = (multiplier * state) % modulus
        uniform_one = max(state / modulus, 1e-12)
        state = (multiplier * state) % modulus
        uniform_two = state / modulus
        magnitude = math.sqrt(-2 * math.log(uniform_one))
        values.append(magnitude * math.cos(2 * math.pi * uniform_two))
        if len(values) < value_count:
            values.append(magnitude * math.sin(2 * math.pi * uniform_two))
    return values


@dataclass
class ReferenceResult:
    discrete_a: Matrix
    discrete_b: Vector
    measurement_matrix: Matrix
    process_covariance: Matrix
    measurement_covariance: Matrix
    time: list[float]
    command: list[float]
    process_noise_shape: list[float]
    primary_noise_shape: list[float]
    backup_noise_shape: list[float]
    truth: list[Vector]
    prior: list[Vector]
    posterior: list[Vector]
    measurement: list[Vector]
    innovation: list[Vector]
    innovation_covariance: list[Matrix]
    gain: list[Matrix]
    prior_covariance: list[Matrix]
    posterior_covariance: list[Matrix]
    nis: list[float]
    error: list[Vector]
    position_rmse: float
    rate_rmse: float
    mean_tail_nis: float
    outlier_index: int


def reference_model(
    assumed_position_noise: float = 0.35,
    assumed_process_noise: float = 0.08,
    position_outlier: float = 0.0,
    seed: int = 1601,
    duration: float = 20.0,
    time_step: float = 0.05,
) -> ReferenceResult:
    step_count = round(duration / time_step)
    damping = 0.5
    decay = math.exp(-damping * time_step)
    position_from_rate = (1 - decay) / damping
    position_from_acceleration = (time_step - position_from_rate) / damping
    discrete_a = [[1.0, position_from_rate], [0.0, decay]]
    discrete_b = [position_from_acceleration, position_from_rate]
    measurement_matrix = [[1.0, 0.0], [1.0, 0.0]]
    process_covariance = [
        [value * assumed_process_noise**2 for value in row]
        for row in outer(discrete_b)
    ]
    measurement_covariance = [[assumed_position_noise**2, 0.0], [0.0, 0.8**2]]
    time = [index * time_step for index in range(step_count + 1)]
    command = [
        0.3 if 2 <= instant < 6 else (-0.2 if 10 <= instant < 14 else 0.0)
        for instant in time
    ]
    process_noise_shape = deterministic_normal(step_count, seed)
    primary_noise_shape = deterministic_normal(step_count + 1, seed + 1)
    backup_noise_shape = deterministic_normal(step_count + 1, seed + 2)
    outlier_index = round(12 / time_step)

    truth: list[Vector] = [[0.0, 0.0]]
    prior: list[Vector] = [[-0.8, 0.8]]
    posterior: list[Vector] = []
    measurement: list[Vector] = []
    innovation: list[Vector] = []
    innovation_covariance: list[Matrix] = []
    gain: list[Matrix] = []
    prior_covariance: list[Matrix] = [[[1.5**2, 0.0], [0.0, 0.8**2]]]
    posterior_covariance: list[Matrix] = []
    nis: list[float] = []
    identity = [[1.0, 0.0], [0.0, 1.0]]
    actual_process_std = 0.08

    for index in range(step_count + 1):
        measured = [
            truth[index][0]
            + 0.35 * primary_noise_shape[index]
            + (position_outlier if index == outlier_index else 0.0),
            truth[index][0] + 0.8 * backup_noise_shape[index],
        ]
        measurement.append(measured)
        predicted_measurement = matrix_vector(measurement_matrix, prior[index])
        residual = [measured[row] - predicted_measurement[row] for row in range(2)]
        innovation.append(residual)
        innovation_s = matrix_add(
            matrix_multiply(
                matrix_multiply(measurement_matrix, prior_covariance[index]),
                transpose(measurement_matrix),
            ),
            measurement_covariance,
        )
        innovation_covariance.append(innovation_s)
        innovation_inverse = inverse_two_by_two(innovation_s)
        update_gain = matrix_multiply(
            matrix_multiply(prior_covariance[index], transpose(measurement_matrix)),
            innovation_inverse,
        )
        gain.append(update_gain)
        correction = matrix_vector(update_gain, residual)
        updated = [prior[index][row] + correction[row] for row in range(2)]
        posterior.append(updated)
        covariance_correction = matrix_subtract(
            identity, matrix_multiply(update_gain, measurement_matrix)
        )
        updated_covariance = matrix_add(
            matrix_multiply(
                matrix_multiply(covariance_correction, prior_covariance[index]),
                transpose(covariance_correction),
            ),
            matrix_multiply(
                matrix_multiply(update_gain, measurement_covariance),
                transpose(update_gain),
            ),
        )
        posterior_covariance.append(updated_covariance)
        scaled_residual = matrix_vector(innovation_inverse, residual)
        nis.append(sum(residual[row] * scaled_residual[row] for row in range(2)))
        if index == step_count:
            continue
        true_prediction = matrix_vector(discrete_a, truth[index])
        actual_acceleration = command[index] + actual_process_std * process_noise_shape[index]
        truth.append(
            [
                true_prediction[row] + discrete_b[row] * actual_acceleration
                for row in range(2)
            ]
        )
        state_prediction = matrix_vector(discrete_a, updated)
        prior.append(
            [
                state_prediction[row] + discrete_b[row] * command[index]
                for row in range(2)
            ]
        )
        prior_covariance.append(
            matrix_add(
                matrix_multiply(
                    matrix_multiply(discrete_a, updated_covariance),
                    transpose(discrete_a),
                ),
                process_covariance,
            )
        )

    error = [
        [actual[row] - estimated[row] for row in range(2)]
        for actual, estimated in zip(truth, posterior)
    ]
    tail_indices = [index for index, instant in enumerate(time) if instant >= duration - 5]
    position_rmse = math.sqrt(
        sum(error[index][0] ** 2 for index in tail_indices) / len(tail_indices)
    )
    rate_rmse = math.sqrt(
        sum(error[index][1] ** 2 for index in tail_indices) / len(tail_indices)
    )
    mean_tail_nis = sum(nis[index] for index in tail_indices) / len(tail_indices)
    return ReferenceResult(
        discrete_a=discrete_a,
        discrete_b=discrete_b,
        measurement_matrix=measurement_matrix,
        process_covariance=process_covariance,
        measurement_covariance=measurement_covariance,
        time=time,
        command=command,
        process_noise_shape=process_noise_shape,
        primary_noise_shape=primary_noise_shape,
        backup_noise_shape=backup_noise_shape,
        truth=truth,
        prior=prior,
        posterior=posterior,
        measurement=measurement,
        innovation=innovation,
        innovation_covariance=innovation_covariance,
        gain=gain,
        prior_covariance=prior_covariance,
        posterior_covariance=posterior_covariance,
        nis=nis,
        error=error,
        position_rmse=position_rmse,
        rate_rmse=rate_rmse,
        mean_tail_nis=mean_tail_nis,
        outlier_index=outlier_index,
    )


class P16ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P16"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 16)
        self.assertEqual(self.module["title"], "Fuse Noisy Sensors with a Kalman Filter")
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["phase"], 4)
        self.assertEqual(self.module["phase_title"], "State-space control")
        self.assertEqual(
            self.module["folder"],
            "modules/16-fuse-noisy-sensors-with-a-kalman-filter",
        )
        self.assertEqual(self.module["prerequisites"], ["P15"])
        self.assertEqual(self.module["implementation_batch"], "P16")
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
            "decay = exp(-dampingPerSec*timeStepSec)",
            "discreteA = [1 positionFromRateSec;0 decay]",
            "measurementMatrix = [1 0;1 0]",
            "processCovariance = accelerationColumn*accelerationColumn.'* ...",
            "measurementCovariance = diag([assumedPositionNoiseStdM^2, ...",
            "innovation(:,k) = measurement(:,k)- ...",
            "kalmanGain(:,:,k) = priorCovariance(:,:,k)* ...",
            "posteriorEstimate(:,k) = priorEstimate(:,k)+ ...",
            "covarianceCorrection = identityState- ...",
            "normalizedInnovationSquared(k) = innovation(:,k).'* ...",
            "function values = deterministicNormal(valueCount,seed)",
            "modulus = 2147483647",
            "multiplier = 16807",
        ):
            self.assertIn(formula, model)
        for validation in (
            "maximumStepCount = 5000",
            "P16:PositionNoiseRange",
            "P16:ProcessNoiseRange",
            "P16:OutlierRange",
            "P16:SeedRange",
            "P16:DurationRange",
            "P16:DisplayResolution",
            "P16:GridAlignment",
            "P16:TooManySteps",
            "P16:InnovationCovariance",
        ):
            self.assertIn(validation, model)
        self.assertLess(
            model.index("stepCount > maximumStepCount"),
            model.index("processNoiseShape = deterministicNormal"),
        )
        self.assertNotRegex(
            model.lower(),
            r"\b(?:plot|figure|uifigure|uiaxes|uislider|uidropdown|rng|rand|randn|random)\s*\(",
        )
        self.assertNotRegex(
            model.lower(),
            r"\b(?:kalman|lqe|dlqe|ss|c2d|lsim|dare|idare|inv|pinv)\s*\(",
        )

    def test_independent_baseline_matrices_noise_and_metrics(self):
        result = reference_model()
        self.assertAlmostEqual(result.discrete_a[1][1], 0.9753099120283326)
        self.assertAlmostEqual(result.discrete_a[0][1], 0.04938017594333477)
        self.assertAlmostEqual(result.discrete_b[0], 0.001239648113330466)
        self.assertAlmostEqual(result.discrete_b[1], 0.04938017594333477)
        self.assertEqual(result.measurement_matrix, [[1.0, 0.0], [1.0, 0.0]])
        self.assertAlmostEqual(result.process_covariance[0][0], 9.835055647256216e-09)
        self.assertEqual(result.measurement_covariance, [[0.35**2, 0.0], [0.0, 0.8**2]])
        expected_noise = (
            [-2.4787634175430178, -1.6170925134602487],
            [-0.4898070815744558, -2.918577816474157],
            [1.814796402487107, -2.3373646304188185],
        )
        for actual, expected in zip(
            (
                result.process_noise_shape[:2],
                result.primary_noise_shape[:2],
                result.backup_noise_shape[:2],
            ),
            expected_noise,
        ):
            for actual_value, expected_value in zip(actual, expected):
                self.assertAlmostEqual(actual_value, expected_value)
        self.assertAlmostEqual(result.position_rmse, 0.07875913925071903)
        self.assertAlmostEqual(result.rate_rmse, 0.009304162796690399)
        self.assertAlmostEqual(result.mean_tail_nis, 1.772969285600885)
        raw_primary_tail = [
            result.measurement[index][0] - result.truth[index][0]
            for index, instant in enumerate(result.time)
            if instant >= 15
        ]
        raw_backup_tail = [
            result.measurement[index][1] - result.truth[index][0]
            for index, instant in enumerate(result.time)
            if instant >= 15
        ]
        primary_rmse = math.sqrt(sum(value**2 for value in raw_primary_tail) / len(raw_primary_tail))
        backup_rmse = math.sqrt(sum(value**2 for value in raw_backup_tail) / len(raw_backup_tail))
        self.assertLess(result.position_rmse, primary_rmse)
        self.assertLess(result.position_rmse, backup_rmse)

    def test_independent_predict_update_covariance_and_nis_recurrences(self):
        result = reference_model()
        identity = [[1.0, 0.0], [0.0, 1.0]]
        for index in range(len(result.time)):
            predicted_measurement = matrix_vector(result.measurement_matrix, result.prior[index])
            expected_innovation = [
                result.measurement[index][row] - predicted_measurement[row]
                for row in range(2)
            ]
            expected_s = matrix_add(
                matrix_multiply(
                    matrix_multiply(result.measurement_matrix, result.prior_covariance[index]),
                    transpose(result.measurement_matrix),
                ),
                result.measurement_covariance,
            )
            inverse_s = inverse_two_by_two(expected_s)
            expected_gain = matrix_multiply(
                matrix_multiply(
                    result.prior_covariance[index], transpose(result.measurement_matrix)
                ),
                inverse_s,
            )
            expected_posterior = [
                result.prior[index][row]
                + matrix_vector(expected_gain, expected_innovation)[row]
                for row in range(2)
            ]
            correction = matrix_subtract(
                identity, matrix_multiply(expected_gain, result.measurement_matrix)
            )
            expected_covariance = matrix_add(
                matrix_multiply(
                    matrix_multiply(correction, result.prior_covariance[index]),
                    transpose(correction),
                ),
                matrix_multiply(
                    matrix_multiply(expected_gain, result.measurement_covariance),
                    transpose(expected_gain),
                ),
            )
            for actual, expected in zip(result.innovation[index], expected_innovation):
                self.assertAlmostEqual(actual, expected)
            for actual_row, expected_row in zip(result.gain[index], expected_gain):
                for actual, expected in zip(actual_row, expected_row):
                    self.assertAlmostEqual(actual, expected)
            for actual, expected in zip(result.posterior[index], expected_posterior):
                self.assertAlmostEqual(actual, expected)
            covariance = result.posterior_covariance[index]
            self.assertAlmostEqual(covariance[0][1], covariance[1][0], places=14)
            determinant = covariance[0][0] * covariance[1][1] - covariance[0][1] ** 2
            self.assertGreater(covariance[0][0], 0)
            self.assertGreater(covariance[1][1], 0)
            self.assertGreater(determinant, 0)
            for actual_row, expected_row in zip(covariance, expected_covariance):
                for actual, expected in zip(actual_row, expected_row):
                    self.assertAlmostEqual(actual, expected)
            scaled = matrix_vector(inverse_s, expected_innovation)
            self.assertAlmostEqual(
                result.nis[index],
                sum(expected_innovation[row] * scaled[row] for row in range(2)),
            )
            if index == len(result.time) - 1:
                continue
            expected_true = matrix_vector(result.discrete_a, result.truth[index])
            expected_prior = matrix_vector(result.discrete_a, result.posterior[index])
            actual_acceleration = result.command[index] + 0.08 * result.process_noise_shape[index]
            for row in range(2):
                self.assertAlmostEqual(
                    result.truth[index + 1][row],
                    expected_true[row] + result.discrete_b[row] * actual_acceleration,
                )
                self.assertAlmostEqual(
                    result.prior[index + 1][row],
                    expected_prior[row] + result.discrete_b[row] * result.command[index],
                )
            expected_prior_covariance = matrix_add(
                matrix_multiply(
                    matrix_multiply(result.discrete_a, covariance),
                    transpose(result.discrete_a),
                ),
                result.process_covariance,
            )
            for actual_row, expected_row in zip(
                result.prior_covariance[index + 1], expected_prior_covariance
            ):
                for actual, expected in zip(actual_row, expected_row):
                    self.assertAlmostEqual(actual, expected)

    def test_two_sweeps_are_independent_with_expected_trust_limits(self):
        sensor_stds = [0.1, 0.2, 0.35, 0.6, 0.9]
        sensor_runs = [reference_model(assumed_position_noise=value) for value in sensor_stds]
        primary_gains = [run.gain[-1][0][0] for run in sensor_runs]
        backup_gains = [run.gain[-1][0][1] for run in sensor_runs]
        mean_nis = [run.mean_tail_nis for run in sensor_runs]
        self.assertEqual(primary_gains, sorted(primary_gains, reverse=True))
        self.assertEqual(backup_gains, sorted(backup_gains))
        self.assertEqual(mean_nis, sorted(mean_nis, reverse=True))
        for run in sensor_runs[1:]:
            self.assertEqual(run.truth, sensor_runs[0].truth)
            self.assertEqual(run.measurement, sensor_runs[0].measurement)
            self.assertEqual(run.process_noise_shape, sensor_runs[0].process_noise_shape)

        process_stds = [0.01, 0.04, 0.08, 0.2, 0.5]
        process_runs = [reference_model(assumed_process_noise=value) for value in process_stds]
        rate_gains = [run.gain[-1][1][0] for run in process_runs]
        rate_stds = [math.sqrt(run.posterior_covariance[-1][1][1]) for run in process_runs]
        self.assertEqual(rate_gains, sorted(rate_gains))
        self.assertEqual(rate_stds, sorted(rate_stds))
        for run in process_runs[1:]:
            self.assertEqual(run.truth, process_runs[0].truth)
            self.assertEqual(run.measurement, process_runs[0].measurement)
            self.assertEqual(run.primary_noise_shape, process_runs[0].primary_noise_shape)

    def test_equal_reported_sensor_noise_has_exact_gain_symmetry_limit(self):
        equal_sensors = reference_model(assumed_position_noise=0.8)
        self.assertEqual(
            equal_sensors.measurement_covariance[0][0],
            equal_sensors.measurement_covariance[1][1],
        )
        for gain in equal_sensors.gain:
            self.assertAlmostEqual(gain[0][0], gain[0][1], places=14)
            self.assertAlmostEqual(gain[1][0], gain[1][1], places=14)

    def test_batch_fusion_matches_sequential_updates_in_either_order(self):
        result = reference_model()
        for index in range(len(result.time)):
            for order in ((0, 1), (1, 0)):
                estimate, covariance = sequential_sensor_update(
                    result.prior[index],
                    result.prior_covariance[index],
                    result.measurement[index],
                    result.measurement_covariance,
                    order,
                )
                for actual, expected in zip(estimate, result.posterior[index]):
                    self.assertAlmostEqual(actual, expected, places=13)
                for actual_row, expected_row in zip(
                    covariance, result.posterior_covariance[index]
                ):
                    for actual, expected in zip(actual_row, expected_row):
                        self.assertAlmostEqual(actual, expected, places=13)

    def test_broken_case_recovery_and_seed_isolation(self):
        clean = reference_model()
        broken = reference_model(position_outlier=4.0)
        changed_measurements = [
            index
            for index, (good, bad) in enumerate(zip(clean.measurement, broken.measurement))
            if good != bad
        ]
        self.assertEqual(changed_measurements, [clean.outlier_index])
        self.assertEqual(clean.truth, broken.truth)
        self.assertEqual(clean.gain, broken.gain)
        self.assertEqual(clean.posterior_covariance, broken.posterior_covariance)
        self.assertAlmostEqual(
            broken.measurement[broken.outlier_index][0]
            - clean.measurement[clean.outlier_index][0],
            4.0,
        )
        expected_kick = [clean.gain[clean.outlier_index][row][0] * 4 for row in range(2)]
        for row in range(2):
            self.assertAlmostEqual(
                broken.posterior[broken.outlier_index][row]
                - clean.posterior[clean.outlier_index][row],
                expected_kick[row],
            )
        self.assertGreater(broken.nis[broken.outlier_index], 90)
        self.assertLess(clean.nis[clean.outlier_index], 10)
        self.assertEqual(reference_model(), clean)

        alternate = reference_model(seed=1701)
        self.assertNotEqual(alternate.measurement, clean.measurement)
        self.assertNotEqual(alternate.truth, clean.truth)
        self.assertEqual(alternate.gain, clean.gain)
        self.assertEqual(alternate.posterior_covariance, clean.posterior_covariance)

    def test_independent_maximum_accepted_grid_is_finite(self):
        bounded = reference_model(duration=30.0, time_step=0.006)
        self.assertEqual(len(bounded.time), 5001)
        self.assertEqual(len(bounded.truth), 5001)
        self.assertEqual(len(bounded.posterior), 5001)
        for collection in (bounded.truth, bounded.posterior):
            self.assertTrue(all(math.isfinite(value) for state in collection for value in state))
        self.assertTrue(all(math.isfinite(value) for value in bounded.nis))

    def test_experiment_has_ordered_flow_labels_metrics_sweeps_and_broken_case(self):
        experiment = self.read("experiment.m")
        section_titles = re.findall(r"^%% (.+)$", experiment, flags=re.MULTILINE)
        self.assertGreaterEqual(len(section_titles), 11)
        flow_markers = (
            "%% Read -",
            "%% Visualize baseline",
            "%% Changed view",
            "%% Sweep 1",
            "%% Read and explain sweep 1",
            "%% Sweep 2",
            "%% Read and explain sweep 2",
            "%% Broken case",
            "%% Read and explain the broken mechanism",
            "%% Check and teach back",
        )
        for marker in flow_markers:
            self.assertIn(marker, experiment)
        for earlier, later in zip(flow_markers, flow_markers[1:]):
            self.assertLess(experiment.index(earlier), experiment.index(later))
        for marker in (
            "assumedPositionNoiseStdValuesM = [0.1 0.2 0.35 0.6 0.9]",
            "assumedProcessNoiseStdValuesMPerSec2 = [0.01 0.04 0.08 0.2 0.5]",
            "broken = model(0.35,0.08,4,1601,20,0.05)",
            "recovered = model(0.35,0.08,0,1601,20,0.05)",
            "tail position RMSE",
            "mean tail NIS",
        ):
            self.assertIn(marker, experiment)
        for unit in (
            "Time (s)",
            "Position (m)",
            "Rate (m/s)",
            "Assumed sensor A noise standard deviation (m)",
            "Assumed process acceleration standard deviation (m/s^2)",
            "Rate gain from sensor A (1/s)",
            "Normalized innovation squared",
        ):
            self.assertIn(unit, experiment)
        self.assertIn("clear run_checks;", experiment)
        self.assertIn("\nrun_checks;\n", experiment)
        self.assertLess(
            experiment.index("clear run_checks;"), experiment.index("\nrun_checks;\n")
        )

    def test_interactive_has_meaningful_controls_reset_and_feedback(self):
        interactive = self.read("interactive.m")
        for marker in (
            "uifigure(",
            "uiaxes(",
            "uislider(",
            "uispinner(",
            "uidropdown(",
            "Assumed sensor A noise std (m)",
            "Assumed acceleration noise std (m/s^2)",
            "+4 m sensor A outlier (broken)",
            "ValueChangingFcn",
            "ValueChangedFcn",
            "ButtonPushedFcn",
            "resetBaseline",
            "redraw(0.35,0.08,'No outlier')",
            "result = modelFunction(positionNoiseStdM, ...",
            "outlier exceeds the covariance model",
            "reported sensor noise is overconfident",
        ):
            self.assertIn(marker, interactive)

    def test_checks_cover_invariants_malformed_recovery_isolation_and_bounds(self):
        checks = self.read("run_checks.m")
        for marker in (
            "isequaln(baselineA,baselineB)",
            "expectedA = [1 expectedPositionFromRate;0 expectedDecay]",
            "expectedQ = expectedB*expectedB.'*0.08^2",
            "expectedSInverse = [expectedS(2,2) -expectedS(1,2); ...",
            "expectedGain = baselineA.priorCovariance(:,:,k)*expectedC.'* ...",
            "expectedPosteriorCovariance = covarianceCorrection* ...",
            "expectedNis = expectedInnovation.'*expectedSInverse*expectedInnovation",
            "sequentialSensorUpdate(baselineA.priorEstimate(:,k), ...",
            "expectedMeasurement,expectedR,[1 2]",
            "expectedMeasurement,expectedR,[2 1]",
            "assumedPositionNoiseStdValuesM = [0.1 0.2 0.35 0.6 0.9]",
            "equalReportedSensors = model(0.8,0.08,0,1601,20,0.05)",
            "equalGainDifference = equalReportedSensors.kalmanGain(:,1,:)- ...",
            "assumedProcessNoiseStdValuesMPerSec2 = [0.01 0.04 0.08 0.2 0.5]",
            "broken = model(0.35,0.08,4,1601,20,0.05)",
            "recovered = model(0.35,0.08,0,1601,20,0.05)",
            "alternateSeed = model(0.35,0.08,0,1701,20,0.05)",
            "P16:PositionNoiseRange",
            "P16:ProcessNoiseRange",
            "P16:OutlierRange",
            "P16:SeedRange",
            "P16:DurationRange",
            "P16:DisplayResolution",
            "P16:GridAlignment",
            "P16:TooManySteps",
            "boundedGrid = model(0.35,0.08,0,1601,30,0.006)",
            "assertAnyError",
            "assertErrorId",
        ):
            self.assertIn(marker, checks)

    def test_tutor_text_connects_p15_and_keeps_claim_boundary(self):
        readme = self.read("README.md")
        lesson = self.read("lesson.md")
        walkthrough = self.read("walkthrough.md")
        checks = self.read("checks.md")
        combined = "\n".join((readme, lesson, walkthrough, checks))
        for marker in (
            QUESTION,
            "P15",
            "innovation",
            "covariance",
            "Q",
            "R",
            "two noisy position sensors",
            "outlier",
            "two sentences",
            "MATLAB-runtime",
            "No MATLAB-runtime",
        ):
            self.assertIn(marker.lower(), combined.lower())
        opaque_calls = (
            r"\b(?:kalman|lqe|dlqe|ss|c2d|lsim|dare|idare|inv|pinv|rng|rand|randn)\s*\("
        )
        for name in ("model.m", "experiment.m", "interactive.m", "run_checks.m", "lesson.m"):
            self.assertNotRegex(self.read(name).lower(), opaque_calls)
        for placeholder in ("scaffolded", "placeholder", "todo"):
            self.assertNotIn(placeholder, combined.lower())

    def test_readme_scopes_the_interactive_module_path(self):
        readme = self.read("README.md")
        add_path = 'addpath(moduleFolder,"-begin");'
        clear_functions = "clear model interactive;"
        remove_path = "rmpath(moduleFolder);"
        clear_path = "clear moduleFolder"
        self.assertIn(
            'moduleFolder = fullfile(pwd,"modules","16-fuse-noisy-sensors-with-a-kalman-filter");',
            readme,
        )
        self.assertIn(add_path, readme)
        self.assertIn(clear_functions, readme)
        self.assertEqual(readme.count(remove_path), 2)
        self.assertIn("catch exception", readme)
        self.assertIn("rethrow(exception)", readme)
        self.assertIn(clear_path, readme)
        interactive_call = "\n    interactive\n"
        self.assertLess(readme.index(add_path), readme.index(clear_functions))
        self.assertLess(readme.index(clear_functions), readme.index(interactive_call))
        self.assertLess(readme.index(add_path), readme.index(interactive_call))
        self.assertLess(readme.index(interactive_call), readme.rindex(remove_path))
        self.assertLess(readme.rindex(remove_path), readme.index(clear_path))

    def test_public_check_route_preserves_existing_learner_progress(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            shutil.copytree(ROOT / "bin", fixture / "bin")
            shutil.copytree(ROOT / "curriculum", fixture / "curriculum")
            shutil.copytree(self.folder, fixture / self.module["folder"])
            progress_file = fixture / ".learning/progress.json"
            progress_file.parent.mkdir(parents=True)
            retained_progress = (
                b'{\n  "current": "P15",\n  "completed": {"P14": true},\n'
                b'  "notes": {"P14": "retain this note"}\n}\n'
            )
            progress_file.write_bytes(retained_progress)
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            checked = subprocess.run(
                [str(fixture / "bin/learn"), "check", "P16"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(checked.stderr, "")
            self.assertEqual(checked.stdout, "Run in MATLAB: run_module_checks('P16')\n")
            self.assertEqual(progress_file.read_bytes(), retained_progress)

    def test_public_start_continue_and_state_isolation(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            shutil.copytree(ROOT / "bin", fixture / "bin")
            shutil.copytree(ROOT / "curriculum", fixture / "curriculum")
            shutil.copytree(self.folder, fixture / self.module["folder"])
            progress_file = fixture / ".learning/progress.json"
            progress_file.parent.mkdir(parents=True)
            original = {
                "current": "P15",
                "completed": {"P14": True},
                "notes": {"P14": "retain this note"},
            }
            progress_file.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            started = subprocess.run(
                [str(fixture / "bin/learn"), "start", "P16"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertEqual(started.stderr, "")
            for expected in (
                "P16 — Fuse Noisy Sensors with a Kalman Filter",
                "Status: implemented",
                f"Guiding question: {QUESTION}",
                "Folder: modules/16-fuse-noisy-sensors-with-a-kalman-filter",
                "launch_lesson('P16')",
                "modules/16-fuse-noisy-sensors-with-a-kalman-filter/checks.md",
            ):
                self.assertIn(expected, started.stdout)
            retained = json.loads(progress_file.read_text(encoding="utf-8"))
            self.assertEqual(retained["current"], "P16")
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


if __name__ == "__main__":
    unittest.main()
