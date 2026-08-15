%% P06 - Tune a PID by Observing Each Term
% Guiding question:
% What inputs, observable effects, and failure modes matter when you tune a PID by Observing Each Term?
%
% P05 made proportional error visible. P06 keeps that feedback loop and adds
% memory plus damping while a constant load makes their distinct jobs visible.

%% Read - make one prediction before the baseline
disp('What inputs, observable effects, and failure modes matter when you tune a PID by Observing Each Term?');
disp('A 1 kg carriage follows 1 m against a constant -1 N load.');
disp('Before plotting, predict which PID term must supply force after the error and velocity approach zero.');

%% Visualize - establish the baseline before moving a lever
baseline = model(4,1,3,-1,-1,20,0.01);
figure('Name','P06 first PID baseline');
plot(baseline.t,baseline.referenceM*ones(size(baseline.t)),'k:', ...
    'LineWidth',1.2,'DisplayName','Reference r');
hold on;
plot(baseline.t,baseline.positionM,'LineWidth',1.5, ...
    'DisplayName','Carriage position x');
hold off; grid on;
xlabel('Time (s)'); ylabel('Position x (m)');
title('PID baseline under a constant load');
legend('Location','southeast');
disp('Observe position first. Then run experiment.m one transition at a time to reveal P, I, and D.');

%% Move one lever - compare memory and damping
disp('Open interactive.m. Move Ki once, reset, then move Kd once. Name one changed observable and one invariant after each move.');
interactive;

%% Check and teach back
disp('Run run_checks. Then explain what each term observes, the tuning tradeoffs, and why the derivative sign must oppose velocity.');
