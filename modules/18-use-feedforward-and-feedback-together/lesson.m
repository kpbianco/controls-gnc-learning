%% P18 - Use Feedforward and Feedback Together
% Guiding question:
% What inputs, observable effects, and failure modes matter when you use Feedforward and Feedback Together?
%
% P17 chose a state-feedback gain for a damped cart. P18 keeps that plant
% and gain, adds a feasible reference plus its planned input, and exposes
% how anticipatory feedforward and error-driven feedback share one command.

%% Observe the deterministic baseline
% Run experiment one section at a time. Make only one prediction before the
% baseline: which command component wakes up when the unplanned load begins?
experiment;

%% Move one lever, view the change, then explain it
% With disturbance removed, sweep only feedforward scale alpha. At alpha=1
% the feasible plan is matched exactly and feedback correction is silent.
% The error recurrence shows why mismatch forces feedback to recreate input.

%% Reset, move the second lever, and explain recovery
% Restore alpha=1 and the load pulse, then sweep only feedback scale beta.
% Feedforward still follows the known plan; positive feedback authority moves
% the error poles inside the unit circle and removes the unplanned offset.

%% Break the mixer, recover, check, and teach back
% Reverse feedforward polarity. Feedback fights the predictable wrong-sign
% command, so opposing components become the diagnostic symptom. Restore the
% sign, run run_checks, then give the two-sentence checks.md teach-back.
