# P05 checks: Close a Loop with Proportional Control

Run `run_checks.m` first. It checks deterministic repeatability, the governing
equation, exact interval propagation, the closed-loop pole and time constant,
steady-state balance, both independent levers, zero-gain and zero-state limits,
sign symmetry, the reversed-sign broken/recovered pair, malformed inputs, endpoint
behavior, response bounds, and the maximum calculation grid.

Then answer one interpretation question at a time:

1. Which measured quantity is subtracted from the reference, and how does that subtraction change the next command?
2. Why does larger `Kp` reduce steady error and response time while increasing initial command?
3. Why can proportional control hold a nonzero output only while a nonzero error remains in this plant?
4. When only `tau` increases, which observable changes and which steady-state ratio remains fixed?
5. In the reversed-sign case, which assumption is violated, what visible symptom reveals the positive pole, and what recovery must happen first?

## Teach-back

In two sentences, answer: “What inputs, observable effects, and failure modes matter
when you close a Loop with Proportional Control?” Sentence one must connect
reference, measured output, error, gain, and command. Sentence two must identify the
speed/error/effort tradeoff, the reversed-sign symptom, and recovery.

Passing static repository tests does not claim that these MATLAB checks, figures, or
controls executed. Record a separate MATLAB-runtime result if they are run.
