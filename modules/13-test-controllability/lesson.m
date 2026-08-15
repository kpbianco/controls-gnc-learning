%% P13 - Test Controllability
% Guiding question:
% What inputs, observable effects, and failure modes matter when you test Controllability?
%
% P12 separated requested effort from applied effort. P13 asks whether the
% available input direction can reach both states at all. Command acts on
% rate first; an intact kinematic coupling lets that rate change position.

%% Observe the deterministic baseline
% Run experiment one section at a time. Before the first plot, predict
% whether an actuator that directly changes only rate can also move position.
experiment;

%% Move one lever at a time
% Sweep actuator effectiveness while maneuver time stays at 2 s. Then reset
% effectiveness to 1 (m/s^2)/command and sweep only maneuver time. Rank can
% stay full while the smallest reachability direction and required command
% effort change substantially.

%% Explain the mechanism from visible columns
% The exact held-input reachability matrix is
%   R = [Ad^(N-1)*Bd, ..., Ad*Bd, Bd].
% Each column is the terminal-state effect of one command sample. Input gain
% scales every column; a longer maneuver adds earlier columns whose rate can
% flow through the dynamics into position.

%% Break, recover, check, and teach back
% Set the kinematic coupling to zero. A probe still changes rate, but no rate
% history can move position and the rank falls to one. Restore coupling, run
% run_checks, then give the two-sentence teach-back requested in checks.md.
