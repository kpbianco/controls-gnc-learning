%% P05 - Close a Loop with Proportional Control
% Guiding question:
% What inputs, observable effects, and failure modes matter when you close a Loop with Proportional Control?
%
% P04 separated a governing physical model from a useful approximation. P05
% keeps the plant deliberately simple so the new cause is visible: measured
% output is fed back and subtracted from the reference before every command.

%% Read - form one prediction
disp('What inputs, observable effects, and failure modes matter when you close a Loop with Proportional Control?');
disp('The controller applies u = Kp*(r-y) to a first-order plant.');
disp('Before plotting, predict whether Kp = 2 reaches a 1 m reference exactly.');

%% Visualize - establish the baseline before moving a lever
baseline = model(2,1,1,1,0,-1,5,0.01);
figure('Name','P05 first closed-loop baseline');
plot(baseline.t,baseline.referenceM*ones(size(baseline.t)),'k:', ...
    'LineWidth',1.2,'DisplayName','Reference r');
hold on;
plot(baseline.t,baseline.outputM,'LineWidth',1.5, ...
    'DisplayName','Measured output y');
hold off; grid on;
xlabel('Time (s)'); ylabel('Output position y (m)');
title('Negative feedback: fast response with finite steady error');
legend('Location','southeast');
disp('Observe the baseline first. Then use experiment.m for one controlled transition at a time.');

%% Move one lever - expose speed, error, and effort
disp('Open interactive.m. Move Kp once, reset, then move plant time constant once. Name the changed observable and invariant.');
interactive;

%% Check and teach back
disp('Run run_checks. Then explain why proportional control needs residual error and why feedback sign matters.');
