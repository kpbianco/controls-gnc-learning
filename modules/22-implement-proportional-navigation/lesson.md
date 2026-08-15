# P22 lesson: Implement Proportional Navigation

## Guiding question

What inputs, observable effects, and failure modes matter when you implement Proportional Navigation?

## Compounds on P21

P21 generated a smooth reference and compared its derivative demands with declared limits. P22 makes the
next distinction: a guidance law generates an acceleration request from relative geometry, while the
vehicle's acceleration authority decides whether that request can be applied. Guidance success and
trajectory feasibility are related boundaries, not interchangeable claims.

## Mental model

Imagine the line of sight as a bearing drawn from interceptor to target. If that bearing stays constant
while range decreases, the two paths are converging. If the bearing continues rotating, the interceptor
will pass to one side unless it turns enough to remove the rotation.

For relative position `r = [r_x,r_y]` and relative velocity `v_rel`, use

```text
R         = sqrt(r_x^2 + r_y^2)                     [m]
Vc        = -dot(r,v_rel)/R                          [m/s]
lambdaDot = (r_x*v_rel_y-r_y*v_rel_x)/R^2            [rad/s]
a_cmd     = N*max(Vc,0)*lambdaDot                    [m/s^2]
a_applied = clip(a_cmd,-a_max,+a_max)                [m/s^2]
psi_next  = psi + (a_applied/interceptor_speed)*dt   [rad]
```

The cross product order fixes the turn sign; the minus sign makes `Vc` positive while closing. The
`max(Vc,0)` term stops PN from treating an opening engagement as though it were still closing. The model
uses radians internally and accelerates normal to a constant-speed velocity.

## What the baseline reveals

At `[5000,600] m` with target crossing speed `60 m/s`, the initial range is about `5035.87 m`, closing
speed is about `290.72 m/s`, and LOS rate is about `0.01893 rad/s`. With `N=3`, the initial command is
about `16.51 m/s^2`, below the `80 m/s^2` limit. The path bends until LOS rotation is nearly removed and
the piecewise-linear relative segment first crosses the `5 m` capture circle.

Event interpolation matters: a time step can cross the circle between plotted samples. The source solves
the segment/circle intersection and stops at the first entry rather than calling the nearest sample an
exact collision.

## Two levers and the broken assumption

- Increasing `N` multiplies the initial command exactly because the initial `Vc` and `lambdaDot` are
  shared. Later paths differ because each turn changes future geometry. Too-small `N` can leave a miss;
  larger `N` commands more acceleration and eventually gives diminishing time benefit.
- Reducing `a_max` leaves the raw PN request intact but clips applied acceleration. The difference between
  command and applied turn is visible saturation, directly connecting to P21's limit discipline.
- In the deliberately broken `5 m/s^2` case, clipping persists, range bottoms out far outside `5 m`, then
  opens until the `25 s` time limit. Restoring `80 m/s^2` exactly recovers the baseline.

## Limiting cases

A target crossing speed of `-36 m/s` makes relative velocity initially parallel to `-r`; LOS rate and PN
command are zero, yet constant bearing plus decreasing range produces capture without a turn. `N=0`
also gives zero command, but for the `60 m/s` crossing baseline geometry the bearing rotates and the
interceptor misses. Once closing speed becomes nonpositive after a miss, the model commands zero rather
than using the magnitude of an opening speed.

## Misconceptions to correct directly

- PN does not aim at the target's current location; it acts on LOS rotation.
- LOS angle and LOS rate are different measurements.
- A larger `N` is not free: it raises acceleration demand.
- Commanded acceleration and applied acceleration are identical only when the actuator does not clip.
- Small range alone is not the mechanism; constant bearing with decreasing range is the intercept cue.
- Capture radius is not exact collision, and sampled simulation is not continuous-time proof.
- This point-mass model omits sensor noise, delay, actuator dynamics, target maneuver acceleration,
  autopilot stability, collision safety, HIL timing, and physical implementation.
- Independent reference arithmetic is not MATLAB-runtime or rendered-UI evidence.

Ask one observation question at a time. Request the teach-back only after executable checks pass.
