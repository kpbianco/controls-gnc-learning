%% P03 - Relate Poles to Visible Motion
% Guiding question:
% What inputs, observable effects, and failure modes matter when you relate Poles to Visible Motion?
%
% P02 showed that a first-order pole at -1/tau creates exponential
% settling. P03 keeps that exponential mechanism and adds an imaginary
% coordinate so the state can reverse direction repeatedly.

%% Read - form one prediction
disp('What inputs, observable effects, and failure modes matter when you relate Poles to Visible Motion?');
disp('For p = sigma +/- j*omega, sigma sets envelope growth or decay and omega sets cycle spacing.');
disp('Before plotting, predict the visible motion for sigma < 0 and omega > 0.');

%% Visualize - establish the baseline before moving a lever
baseline = model(-0.5,2,1,0,12,0.01);
figure('Name','P03 first baseline');
plot(baseline.t,baseline.position,'LineWidth',1.4,'DisplayName','Displacement x');
hold on;
plot(baseline.t,baseline.envelope,'--','DisplayName','Positive envelope');
plot(baseline.t,-baseline.envelope,'--','DisplayName','Negative envelope');
hold off; grid on;
xlabel('Time (s)'); ylabel('Displacement (m)');
title('Left-half-plane conjugate poles: oscillation inside a shrinking envelope');
legend('Location','northeast');
disp('Observe the baseline first. Then open experiment.m and run later sections one transition at a time.');

%% Move one lever - use the bounded stable interactive view
disp('Open interactive.m. Move sigma once, reset, then move omega once. Explain each changed view from the pole coordinates.');
interactive;

%% Check and teach back
disp('Run run_checks. Then explain how both pole coordinates map to motion and why the right-half-plane case grows.');
