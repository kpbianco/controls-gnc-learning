# P04 checks: Compare Linear and Nonlinear Pendulum Models

Run `run_checks.m` first. It checks deterministic repeatability, shared initial
conditions, governing accelerations, linear poles and period, energy direction,
release-angle and length levers, small-angle and zero-state limits, sign symmetry,
the broken/recovered pair, malformed inputs, endpoint behavior, calculation
resolution, and resource bounds.

Then answer one interpretation question at a time:

1. Which single restoring term differs between the models, and why must `theta` be in radians when making the small-angle comparison?
2. At a 20-degree release, why does the nonlinear curve gradually lag even though both models begin from exactly the same state?
3. When only release angle increases, which error grows and which physical parameters remain unchanged?
4. When only length increases, why do both predictions slow down, and why does that not repair a large-angle approximation?
5. In the 120-degree broken case, which assumption is violated, what visible symptom reveals it, and what two recovery choices are available?

## Teach-back

In two sentences, answer: “What inputs, observable effects, and failure modes matter
when you compare Linear and Nonlinear Pendulum Models?” Sentence one must connect
the two restoring laws to release angle and length. Sentence two must identify the
large-angle symptom and a valid recovery.

Passing static repository tests does not claim that these MATLAB checks, figures, or
controls executed. Record a separate MATLAB-runtime result if they are run.
