from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTION = (
    "What inputs, observable effects, and failure modes matter when you test "
    "Controllability?"
)


@dataclass
class ReferenceResult:
    discrete_a: tuple[tuple[float, float], tuple[float, float]]
    discrete_b: tuple[float, float]
    reachability: list[tuple[float, float]]
    gramian: tuple[float, float, float]
    minimum_singular_value: float
    rank: int
    reachable: bool
    command: list[float]
    transfer_command: list[float]
    trajectory: list[tuple[float, float]]
    probe: list[tuple[float, float]]
    energy: float
    peak: float
    residual: float


def matvec(
    matrix: tuple[tuple[float, float], tuple[float, float]],
    vector: tuple[float, float],
) -> tuple[float, float]:
    return (
        matrix[0][0] * vector[0] + matrix[0][1] * vector[1],
        matrix[1][0] * vector[0] + matrix[1][1] * vector[1],
    )


def reference_model(
    input_gain: float = 1,
    coupling: float = 1,
    horizon: float = 2,
    time_step: float = 0.05,
) -> ReferenceResult:
    damping = 0.5
    step_count = round(horizon / time_step)
    decay = math.exp(-damping * time_step)
    discrete_a = (
        (1.0, coupling * (1 - decay) / damping),
        (0.0, decay),
    )
    discrete_b = (
        coupling
        * input_gain
        / damping
        * (time_step - (1 - decay) / damping),
        input_gain * (1 - decay) / damping,
    )

    reachability = [(0.0, 0.0)] * step_count
    reachability[-1] = discrete_b
    for index in range(step_count - 2, -1, -1):
        reachability[index] = matvec(discrete_a, reachability[index + 1])
    g11 = sum(column[0] ** 2 for column in reachability)
    g12 = sum(column[0] * column[1] for column in reachability)
    g22 = sum(column[1] ** 2 for column in reachability)
    trace = g11 + g22
    spread = math.hypot(g11 - g22, 2 * g12)
    lambda_maximum = max(0.0, 0.5 * (trace + spread))
    lambda_minimum = max(0.0, 0.5 * (trace - spread))
    tolerance = 128 * math.ulp(max(trace, 1.0))
    if lambda_maximum <= tolerance:
        rank = 0
    elif lambda_minimum <= tolerance:
        rank = 1
    else:
        rank = 2
    if rank == 2:
        determinant = g11 * g22 - g12 * g12
        dual = (g22 / determinant, -g12 / determinant)
        command = [
            column[0] * dual[0] + column[1] * dual[1]
            for column in reachability
        ]
        transfer_command = command
    else:
        command = [math.nan] * step_count
        transfer_command = [0.0] * step_count

    def simulate(commands: list[float]) -> list[tuple[float, float]]:
        state = (0.0, 0.0)
        states = [state]
        for held_command in commands:
            propagated = matvec(discrete_a, state)
            state = (
                propagated[0] + discrete_b[0] * held_command,
                propagated[1] + discrete_b[1] * held_command,
            )
            states.append(state)
        return states

    trajectory = simulate(transfer_command)
    probe_command = [0.0] * step_count
    probe_step_count = max(1, math.floor(0.25 * step_count + 0.5))
    for index in range(probe_step_count):
        probe_command[index] = 1.0
    probe = simulate(probe_command)
    terminal = trajectory[-1]
    return ReferenceResult(
        discrete_a=discrete_a,
        discrete_b=discrete_b,
        reachability=reachability,
        gramian=(g11, g12, g22),
        minimum_singular_value=math.sqrt(lambda_minimum),
        rank=rank,
        reachable=rank == 2,
        command=command,
        transfer_command=transfer_command,
        trajectory=trajectory,
        probe=probe,
        energy=(
            time_step * sum(value * value for value in command)
            if rank == 2
            else math.inf
        ),
        peak=max(abs(value) for value in command) if rank == 2 else math.inf,
        residual=math.hypot(1 - terminal[0], terminal[1]),
    )


