%% P08 - Reject a Disturbance with Feedback
% Guiding question:
% What inputs, observable effects, and failure modes matter when you reject a Disturbance with Feedback?
%
% P06 made controller effort visible, and P07 made loop reserve visible. P08
% now asks which unwanted inputs that loop can actually suppress. Predict what
% happens to a constant plant-input load when proportional gain increases.

%% Read the physical model
% A normalized first-order plant obeys tau*y'=-y+u+d with tau=1 s. The zero
% reference controller is u=-K*y_measured. With an honest sensor and a constant
% disturbance, equilibrium requires y=d/(1+K) and u=-K*d/(1+K).

%% Visualize the deterministic baseline
baseline = model(4,1,0,0,12,0.01);
figure('Name','P08 lesson baseline');
plot(baseline.t,baseline.disturbanceInput,'k--','LineWidth',1.2, ...
    'DisplayName','Plant-input disturbance d');
hold on;
plot(baseline.t,baseline.trueOutput,'LineWidth',1.6, ...
    'DisplayName','True output y');
plot(baseline.t,baseline.controlEffort,'LineWidth',1.3, ...
    'DisplayName','Control effort u');
hold off; grid on;
xlabel('Time (s)'); ylabel('Amplitude (output)');
title('Baseline: K=4 reduces a unit load to 0.2 output');
legend('Location','southeast');

%% Read and explain the observed balance
% At rest, -0.2-0.8+1=0. Feedback supplies most of the opposing input, but
% proportional action needs 0.2 output of residual deviation to create it.
% Integral action from P06 could remove a constant residual, while P07 reminds
% us that extra loop action must preserve stability margin.

%% Move one lever at a time
% Run experiment.m one section at a time. First move feedback gain with the
% same unit step load. Reset K to 4, then move disturbance frequency. Read the
% mechanism after each changed view before opening interactive.m.

%% Open the bounded interactive view
interactive;
