%% P23 - Model Sensor and Actuator Dynamics
% Guiding question:
% What inputs, observable effects, and failure modes matter when you model Sensor and Actuator Dynamics?

%% Read the request-motion-measurement boundary before plotting
% P22 generated a lateral-acceleration request. P23 separates that request
% from actuator motion and from the sensor report with two visible
% first-order states, a magnitude limit, and a declared sensor bias.

%% Run the ordered experiment
experiment;

%% Explore one lever at a time
% Run interactive.m. Change sensor tau, reset, then change actuator tau.
% Explore command timing, limit, and bias only after explaining which state
% each one affects.

%% Explain, check, and teach back
% Run run_checks.m, answer checks.md one prompt at a time, and give the
% required two-sentence teach-back. Simulated state histories are not sensor
% calibration, actuator characterization, HIL, or physical evidence.
