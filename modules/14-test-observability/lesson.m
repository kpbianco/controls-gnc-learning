%% P14 - Test Observability
% Guiding question:
% What inputs, observable effects, and failure modes matter when you test Observability?
%
% P13 asked whether an actuator can move every state direction. P14 reverses
% the information path: can a sensor history distinguish every initial state?

%% Observe the deterministic baseline
% Run experiment one section at a time. Before the first measurement plot,
% predict whether position samples can reveal a rate that is not measured
% directly.
experiment;

%% Move one lever at a time
% Sweep position-sensor sensitivity while the observation window stays at
% 2 s. Then reset sensitivity to 1 sensor unit/m and sweep only the window.
% Rank can stay full while separation and noise amplification change.

%% Explain the mechanism from visible rows
% The exact sampled observation matrix is
%   O = [C; C*Ad; ...; C*Ad^N].
% Each row maps the initial state to one output sample. Sensor gain scales
% every row; a longer window adds rows in which initial rate has had more
% time to accumulate into measured position.

%% Break, recover, check, and teach back
% Select rate-only measurement. Two states separated only by a constant
% position offset produce identical outputs, so position is not unique.
% Restore position measurement, run run_checks, then give the two-sentence
% teach-back requested in checks.md.
