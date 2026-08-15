# P06 checks: Tune a PID by Observing Each Term

Run `run_checks.m` before answering these questions. The executable checks cover
controller and plant identities, deterministic repeatability, both isolated
sweeps, limiting cases, malformed inputs, the derivative-sign failure and
recovery, time resolution, and the 20,001-sample resource bound.

Answer one interpretation question at a time:

1. At the baseline's first sample, why is the proportional force `4 N` while the
   integral and derivative forces are both zero?
2. With `Ki = 0`, why does the `-1 N` load leave `0.25 m` of error when `Kp = 4
   N/m`, even though the derivative term damps the transient?
3. When only `Ki` increases, which view proves offset removal, and which metric
   reveals that excessive integral action can overshoot?
4. When only `Kd` increases, why does overshoot fall while the peak magnitude of
   the derivative force rises?
5. In the broken case, what named assumption is violated when `D = +Kd*v`, and
   why is restoring `D = -Kd*v` the recovery step before retuning?

Teach-back: in two sentences, answer “What inputs, observable effects, and failure
modes matter when you tune a PID by Observing Each Term?” Name what P, I, and D
respond to, one visible tuning tradeoff, the wrong-sign symptom, and its recovery.
