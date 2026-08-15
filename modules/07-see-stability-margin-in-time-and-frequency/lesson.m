%% P07 - See Stability Margin in Time and Frequency
% Guiding question:
% What inputs, observable effects, and failure modes matter when you see Stability Margin in Time and Frequency?
%
% P06 made controller terms visible. P07 keeps a transparent feedback loop
% and asks how much gain or actuator lag it can tolerate before oscillations
% stop decaying.

%% Read - make one prediction before the baseline
disp('What inputs, observable effects, and failure modes matter when you see Stability Margin in Time and Frequency?');
disp('The same loop will be shown as a step response and as open-loop magnitude and phase.');
disp('Before plotting, predict what extra actuator lag does to phase margin and overshoot.');

%% Visualize - establish the time baseline
baseline = model(1,0.2,20,0.01);
figure('Name','P07 first stability-margin baseline');
plot(baseline.t,baseline.reference*ones(size(baseline.t)),'k:', ...
    'LineWidth',1.2,'DisplayName','Reference r');
hold on;
plot(baseline.t,baseline.output,'LineWidth',1.5, ...
    'DisplayName','Output y');
hold off; grid on;
xlabel('Time (s)'); ylabel('Output y (normalized)');
title('Baseline: margins are positive and oscillations decay');
legend('Location','southeast');
fprintf(['Baseline: phase margin %.2f deg, gain margin %.2f dB, ' ...
    'overshoot %.3f normalized.\n'],baseline.phaseMarginDeg, ...
    baseline.gainMarginDb,baseline.overshoot);
disp('Observe the time response first. Run experiment.m one section at a time to reveal the matching frequency view.');

%% Move one lever - compare loop gain and actuator lag
disp('Open interactive.m. Move loop gain once, reset, then move actuator lag once. Name the changed margin and time symptom after each move.');
interactive;

%% Check and teach back
disp('Run run_checks. Then connect gain crossover, phase margin, overshoot, the broken lag assumption, and recovery.');