class P13ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "curriculum/modules.json").read_text(encoding="utf-8")
        )
        cls.module = next(
            module for module in cls.manifest["modules"] if module["id"] == "P13"
        )
        cls.folder = ROOT / cls.module["folder"]

    def read(self, name: str) -> str:
        return (self.folder / name).read_text(encoding="utf-8")

    def test_manifest_identity_and_permanent_completion(self):
        self.assertEqual(self.module["number"], 13)
        self.assertEqual(self.module["title"], "Test Controllability")
        self.assertEqual(self.module["guiding_question"], QUESTION)
        self.assertEqual(self.module["phase"], 4)
        self.assertEqual(self.module["phase_title"], "State-space control")
        self.assertEqual(self.module["prerequisites"], ["P12"])
        self.assertEqual(self.module["implementation_batch"], "P13")
        self.assertEqual(self.module["status"], "implemented")
        self.assertEqual(self.module["evidence_level"], "simulated")

    def test_public_check_route_resolves_p13_without_mutating_progress(self):
        checked = subprocess.run(
            [str(ROOT / "bin/learn"), "check", "P13"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertEqual(checked.stdout, "Run in MATLAB: run_module_checks('P13')\n")

    def test_public_start_then_continue_retains_p13_in_isolated_learner_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "repo"
            shutil.copytree(ROOT / "bin", fixture / "bin")
            shutil.copytree(ROOT / "curriculum", fixture / "curriculum")
            shutil.copytree(self.folder, fixture / self.module["folder"])
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"

            started = subprocess.run(
                [str(fixture / "bin/learn"), "start", "P13"],
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
                "P13 — Test Controllability",
                "Status: implemented",
                f"Guiding question: {QUESTION}",
                "Folder: modules/13-test-controllability",
                "launch_lesson('P13')",
                "modules/13-test-controllability/checks.md",
            ):
                self.assertIn(expected, started.stdout)

            progress = json.loads(
                (fixture / ".learning/progress.json").read_text(encoding="utf-8")
            )
            self.assertEqual(progress["current"], "P13")
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
            self.assertEqual(continued.stderr, "")
            self.assertEqual(continued.stdout, started.stdout)

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

    def test_model_is_transparent_pure_and_resource_bounded(self):
        model = self.read("model.m")
        for formula in (
            "continuousA = [0 coupling;0 -dampingPerSec]",
            "continuousB = [0;inputGain]",
            "[continuousB continuousA*continuousB]",
            "-coupling*inputGain*inputGain",
            "decay = exp(-dampingPerSec*timeStepSec)",
            "discreteA = [1 positionFromRate;0 rateFromRate]",
            "discreteB = [positionFromCommand;rateFromCommand]",
            "reachabilityMatrix(:,k) = discreteA*reachabilityMatrix(:,k+1)",
            "scaledReachabilityMatrix = stateScaling*reachabilityMatrix",
            "gramian = scaledReachabilityMatrix*scaledReachabilityMatrix.'",
            "minimumEnergyCommand = scaledReachabilityMatrix.'*dualState",
            "transferCommand = zeros(stepCount,1)",
            "stateTrajectory(:,k+1) = discreteA*stateTrajectory(:,k)+",
        ):
            self.assertIn(formula, model)
        for validation in (
            "maximumStepCount = 5000",
            "maximumCommandMagnitude = 100",
            "stateScaling = diag([1/positionScaleM 1/rateScaleMPerSec])",
            "P13:InputGainRange",
            "P13:CouplingRange",
            "P13:HorizonRange",
            "P13:DisplayResolution",
            "P13:TargetRange",
            "P13:TooManySteps",
            "P13:GridAlignment",
            "P13:CommandBound",
        ):
            self.assertIn(validation, model)
        self.assertLess(
            model.index("stepCount > maximumStepCount"),
            model.index("reachabilityMatrix = zeros(2,stepCount)"),
        )
        self.assertNotRegex(
            model.lower(),
            r"\b(?:plot|figure|uifigure|uiaxes|uislider|uidropdown|rng|random)\s*\(",
        )

    def test_independent_baseline_exact_hold_and_target_reconstruction(self):
        result = reference_model()
        decay = math.exp(-0.025)
        self.assertAlmostEqual(result.discrete_a[0][1], 2 * (1 - decay))
        self.assertAlmostEqual(result.discrete_a[1][1], decay)
        self.assertAlmostEqual(result.discrete_b[0], 2 * (0.05 - 2 * (1 - decay)))
        self.assertAlmostEqual(result.discrete_b[1], 2 * (1 - decay))
        self.assertEqual(result.rank, 2)
        self.assertAlmostEqual(result.minimum_singular_value, 0.1162100350701485)
        self.assertAlmostEqual(result.energy, 1.6508722484834308)
        self.assertAlmostEqual(result.peak, 1.5033135650687792)
        self.assertLess(result.residual, 2e-14)
        self.assertGreater(max(state[1] for state in result.trajectory), 0.74)
        self.assertAlmostEqual(result.trajectory[-1][0], 1.0)
        self.assertAlmostEqual(result.trajectory[-1][1], 0.0)

    def test_independent_reachability_columns_and_gramian(self):
        result = reference_model()
        self.assertEqual(len(result.reachability), 40)
        self.assertEqual(result.reachability[-1], result.discrete_b)
        for earlier, later in zip(result.reachability, result.reachability[1:]):
            propagated = matvec(result.discrete_a, later)
            self.assertAlmostEqual(earlier[0], propagated[0])
            self.assertAlmostEqual(earlier[1], propagated[1])
        g11, g12, g22 = result.gramian
        self.assertAlmostEqual(g11, 0.06722748992859534)
        self.assertAlmostEqual(g12, 0.03996214326999061)
        self.assertAlmostEqual(g22, 0.043230984247860524)
        reconstructed = (
            sum(column[0] * command for column, command in zip(result.reachability, result.command)),
            sum(column[1] * command for column, command in zip(result.reachability, result.command)),
        )
        self.assertAlmostEqual(reconstructed[0], 1.0)
        self.assertAlmostEqual(reconstructed[1], 0.0)
        columns = result.reachability[:3]
        null_direction = [
            columns[1][0] * columns[2][1] - columns[1][1] * columns[2][0],
            columns[2][0] * columns[0][1] - columns[2][1] * columns[0][0],
            columns[0][0] * columns[1][1] - columns[0][1] * columns[1][0],
        ]
        length = math.sqrt(sum(value * value for value in null_direction))
        null_direction = [value / length for value in null_direction]
        self.assertAlmostEqual(
            sum(column[0] * value for column, value in zip(columns, null_direction)),
            0.0,
        )
        self.assertAlmostEqual(
            sum(column[1] * value for column, value in zip(columns, null_direction)),
            0.0,
        )
        self.assertAlmostEqual(
            sum(command * value for command, value in zip(result.command, null_direction)),
            0.0,
        )
        perturbed = result.command.copy()
        for index, value in enumerate(null_direction):
            perturbed[index] += value
        self.assertGreater(
            0.05 * sum(value * value for value in perturbed),
            result.energy + 0.04,
        )

    def test_two_sweeps_are_independent_and_have_expected_limits(self):
        baseline = reference_model()
        gains = [0.25, 0.5, 1.0, 1.5, 2.0]
        gain_results = [reference_model(input_gain=gain) for gain in gains]
        self.assertTrue(all(result.rank == 2 for result in gain_results))
        for gain, result in zip(gains, gain_results):
            self.assertAlmostEqual(
                result.minimum_singular_value,
                gain * baseline.minimum_singular_value,
            )
            self.assertAlmostEqual(result.energy, baseline.energy / gain**2)
            self.assertAlmostEqual(result.peak, baseline.peak / gain)
        horizons = [0.5, 1.0, 2.0, 3.0, 4.0]
        time_results = [reference_model(horizon=horizon) for horizon in horizons]
        self.assertTrue(all(result.rank == 2 for result in time_results))
        self.assertEqual(
            [result.energy for result in time_results],
            sorted((result.energy for result in time_results), reverse=True),
        )
        self.assertEqual(
            [result.peak for result in time_results],
            sorted((result.peak for result in time_results), reverse=True),
        )
        self.assertGreater(time_results[0].energy, 50 * time_results[2].energy)

    def test_broken_case_zero_input_limit_and_recovery_are_isolated(self):
        broken = reference_model(coupling=0)
        recovered = reference_model(coupling=1)
        no_actuator = reference_model(input_gain=0)
        self.assertEqual(broken.rank, 1)
        self.assertFalse(broken.reachable)
        self.assertEqual(no_actuator.rank, 0)
        self.assertFalse(no_actuator.reachable)
        self.assertTrue(all(state[0] == 0 for state in broken.probe))
        self.assertEqual(
            [state[1] for state in broken.probe],
            [state[1] for state in recovered.probe],
        )
        self.assertGreater(max(state[0] for state in recovered.probe), 0.1)
        self.assertTrue(all(math.isnan(value) for value in broken.command))
        self.assertEqual(broken.transfer_command, [0.0] * 40)
        self.assertTrue(math.isinf(broken.energy))
        self.assertTrue(math.isinf(broken.peak))
        self.assertEqual(broken.residual, 1.0)
        self.assertTrue(all(state == (0.0, 0.0) for state in no_actuator.probe))
        self.assertLess(recovered.residual, 2e-14)
        short = reference_model(horizon=0.5)
        short_decay = short.discrete_a[1][1]
        self.assertGreater(short.probe[3][1], 0)
        self.assertAlmostEqual(short.probe[4][1], short_decay * short.probe[3][1])

    def test_experiment_has_learning_flow_labels_metrics_sweeps_and_broken_case(self):
        experiment = self.read("experiment.m")
        section_titles = re.findall(r"^%% (.+)$", experiment, flags=re.MULTILINE)
        self.assertGreaterEqual(len(section_titles), 10)
        for marker in (
            "%% Read -",
            "%% Visualize baseline",
            "%% Changed view",
            "%% Sweep 1",
            "%% Read and explain sweep 1",
            "%% Sweep 2",
            "%% Read and explain sweep 2",
            "%% Broken case",
            "%% Check and teach back",
            "inputGains = [0.25 0.5 1 1.5 2]",
            "maneuverTimesSec = [0.5 1 2 3 4]",
            "broken = model(1,0,2,0.05)",
            "recovered = model(1,1,2,0.05)",
            "stairs(baseline.timeSec,[baseline.minimumEnergyCommand; ...",
            "baseline.minimumEnergyCommand(end)]",
        ):
            self.assertIn(marker, experiment)
        for unit in (
            "Time (s)",
            "Position (m)",
            "Rate (m/s)",
            "Command (command)",
            "Input gain ((m/s^2)/command)",
            "Command energy (command^2*s)",
            "Maneuver time (s)",
        ):
            self.assertIn(unit, experiment)
        self.assertIn("scaled sigma_min", experiment)
        self.assertIn("terminal position ' ...", experiment)
        self.assertIn("residual %.3f / %.3g m", experiment)

    def test_interactive_exposes_meaningful_controls_reset_and_immediate_feedback(self):
        interactive = self.read("interactive.m")
        for marker in (
            "uifigure(",
            "uiaxes(",
            "uislider(",
            "uispinner(",
            "uidropdown(",
            "Input gain ((m/s^2)/command)",
            "Maneuver time (s)",
            "Disconnected (broken)",
            "ValueChangingFcn",
            "ValueChangedFcn",
            "ButtonPushedFcn",
            "resetBaseline",
            "redraw(1,2,'Intact coupling')",
            "horizonSec = round(horizonSec/0.05)*0.05",
            "result = modelFunction(inputGain,coupling,horizonSec,0.05)",
            "position unreachable",
            "effortText = 'energy N/A | peak N/A'",
            "full rank, demanding command",
        ):
            self.assertIn(marker, interactive)

    def test_checks_cover_invariants_malformed_inputs_recovery_and_bounds(self):
        checks = self.read("run_checks.m")
        for marker in (
            "isequaln(baselineA,baselineB)",
            "expectedContinuousColumns",
            "expectedAd",
            "expectedBd",
            "expectedGramian",
            "reconstructedTarget",
            "inputGains = [0.25 0.5 1 1.5 2]",
            "maneuverTimesSec = [0.5 1 2 3 4]",
            "broken = model(1,0,2,0.05)",
            "recovered = model(1,1,2,0.05)",
            "noActuator = model(0,1,2,0.05)",
            "all(isnan(broken.minimumEnergyCommand))",
            "broken.transferCommand",
            "model(NaN,1,2,0.05)",
            "model([1 2],1,2,0.05)",
            "model(1,1+1i,2,0.05)",
            "P13:GridAlignment",
            "P13:TooManySteps",
            "P13:CommandBound",
            "boundedGrid = model(1,1,5,0.001)",
        ):
            self.assertIn(marker, checks)

    def test_tutor_text_connects_prerequisite_interpretation_and_claim_boundary(self):
        readme = self.read("README.md")
        lesson = self.read("lesson.md")
        walkthrough = self.read("walkthrough.md")
        checks = self.read("checks.md")
        combined = "\n".join((readme, lesson, walkthrough, checks))
        self.assertIn(QUESTION, combined)
        self.assertIn("P12", lesson)
        self.assertIn("P14", lesson)
        self.assertIn("two sentences", combined.lower())
        self.assertIn("coordinate-scaled", readme)
        self.assertIn("Full rank does not mean", lesson)
        for excluded_claim in (
            "no MATLAB-runtime",
            "UI",
            "MATLAB numerical-",
            "bench",
            "HIL",
            "field",
            "production",
        ):
            self.assertIn(excluded_claim, combined)
        self.assertNotIn("syntax-first", combined.lower())

    def test_no_placeholder_or_opaque_control_toolbox_path(self):
        combined = "\n".join(
            self.read(name)
            for name in ("model.m", "experiment.m", "interactive.m", "run_checks.m")
        )
        self.assertNotIn("scaffolded", combined.lower())
        self.assertNotIn("not implemented", combined.lower())
        self.assertNotRegex(
            combined.lower(),
            r"\b(?:ctrb|rank|gram|c2d|ss|lsim|pinv|expm|ode45)\s*\(",
        )


if __name__ == "__main__":
    unittest.main()
