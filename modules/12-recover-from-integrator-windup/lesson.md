# P12 lesson: Recover from Integrator Windup

## Guiding question

What inputs, observable effects, and failure modes matter when you recover from Integrator Windup?

## Compounds on

- **P05:** feedback error drives controller effort.
- **P06:** the integral term is controller memory with actuator units.
- **P09 and P10:** a digital controller updates state over explicit held-command intervals.
- **P11:** requested and applied control separate when actuator authority is exhausted.

## One prediction before the baseline

The reference stays at an unreachable `+2 output` for three seconds, then changes to reachable
`-0.5 output`. Two PI loops have identical gains, plant, time grid, and `±1 actuator` limit. One
integrator uses only `Ki*e`; the other also uses the requested-applied command gap. Which loop will
reverse applied control first, and what internal state should explain the difference?

## Mechanism-first explanation

The controller requests

`uRequested = Kp*e + I`,

but the plant receives

`uApplied = clamp(uRequested, -uLimit, +uLimit)`.

With no anti-windup, `I` keeps integrating positive error while `uApplied` is already pinned. The
growing request cannot make the actuator push harder; it only stores a larger obsolete command.
Back-calculation adds

`Kaw*(uApplied-uRequested)`

to the integral derivative. During positive clipping the term is negative, so it opposes windup.
After the reference reverses, less positive memory blocks the needed negative control.

## Levers and observable effects

### Anti-windup gain `Kaw` (1/s)

- `Kaw = 0` is the exact no-protection limiting case.
- Moderate gain lowers integral state at release and post-release integral absolute error.
- Excessive gain can drive the integral state too negative and add an opposite recovery transient.

### High-demand duration (s)

- Longer duration keeps the actuator pinned while the unprotected integral state grows.
- Correct back-calculation uses the persistent command gap to bound stored effort.
- The duration lever changes exposure to saturation, not plant or controller gains.

## Deliberately broken case

The broken case uses `uRequested-uApplied` where the correction needs
`uApplied-uRequested`. Missing positive command then adds more positive integral state. The request
grows, the actuator stays pinned in the old direction after the target changes, and recovery fails.
This is a sign error in a feedback path, not evidence that anti-windup itself creates more authority.

## Correct these misconceptions directly

- **“The integrator makes the actuator stronger.”** No. Applied effort remains within `±1 actuator`.
- **“Any large anti-windup gain is better.”** No. Over-aggressive correction can over-unwind state.
- **“Clipping alone is windup.”** No. P11 clipped a P controller with no integral state. Windup is
  incompatible stored controller memory during clipping.
- **“Low output after reversal proves plant delay.”** Not by itself. Inspect integral state and
  applied-command direction to distinguish controller memory from the one-second plant time constant.

## Teach-back

In two sentences, explain why an unprotected PI controller can keep applying effort in the old
direction after a reference reversal, and how correctly signed back-calculation changes the
integral-state update without violating the actuator limit.
