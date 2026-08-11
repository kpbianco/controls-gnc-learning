# Lesson: Watch a Mass-Spring-Damper Respond

## Guiding question

How do mass, stiffness, and damping determine visible motion?

## Mental model

A mass stores momentum, a spring stores potential energy, and a damper removes energy. Their balance determines oscillation, settling, and overshoot.

## What to manipulate

Use `interactive.m`. Change one lever at a time before combining effects.

## First observation

Lower damping until the response rings, then raise it until motion becomes sluggish. Change mass and stiffness separately and notice that both alter natural frequency in different physical ways.

## Common mistakes

- More damping is not always faster.
- A stable system can still be too slow or too oscillatory.
- The same-looking step response can hide different physical parameters.

## Completion standard

The learner can explain the baseline, identify what each lever changes, diagnose the deliberately broken case, and pass `run_checks.m`.
