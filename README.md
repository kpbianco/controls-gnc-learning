# Controls, State Estimation, Guidance, and Navigation

A MATLAB-first, Khan-Academy-style learning track with 24 guided modules.

Each implemented module combines:

- a concise lesson and physical mental model;
- MATLAB `%%` notebook cells;
- deterministic plots;
- actual UI sliders, spinners, or dropdowns;
- two parameter sweeps;
- one deliberately broken case;
- executable numerical checks;
- a tutor protocol that asks one observation question at a time.

## Start

From a shell:

```bash
./bin/learn start
./bin/learn start P01
./bin/learn start P02
./bin/learn start P03
./bin/learn start P04
./bin/learn start P05
./bin/learn start P06
./bin/learn start P07
./bin/learn start P08
./bin/learn start P09
./bin/learn start P10
./bin/learn list
./bin/learn status
```

On Windows PowerShell:

```powershell
python .\bin\learn.py start
```

In MATLAB:

```matlab
launch_lesson("P01")
run_module_checks("P01")
```

`P01` is the complete reference implementation; `P02` through `P10` are implemented
learning slices. Later modules remain intentionally scaffolded so each can be
implemented in a bounded, reviewable batch.

## Module layout

```text
modules/01-example/
├── README.md
├── lesson.m
├── model.m
├── experiment.m
├── interactive.m
├── lesson.md
├── walkthrough.md
├── checks.md
└── run_checks.m
```

## Learning contract

The flow is always:

> question → mental model → baseline → manipulate levers → observe plots → break an assumption → explain → check → teach back

This repository is compatible with the same tutor/build split used by `dsp-radar_learning`.
