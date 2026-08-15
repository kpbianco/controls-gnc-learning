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
    "What inputs, observable effects, and failure modes matter when you balance "
    "State Error and Control Effort with LQR?"
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


def outer(left: Vector, right: Vector) -> Matrix:
    return [[left_value * right_value for right_value in right] for left_value in left]


def maximum_matrix_delta(left: Matrix, right: Matrix) -> float:
    return max(
        abs(left[row][column] - right[row][column])
        for row in range(len(left))
        for column in range(len(left[0]))
    )


def characteristic_poles(matrix: Matrix) -> tuple[complex, complex]:
    trace = matrix[0][0] + matrix[1][1]
    determinant = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    root = complex(trace * trace - 4 * determinant, 0) ** 0.5
    return ((trace + root) / 2, (trace - root) / 2)


@dataclass
class ReferenceResult:
    discrete_a: Matrix
    discrete_b: Vector
    q: Matrix
    r: float
    p: Matrix
    gain: Vector
    iterations: int
    nominal_poles: tuple[complex, complex]
    actual_poles: tuple[complex, complex]
    time: list[float]
    state: list[Vector]
    commanded: list[float]
    applied: list[float]
    position_ise: float
    rate_ise: float
    effort_integral: float
    running_cost: float
    terminal_cost: float
    initial_value: float
    settling_time: float


def reference_model(
    position_weight: float = 4.0,
    effort_weight: float = 1.0,
    effectiveness: float = 1.0,
    initial_position: float = 1.0,
    duration: float = 12.0,
    time_step: float = 0.02,
) -> ReferenceResult:
    damping = 0.5
    decay = math.exp(-damping * time_step)
    position_from_rate = (1 - decay) / damping
    position_from_acceleration = (time_step - position_from_rate) / damping
    discrete_a = [[1.0, position_from_rate], [0.0, decay]]
    discrete_b = [position_from_acceleration, position_from_rate]
    q = [[position_weight, 0.0], [0.0, 1.0]]
    p = [row[:] for row in q]

    for iterations in range(1, 40_001):
        p_b = matrix_vector(p, discrete_b)
        control_curvature = effort_weight + sum(
            discrete_b[index] * p_b[index] for index in range(2)
        )
        p_a = matrix_multiply(p, discrete_a)
        b_transpose_p_a = [
            sum(discrete_b[index] * p_a[index][column] for index in range(2))
            for column in range(2)
        ]
        gain = [value / control_curvature for value in b_transpose_p_a]
        a_transpose_p_a = matrix_multiply(transpose(discrete_a), p_a)
        a_transpose_p_b = matrix_vector(transpose(discrete_a), p_b)
        next_p = matrix_add(
            q,
            matrix_subtract(a_transpose_p_a, outer(a_transpose_p_b, gain)),
        )
        next_p = [
            [(next_p[row][column] + next_p[column][row]) / 2 for column in range(2)]
            for row in range(2)
        ]
        delta = maximum_matrix_delta(next_p, p)
        scale = max(1.0, *(abs(value) for row in next_p for value in row))
        p = next_p
        if delta <= 1e-12 * scale:
            break
    else:
        raise AssertionError("reference Riccati iteration did not converge")

    p_b = matrix_vector(p, discrete_b)
    control_curvature = effort_weight + sum(
        discrete_b[index] * p_b[index] for index in range(2)
    )
    p_a = matrix_multiply(p, discrete_a)
    gain = [
        sum(discrete_b[index] * p_a[index][column] for index in range(2))
        / control_curvature
        for column in range(2)
    ]
    nominal_closed_loop = matrix_subtract(discrete_a, outer(discrete_b, gain))
    actual_closed_loop = matrix_subtract(
        discrete_a, outer([effectiveness * value for value in discrete_b], gain)
    )

    step_count = round(duration / time_step)
    time = [index * time_step for index in range(step_count + 1)]
    state: list[Vector] = [[initial_position, 0.0]]
    commanded: list[float] = []
    applied: list[float] = []
    for index in range(step_count + 1):
        command = -sum(gain[row] * state[index][row] for row in range(2))
        commanded.append(command)
        applied.append(effectiveness * command)
        if index < step_count:
            prediction = matrix_vector(discrete_a, state[index])
            state.append(
                [prediction[row] + discrete_b[row] * applied[-1] for row in range(2)]
            )

    position_ise = time_step * sum(value[0] ** 2 for value in state[:-1])
    rate_ise = time_step * sum(value[1] ** 2 for value in state[:-1])
    effort_integral = time_step * sum(value**2 for value in commanded[:-1])
    running_cost = position_weight * position_ise + rate_ise + effort_weight * effort_integral
    terminal_cost = time_step * sum(
        state[-1][row] * matrix_vector(p, state[-1])[row] for row in range(2)
    )
    initial_value = time_step * sum(
        state[0][row] * matrix_vector(p, state[0])[row] for row in range(2)
    )
    position_tolerance = 0.02 * abs(initial_position)
    outside = [
        abs(value[0]) > position_tolerance or abs(value[1]) > 0.02 for value in state
    ]
    if any(outside):
        last_outside = len(outside) - 1 - outside[::-1].index(True)
        settling_time = math.inf if last_outside == step_count else time[last_outside + 1]
    else:
        settling_time = 0.0
    return ReferenceResult(
        discrete_a=discrete_a,
        discrete_b=discrete_b,
        q=q,
        r=effort_weight,
        p=p,
        gain=gain,
        iterations=iterations,
        nominal_poles=characteristic_poles(nominal_closed_loop),
        actual_poles=characteristic_poles(actual_closed_loop),
        time=time,
        state=state,
        commanded=commanded,
        applied=applied,
        position_ise=position_ise,
        rate_ise=rate_ise,
        effort_integral=effort_integral,
        running_cost=running_cost,
        terminal_cost=terminal_cost,
        initial_value=initial_value,
        settling_time=settling_time,
    )


