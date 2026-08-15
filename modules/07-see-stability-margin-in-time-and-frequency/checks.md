# P07 checks: See Stability Margin in Time and Frequency

Run `run_checks.m` before answering these questions. The executable checks cover
deterministic repeatability, state and frequency identities, exact margin
relations, both isolated sweeps, zero-gain and zero-lag limits, malformed inputs,
time resolution, the 20,001-sample resource bound, instability, and recovery.

Answer one interpretation question at a time:

1. At gain crossover, why is magnitude `0 dB`, and what angular distance is the
   phase margin measuring?
2. When only `K` increases, why does crossover move higher, phase margin shrink,
   and time-domain overshoot rise?
3. When only `tau` increases, which frequency term adds lag, and what time-domain
   symptom reveals the lost reserve?
4. Why can a stable response still oscillate even though gain margin exceeds one
   and phase margin is positive?
5. In the broken case, what assumption was violated when `K = 4 1/s^2` was selected
   using `tau = 0`, and why does reducing gain below `b*(1+b*tau)/tau` recover the
   actual lagged loop?

Teach-back: in two sentences, answer “What inputs, observable effects, and failure
modes matter when you see Stability Margin in Time and Frequency?” Name both
levers, one time/frequency connection, the omitted-lag symptom, and its recovery.
