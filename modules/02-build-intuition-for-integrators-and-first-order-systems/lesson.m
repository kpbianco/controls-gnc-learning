%% P02 - Build Intuition for Integrators and First-Order Systems
% Guiding question:
% What inputs, observable effects, and failure modes matter when you build Intuition for Integrators and First-Order Systems?
%
% P01 showed storage and dissipation acting together in a mass-spring-damper.
% P02 isolates two simpler building blocks: perfect accumulation and a
% single state that leaks toward equilibrium.

%% Read - form one prediction
disp('What inputs, observable effects, and failure modes matter when you build Intuition for Integrators and First-Order Systems?');
disp('Integrator: dx_I/dt = u. First order: tau*dy/dt + y = K*u.');
disp('Before plotting, predict which output can settle under a constant positive input.');

%% Visualize - work through one transition at a time
baseline = model(1,2,1,10,0.02);
figure('Name','P02 first baseline');
plot(baseline.t,baseline.integrator,'LineWidth',1.4,'DisplayName','Integrator x_I');
hold on;
plot(baseline.t,baseline.firstOrder,'LineWidth',1.4,'DisplayName','First-order y');
yline(baseline.firstOrderSteady,'--','K A');
hold off; grid on;
xlabel('Time (s)'); ylabel('Output (command for y; command s for x_I)');
title('Same constant input: accumulation versus settling');
legend('Location','best');
disp('Observe the baseline first. Then open experiment.m and run its later sections one at a time.');

%% Move one lever - open the bounded interactive view
disp('Open the interactive panel. Move amplitude, reset, then move tau. Explain the changed rate before combining controls.');
interactive;

%% Check and teach back
disp('Run run_checks. Then explain why one output ramps, why the other settles, and how a coarse Euler step can lie.');
