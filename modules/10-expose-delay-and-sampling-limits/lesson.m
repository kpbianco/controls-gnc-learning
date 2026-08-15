%% P10 - Expose Delay and Sampling Limits
% Guiding question:
% What inputs, observable effects, and failure modes matter when you expose Delay and Sampling Limits?
%
% P09 showed when a digital controller samples and holds. Now computation
% itself takes Td seconds. Predict which trace shows that latency first: the
% controller command or the plant output.

%% Read the two-piece feedback interval
% The plant remains y'=-y+u and the controller computes u=8*(1-y) every Ts.
% During Td the previous command remains applied. During Ts-Td the new command
% is applied. The plant evolves continuously through both exact pieces.

%% Visualize the deterministic baseline
baseline = model(0.05,0.01,4,0.005);
figure('Name','P10 lesson baseline');
plot(baseline.t,baseline.continuousOutput,'k--','LineWidth',1.3, ...
    'DisplayName','Immediate continuous P target');
hold on;
plot(baseline.t,baseline.sampledOutput,'LineWidth',1.7, ...
    'DisplayName','Sampled and delayed output');
stairs(baseline.t,baseline.appliedCommand,'LineWidth',1.2, ...
    'DisplayName','Applied command');
hold off; grid on;
xlabel('Time (s)'); ylabel('Amplitude (output)');
title('Baseline: the plant moves while a new command is computed');
legend('Location','best');

%% Read and explain the observed difference
% Sampling holds a correction for Ts. Computation delay keeps the older
% correction active for Td of that interval. The output stays continuous, but
% command timing changes the trajectory and the closed-loop pole locations.

%% Move one lever at a time
% Run experiment.m one section at a time. First hold Td at zero and move Ts.
% Then reset Ts to 0.1 s and move only Td. Read each mechanism before opening
% the next plot or the bounded interactive view.

%% Open the bounded interactive view
interactive;
