# P09 lesson: Discretize a Continuous Controller

## Guiding question

What inputs, observable effects, and failure modes matter when you discretize a Continuous Controller?

## Compounds on

P06 exposed PI memory and separate controller terms. P07 connected loop dynamics
to stability reserve. P08 showed continuous feedback rejecting unwanted inputs.
P09 keeps a stable continuous PI target but makes measurement, computation, and
command timing explicit.

## Mental model

The normalized plant is `y' = -y + u`. A continuous PI controller would read
`e = 1-y` at every instant and apply `u = 2*e + 4*integral(e dt)`. Its closed-loop
characteristic equation is `s^2 + 3*s + 4 = 0`, so the continuous target is stable.

A digital controller reads `e[k]` every `Ts` seconds. Between samples, a zero-order
hold preserves `u[k]`, and the plant moves exactly according to
`y[k+1] = a*y[k] + (1-a)*u[k]`, where `a = exp(-Ts)`. The implementation writes
that operation directly instead of hiding it behind a conversion toolbox.

Forward Euler updates integral memory after using it, so `u[k]` contains error
through sample `k-1`. Backward Euler updates memory with `e[k]` before forming
`u[k]`. At small `Ts`, both approximate the same continuous controller. At finite
`Ts`, their timing and pole locations differ.

The sample-period sweep isolates how fewer updates create a larger tracking gap,
more visible hold action, and less trustworthy continuous approximation. The rule
sweep holds `Ts` and both gains fixed, so any delta comes from which sampled error
enters integral memory.

The broken case uses forward Euler at `Ts = 0.8 s`. Its explicitly calculated
closed-loop spectral radius exceeds one. Oscillations grow even though the original
continuous PI design is stable. The violated assumption is that the sample period
is small enough for the chosen discrete realization. Reducing `Ts` to `0.05 s`
restores pole magnitude below one and convergence.

## Tutor sequence

Ask one prediction before the baseline: which signal first reveals sampling—the
plant output or controller command? Show the output comparison, then reveal the
held command. Move sample period once and connect the change to update spacing.
Reset, change only the Euler rule, and connect the delta to current versus previous
error. Finally show the coarse-sample pole magnitude before revealing its growing
time trace, then recover by reducing `Ts`.

## Direct misconception corrections

- “Discretizing only changes syntax.” No. It changes when error enters memory and
  where the closed-loop poles lie.
- “The physical plant becomes discrete.” No. The controller samples and holds;
  the plant continues moving between samples.
- “A smooth line through samples proves a good approximation.” No. Inspect held
  effort, tracking gap, samples per natural period, and pole magnitude.
- “A stable continuous controller stays stable at any sample period.” No. The
  discrete realization can lose asymptotic convergence at pole magnitude one and
  grow when pole magnitude exceeds one.
- “The plot proves runtime or hardware behavior.” No. It is a retained software
  model; MATLAB runtime, UI, numerical fidelity, bench, HIL, and field validation
  require separate evidence.

## Teach-back

In two sentences, explain what is sampled and what is held, describe how `Ts` or
Euler rule changes one observable, and name the broken assumption, symptom, and
recovery.
