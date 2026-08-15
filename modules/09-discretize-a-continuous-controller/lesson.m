%% P09 - Discretize a Continuous Controller
% Guiding question:
% What inputs, observable effects, and failure modes matter when you discretize a Continuous Controller?
%
% P08 treated feedback as continuous. A processor instead samples error,
% updates a controller state, and holds one command until the next sample.
% Predict which trace becomes stair-stepped first: plant output or control effort.

%% Read the sampled-data mechanism
% The plant remains y'=-y+u. The PI target is u=2*e+4*integral(e dt),
% where e=1-y. During a sample interval the held command makes the plant
% transition exact: y_next=exp(-Ts)*y+(1-exp(-Ts))*u.

%% Visualize the deterministic baseline
baseline = model(0.05,'backward-euler',12,0.01);
figure('Name','P09 lesson baseline');
plot(baseline.t,baseline.continuousOutput,'k--','LineWidth',1.3, ...
    'DisplayName','Continuous PI target');
hold on;
plot(baseline.t,baseline.digitalOutput,'LineWidth',1.7, ...
    'DisplayName','Digital PI output');
stairs(baseline.sampleTimes,baseline.controlSamples,'LineWidth',1.2, ...
    'DisplayName','Held digital command');
hold off; grid on;
xlabel('Time (s)'); ylabel('Amplitude (output)');
title('Baseline: samples are discrete even while the plant moves continuously');
legend('Location','best');

%% Read and explain the observed difference
% The output is not a staircase because the physical plant evolves between
% controller updates. The command is held. At Ts=0.05 s, the digital output
% stays close to the continuous target, but it is not identical to it.

%% Move one lever at a time
% Run experiment.m one section at a time. First move sample period with the
% backward-Euler rule fixed. Reset Ts to 0.05 s, then move only the rule.
% Read the mechanism after each changed view before opening interactive.m.

%% Open the bounded interactive view
interactive;