def retained_cost_for_gain(result: ReferenceResult, gain: Vector) -> float:
    """Evaluate one fixed feedback gain on the retained plant and horizon."""
    time_step = result.time[1] - result.time[0]
    state = result.state[0][:]
    running_cost = 0.0
    for _ in range(len(result.time) - 1):
        command = -sum(gain[index] * state[index] for index in range(2))
        q_state = matrix_vector(result.q, state)
        running_cost += time_step * (
            sum(state[index] * q_state[index] for index in range(2))
            + result.r * command**2
        )
        prediction = matrix_vector(result.discrete_a, state)
        state = [
            prediction[index] + result.discrete_b[index] * command
            for index in range(2)
        ]
    terminal_state = matrix_vector(result.p, state)
    terminal_cost = time_step * sum(
        state[index] * terminal_state[index] for index in range(2)
    )
    return running_cost + terminal_cost


class P17ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P17"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 17)
        self.assertEqual(
            self.module["title"], "Balance State Error and Control Effort with LQR"
        )
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["phase"], 5)
        self.assertEqual(self.module["phase_title"], "Optimal and robust control")
        self.assertEqual(
            self.module["folder"],
            "modules/17-balance-state-error-and-control-effort-with-lqr",
        )
        self.assertEqual(self.module["prerequisites"], ["P16"])
        self.assertEqual(self.module["implementation_batch"], "P17")
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
            "discreteA = [1 positionFromRateSec;0 decay]",
            "stateCost = diag([positionErrorWeight/positionScaleM^2, ...",
            "controlCurvature = inputCost+ ...",
            "trialGain = (discreteB.'*riccatiMatrix*discreteA)/ ...",
            "nextRiccatiMatrix = stateCost+ ...",
            "feedbackGain = (discreteB.'*riccatiMatrix*discreteA)/controlCurvature",
            "actualClosedLoopA = discreteA-actuatorEffectiveness*discreteB*feedbackGain",
            "commandedAccelerationMPerSec2(k) = -feedbackGain*state(:,k)",
            "state(:,k+1) = discreteA*state(:,k)+ ...",
            "normalizedCostWithTerminalSec",
            "normalizedInitialValueSec",
        ):
            self.assertIn(formula, model)
        for validation in (
            "maximumStepCount = 5000",
            "maximumRiccatiIterations = 40000",
            "P17:PositionWeightRange",
            "P17:EffortWeightRange",
            "P17:ActuatorEffectivenessRange",
            "P17:InitialPositionRange",
            "P17:DurationRange",
            "P17:DisplayResolution",
            "P17:GridAlignment",
            "P17:TooManySteps",
            "P17:RiccatiConvergence",
        ):
            self.assertIn(validation, model)
        self.assertLess(model.index("stepCount > maximumStepCount"), model.index("state = zeros"))
        self.assertNotRegex(
            model.lower(),
            r"\b(?:plot|figure|uifigure|uiaxes|uislider|uidropdown|rng|rand|randn)\s*\(",
        )
        self.assertNotRegex(
            model.lower(),
            r"\b(?:lqr|dlqr|dare|idare|ss|c2d|lsim|inv|pinv)\s*\(",
        )

    def test_independent_baseline_gain_poles_metrics_and_bellman_identity(self):
        result = reference_model()
        self.assertAlmostEqual(result.discrete_a[1][1], 0.9900498337491681)
        self.assertAlmostEqual(result.discrete_a[0][1], 0.019900332501663787)
        self.assertAlmostEqual(result.discrete_b[0], 0.00019933499667242678)
        self.assertAlmostEqual(result.discrete_b[1], 0.019900332501663787)
        self.assertAlmostEqual(result.gain[0], 1.9644942427723904, places=10)
        self.assertAlmostEqual(result.gain[1], 1.7703588392280174, places=10)
        self.assertEqual(result.iterations, 563)
        expected_poles = (
            complex(0.9772137558777167, 0.016207061812201457),
            complex(0.9772137558777167, -0.016207061812201457),
        )
        for actual, expected in zip(result.nominal_poles, expected_poles):
            self.assertAlmostEqual(actual.real, expected.real)
            self.assertAlmostEqual(abs(actual.imag), abs(expected.imag))
        self.assertLess(max(abs(value) for value in result.nominal_poles), 1)
        self.assertAlmostEqual(result.position_ise, 0.8011009435616349)
        self.assertAlmostEqual(result.effort_integral, 0.9818849175073874)
        self.assertAlmostEqual(result.settling_time, 3.34)
        self.assertAlmostEqual(
            result.running_cost + result.terminal_cost, result.initial_value, places=9
        )

    def test_independent_riccati_and_state_recurrences(self):
        result = reference_model()
        p_b = matrix_vector(result.p, result.discrete_b)
        curvature = result.r + sum(
            result.discrete_b[index] * p_b[index] for index in range(2)
        )
        self.assertGreater(curvature, 0)
        p_a = matrix_multiply(result.p, result.discrete_a)
        expected_gain = [
            sum(result.discrete_b[index] * p_a[index][column] for index in range(2))
            / curvature
            for column in range(2)
        ]
        for actual, expected in zip(result.gain, expected_gain):
            self.assertAlmostEqual(actual, expected)
        a_transpose_p_a = matrix_multiply(transpose(result.discrete_a), p_a)
        a_transpose_p_b = matrix_vector(transpose(result.discrete_a), p_b)
        right = matrix_add(
            result.q,
            matrix_subtract(a_transpose_p_a, outer(a_transpose_p_b, result.gain)),
        )
        self.assertLess(maximum_matrix_delta(result.p, right), 2e-8)
        self.assertAlmostEqual(result.p[0][1], result.p[1][0])
        self.assertGreaterEqual(result.p[0][0], 0)
        self.assertGreaterEqual(result.p[1][1], 0)
        self.assertGreaterEqual(result.p[0][0] * result.p[1][1] - result.p[0][1] ** 2, 0)

        for index in range(len(result.time) - 1):
            expected_command = -sum(
                result.gain[row] * result.state[index][row] for row in range(2)
            )
            self.assertAlmostEqual(result.commanded[index], expected_command)
            predicted = matrix_vector(result.discrete_a, result.state[index])
            for row in range(2):
                self.assertAlmostEqual(
                    result.state[index + 1][row],
                    predicted[row] + result.discrete_b[row] * result.applied[index],
                )

    def test_lqr_gain_beats_perturbed_feedback_on_retained_cost(self):
        result = reference_model()
        optimal_cost = retained_cost_for_gain(result, result.gain)
        self.assertAlmostEqual(optimal_cost, result.initial_value, places=9)

        perturbations = ([0.2, 0.0], [-0.2, 0.0], [0.0, 0.2], [0.0, -0.2])
        for perturbation in perturbations:
            with self.subTest(perturbation=perturbation):
                candidate_gain = [
                    result.gain[index] + perturbation[index] for index in range(2)
                ]
                candidate_cost = retained_cost_for_gain(result, candidate_gain)
                self.assertGreater(candidate_cost, optimal_cost + 0.01)

    def test_two_sweeps_are_independent_with_expected_tradeoffs(self):
        position_weights = [0.0, 0.25, 1.0, 4.0, 16.0]
        position_runs = [reference_model(position_weight=value) for value in position_weights]
        gains = [run.gain[0] for run in position_runs]
        position_ise = [run.position_ise for run in position_runs]
        effort = [run.effort_integral for run in position_runs]
        self.assertEqual(gains, sorted(gains))
        self.assertEqual(position_ise, sorted(position_ise, reverse=True))
        self.assertEqual(effort, sorted(effort))
        for run in position_runs:
            self.assertEqual(run.discrete_a, position_runs[0].discrete_a)
            self.assertEqual(run.discrete_b, position_runs[0].discrete_b)
            self.assertEqual(run.r, 1.0)

        effort_weights = [0.1, 0.25, 1.0, 4.0, 10.0]
        effort_runs = [reference_model(effort_weight=value) for value in effort_weights]
        peaks = [max(abs(value) for value in run.commanded) for run in effort_runs]
        settling = [run.settling_time for run in effort_runs]
        effort_integrals = [run.effort_integral for run in effort_runs]
        self.assertEqual(peaks, sorted(peaks, reverse=True))
        self.assertEqual(settling, sorted(settling))
        self.assertEqual(effort_integrals, sorted(effort_integrals, reverse=True))
        for run in effort_runs:
            self.assertEqual(run.q, [[4.0, 0.0], [0.0, 1.0]])
            self.assertEqual(run.discrete_a, effort_runs[0].discrete_a)

    def test_zero_weight_broken_case_recovery_and_sign_isolation(self):
        zero_weight = reference_model(position_weight=0.0)
        self.assertEqual(zero_weight.gain[0], 0.0)
        self.assertTrue(all(state == [1.0, 0.0] for state in zero_weight.state))
        self.assertTrue(all(command == 0.0 for command in zero_weight.commanded))
        self.assertAlmostEqual(max(abs(pole) for pole in zero_weight.nominal_poles), 1.0)
        self.assertTrue(math.isinf(zero_weight.settling_time))

        baseline = reference_model()
        broken = reference_model(effectiveness=0.0)
        self.assertEqual(broken.gain, baseline.gain)
        self.assertEqual(broken.p, baseline.p)
        self.assertEqual(broken.nominal_poles, baseline.nominal_poles)
        self.assertTrue(all(state == [1.0, 0.0] for state in broken.state))
        self.assertTrue(all(value == 0.0 for value in broken.applied))
        self.assertGreater(broken.effort_integral, 40)
        self.assertAlmostEqual(max(abs(pole) for pole in broken.actual_poles), 1.0)
        self.assertTrue(math.isinf(broken.settling_time))
        self.assertEqual(reference_model(effectiveness=1.0), baseline)

        negative = reference_model(initial_position=-1.0)
        for positive_state, negative_state in zip(baseline.state, negative.state):
            for positive, opposite in zip(positive_state, negative_state):
                self.assertAlmostEqual(positive, -opposite)
        self.assertEqual(baseline.position_ise, negative.position_ise)
        self.assertEqual(baseline.effort_integral, negative.effort_integral)

    def test_zero_equilibrium_and_maximum_grid_are_finite(self):
        equilibrium = reference_model(initial_position=0.0)
        self.assertTrue(all(state == [0.0, 0.0] for state in equilibrium.state))
        self.assertEqual(equilibrium.settling_time, 0.0)
        bounded = reference_model(duration=20.0, time_step=0.004)
        self.assertEqual(len(bounded.time), 5001)
        self.assertLess(bounded.iterations, 40_000)
        self.assertTrue(
            all(math.isfinite(value) for state in bounded.state for value in state)
        )
        self.assertTrue(all(math.isfinite(value) for value in bounded.commanded))

    def test_worst_accepted_riccati_case_converges_within_fixed_bound(self):
        worst = reference_model(
            position_weight=0.25,
            effort_weight=20.0,
            duration=8.0,
            time_step=0.0016,
        )
        self.assertEqual(len(worst.time), 5001)
        self.assertGreater(worst.iterations, 30_000)
        self.assertLess(worst.iterations, 40_000)
        self.assertLess(max(abs(value) for value in worst.nominal_poles), 1)

    def test_experiment_has_ordered_flow_labels_metrics_sweeps_and_broken_case(self):
        experiment = self.read("experiment.m")
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
            "J = dt*sum(q_p*(p/1 m)^2",
            "common positive dt gives J seconds",
            "positionErrorWeightValues = [0 0.25 1 4 16]",
            "controlEffortWeightValues = [0.1 0.25 1 4 10]",
            "broken = model(4,1,0,1,12,0.02)",
            "recovered = model(4,1,1,1,12,0.02)",
            "position ISE",
            "effort integral",
            "clear run_checks;",
            "\nrun_checks;\n",
        ):
            self.assertIn(marker, experiment)
        for unit in (
            "Time (s)",
            "Position error (m)",
            "Rate error (m/s)",
            "Acceleration (m/s^2)",
            "Position feedback gain (1/s^2)",
            "Position integral squared error (m^2 s)",
            "Squared-command effort integral (m^2/s^3)",
        ):
            self.assertIn(unit, experiment)

    def test_interactive_has_meaningful_controls_reset_and_feedback(self):
        interactive = self.read("interactive.m")
        for marker in (
            "uifigure(",
            "uiaxes(",
            "uislider(",
            "uispinner(",
            "uidropdown(",
            "Position-error weight q_p",
            "Control-effort weight r",
            "Disconnected actuator (broken)",
            "ValueChangingFcn",
            "ValueChangedFcn",
            "ButtonPushedFcn",
            "resetBaseline",
            "redraw(4,1,'Full actuator authority')",
            "result = modelFunction(positionWeight,effortWeight, ...",
            "broken: requested effort has no authority",
            "limit: unpriced position offset persists",
            "Kp %.2f 1/s^2, Kv %.2f 1/s",
        ):
            self.assertIn(marker, interactive)

    def test_checks_cover_invariants_limits_malformed_recovery_and_bounds(self):
        checks = self.read("run_checks.m")
        for marker in (
            "isequaln(baselineA,baselineB)",
            "expectedA = [1 expectedPositionFromRate;0 expectedDecay]",
            "expectedGain = (expectedB.'*P*expectedA)/expectedControlCurvature",
            "expectedRiccatiRight = expectedQ+expectedA.'*P*expectedA- ...",
            "normalizedCostWithTerminalSec",
            "costDerivative",
            "gainPerturbations = [0.2 0;-0.2 0;0 0.2;0 -0.2]",
            "perturbedCostValues",
            "riccatiDeterminant",
            "positionErrorWeightValues = [0 0.25 1 4 16]",
            "zeroPositionWeight = positionRuns{1}",
            "controlEffortWeightValues = [0.1 0.25 1 4 10]",
            "broken = model(4,1,0,1,12,0.02)",
            "recovered = model(4,1,1,1,12,0.02)",
            "negativeInitialState = model(4,1,1,-1,12,0.02)",
            "P17:PositionWeightRange",
            "P17:EffortWeightRange",
            "P17:ActuatorEffectivenessRange",
            "P17:InitialPositionRange",
            "P17:DurationRange",
            "P17:DisplayResolution",
            "P17:GridAlignment",
            "P17:TooManySteps",
            "boundedGrid = model(4,1,1,1,20,0.004)",
            "worstRiccati = model(0.25,20,1,1,8,0.0016)",
            "assertAnyError",
            "assertErrorId",
        ):
            self.assertIn(marker, checks)

    def test_tutor_text_connects_prerequisites_and_keeps_claim_boundary(self):
        combined = "\n".join(
            self.read(name)
            for name in ("README.md", "lesson.md", "walkthrough.md", "checks.md")
        )
        for marker in (
            QUESTION,
            "P16",
            "P13",
            "state estimate",
            "Q",
            "R",
            "Riccati",
            "actuator",
            "two sentences",
            "MATLAB-runtime",
            "No MATLAB-runtime",
            "hard actuator limit",
            "integrated score units of seconds",
        ):
            self.assertIn(marker.lower(), combined.lower())
        for name in ("model.m", "experiment.m", "interactive.m", "run_checks.m", "lesson.m"):
            self.assertNotRegex(
                self.read(name).lower(),
                r"\b(?:lqr|dlqr|dare|idare|ss|c2d|lsim|inv|pinv)\s*\(",
            )
        for placeholder in ("scaffolded", "placeholder", "todo"):
            self.assertNotIn(placeholder, combined.lower())

    def test_readme_scopes_interactive_path_and_public_cli_is_isolated(self):
        readme = self.read("README.md")
        add_path = 'addpath(moduleFolder,"-begin");'
        clear_functions = "clear model interactive;"
        remove_path = "rmpath(moduleFolder);"
        self.assertIn(
            'moduleFolder = fullfile(pwd,"modules","17-balance-state-error-and-control-effort-with-lqr");',
            readme,
        )
        self.assertIn(add_path, readme)
        self.assertIn(clear_functions, readme)
        self.assertEqual(readme.count(remove_path), 2)
        self.assertIn("catch exception", readme)
        self.assertIn("rethrow(exception)", readme)

        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            shutil.copytree(ROOT / "bin", fixture / "bin")
            shutil.copytree(ROOT / "curriculum", fixture / "curriculum")
            shutil.copytree(self.folder, fixture / self.module["folder"])
            progress_file = fixture / ".learning/progress.json"
            progress_file.parent.mkdir(parents=True)
            original = {
                "current": "P16",
                "completed": {"P15": True},
                "notes": {"P15": "retain this note"},
            }
            progress_file.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            checked = subprocess.run(
                [str(fixture / "bin/learn"), "check", "P17"],
                cwd=fixture,
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(checked.stdout, "Run in MATLAB: run_module_checks('P17')\n")
            self.assertEqual(json.loads(progress_file.read_text()), original)
            started = subprocess.run(
                [str(fixture / "bin/learn"), "start", "P17"],
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
            self.assertEqual(retained["current"], "P17")
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
