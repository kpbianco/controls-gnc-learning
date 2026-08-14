%% P04 - Compare Linear and Nonlinear Pendulum Models
% Guiding question:
% What inputs, observable effects, and failure modes matter when you compare Linear and Nonlinear Pendulum Models?
%
% P03 connected a linear second-order equation to visible motion and pole
% locations. P04 asks when that linear equation is a useful local model of
% a physical pendulum and when its small-angle assumption becomes visible.

%% Read - form one prediction
disp('What inputs, observable effects, and failure modes matter when you compare Linear and Nonlinear Pendulum Models?');
disp('The nonlinear restoring term is sin(theta); the linear model substitutes theta.');
disp('Before plotting, predict whether the models stay close after a 20 degree release.');

%% Visualize - establish the baseline before moving a lever
baseline = model(20,0,1,0.02,12,0.01);
figure('Name','P04 first baseline');
plot(baseline.t,baseline.linearAngleDeg,'--','LineWidth',1.3, ...
    'DisplayName','Linear model');
hold on;
plot(baseline.t,baseline.nonlinearAngleDeg,'LineWidth',1.5, ...
    'DisplayName','Nonlinear model');
hold off; grid on;
xlabel('Time (s)'); ylabel('Angle theta (deg)');
title('A 20 degree release: similar predictions, slowly accumulating phase error');
legend('Location','northeast');
disp('Observe the baseline first. Then use experiment.m for one controlled transition at a time.');

%% Move one lever - compare the approximation where it is used
disp('Open interactive.m. Move release angle once, reset, then move length once. Name the changed observable and invariant.');
interactive;

%% Check and teach back
disp('Run run_checks. Then explain why the small-angle model fails gradually as release angle grows and how to recover agreement.');
