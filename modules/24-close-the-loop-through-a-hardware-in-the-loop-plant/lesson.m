%% P24 - Close the Loop Through a Hardware-in-the-Loop Plant
% Guiding question:
% What inputs, observable effects, and failure modes matter when you close the Loop Through a Hardware-in-the-Loop Plant?

%% Read the controller-protocol-plant boundary before plotting
% P23 separated requested acceleration, physical response, and measurement. P24
% closes feedback across timestamped virtual measurement and command paths,
% then makes stale data, loss, watchdog action, and cancellation visible.

%% Run the ordered experiment
experiment;

%% Explore one lever at a time
% Run interactive.m. Move latency, reset, then move controller period.
% Explore packet loss, timeout, cancellation, and plant mass only after
% explaining which boundary each input changes.

%% Explain, check, and teach back
% Run run_checks.m, answer checks.md one prompt at a time, and give the
% required two-sentence teach-back. This virtual-time software emulator is
% not MATLAB-runtime, real-time target, bench, or physical HIL evidence.
