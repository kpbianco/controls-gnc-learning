%% P08 - Reject a Disturbance with Feedback
%
% Guiding question:
% What inputs, observable effects, and failure modes matter when you reject a Disturbance with Feedback?
%
% Run one section at a time. Observe each changed view before reading its
% mechanism, and reset the first lever before moving the second.

%% Read - connect P06 control action and P07 loop reserve
% The normalized plant is tau*y'=-y+u+d with tau=1 s. Proportional feedback
% uses u=-K*y_measured to hold a zero reference. For an honest sensor and a
% constant plant-input disturbance, y_ss=d/(1+K). Predict whether increasing K
% reduces output deviation, control effort, or both.
feedbackGain = 4;                    % K (dimensionless)
disturbanceAmplitude = 1;            % d amplitude (output)
disturbanceFrequencyRadPerSec = 0;   % zero selects a constant load; units rad/s
sensorBias = 0;                      % measurement bias (output)
tEnd = 12;                           % observation duration (s)
dt = 0.01;                           % requested calculation interval (s)
baseline = model(feedbackGain,disturbanceAmplitude, ...
    disturbanceFrequencyRadPerSec,sensorBias,tEnd,dt);

%% Visualize baseline - disturbance, output, and correction in time
figure('Name','P08 baseline time response');
subplot(2,1,1);
plot(baseline.t,baseline.disturbanceInput,'k--','LineWidth',1.2, ...
    'DisplayName','Plant-input disturbance d');
hold on;
plot(baseline.t,baseline.trueOutput,'LineWidth',1.6, ...
    'DisplayName','True output y');
yline(baseline.stepTrueOutput,':','DisplayName','Expected y_{ss}');
hold off; grid on;
xlabel('Time (s)'); ylabel('Amplitude (output)');
title('Baseline: feedback reduces a constant load disturbance');
legend('Location','southeast');
subplot(2,1,2);
plot(baseline.t,baseline.controlEffort,'LineWidth',1.5, ...
    'DisplayName','Control effort u');
hold on; yline(baseline.stepControlEffort,':', ...
    'DisplayName','Expected u_{ss}'); hold off; grid on;
xlabel('Time (s)'); ylabel('Control effort (output)');
title('The controller supplies the opposing input');
legend('Location','southeast');
fprintf(['Baseline metrics: y_ss %.3f output, u_ss %.3f output, ' ...
    'closed-loop time constant %.3f s, additional attenuation (dB) %.2f.\n'], ...
    baseline.stepTrueOutput,baseline.stepControlEffort, ...
    baseline.closedLoopTimeConstantSec,baseline.additionalAttenuationDb);

%% Changed view - exact disturbance path across frequency
figure('Name','P08 baseline frequency response');
subplot(2,1,1);
semilogx(baseline.omegaRadPerSec, ...
    baseline.openLoopDisturbanceMagnitude,'k--','LineWidth',1.2, ...
    'DisplayName','No feedback |Y/D|');
hold on;
semilogx(baseline.omegaRadPerSec, ...
    baseline.closedLoopDisturbanceMagnitude,'LineWidth',1.6, ...
    'DisplayName','With feedback |Y/D|');
hold off; grid on;
xlabel('Disturbance frequency (rad/s)');
ylabel('Output/disturbance magnitude (dimensionless)');
title('Absolute response: plant dynamics and feedback both attenuate');
legend('Location','southwest');
subplot(2,1,2);
additionalRatio = baseline.closedLoopDisturbanceMagnitude./ ...
    baseline.openLoopDisturbanceMagnitude;
semilogx(baseline.omegaRadPerSec,additionalRatio,'LineWidth',1.6);
grid on; ylim([0 1.05]);
xlabel('Disturbance frequency (rad/s)');
ylabel('With-feedback / no-feedback ratio');
title('Feedback adds strong low-frequency rejection, little at high frequency');

%% Read and explain the baseline mechanism
% The constant load is reduced from 1 output to 0.2 output because K=4 makes
% 1/(1+K)=0.2. The controller holds u=-0.8 output, leaving -y+u+d=0.
% Proportional action needs the residual y to command that holding effort. P06
% showed how integral action can remove a constant residual; P07 showed why more
% loop action must keep adequate margin.

%% Sweep 1 - move only feedback gain
feedbackGains = [0 1 4 9];
figure('Name','P08 sweep 1 - feedback gain'); hold on; grid on;
for k = 1:numel(feedbackGains)
    sweepDt = min(0.01,0.08/(1+feedbackGains(k)));
    changed = model(feedbackGains(k),disturbanceAmplitude,0,0,8,sweepDt);
    plot(changed.t,changed.trueOutput,'LineWidth',1.3, ...
        'DisplayName',sprintf('K = %.0f, y_{ss} = %.2f, |u_{ss}| = %.2f', ...
        feedbackGains(k),changed.stepTrueOutput,abs(changed.stepControlEffort)));
end
xlabel('Time (s)'); ylabel('True output y (output)');
title('Sweep 1: more gain rejects more load and spends more effort');
legend('Location','southeast');

%% Read and explain sweep 1
% Only K moved; the load remained a unit step at the plant input and the sensor
% remained honest. Larger K makes y_ss=1/(1+K) smaller and the response faster,
% while |u_ss|=K/(1+K) approaches the full disturbance amplitude.

%% Sweep 2 - reset gain and move only disturbance frequency
feedbackGain = 4;
disturbanceFrequenciesRadPerSec = [0.2 1 5 15];
figure('Name','P08 sweep 2 - disturbance frequency'); hold on; grid on;
for k = 1:numel(disturbanceFrequenciesRadPerSec)
    omega = disturbanceFrequenciesRadPerSec(k);
    sweepDt = min(0.01,0.08/max(1+feedbackGain,omega));
    changed = model(feedbackGain,disturbanceAmplitude,omega,0,16,sweepDt);
    plot(changed.t,changed.trueOutput,'LineWidth',1.2, ...
        'DisplayName',sprintf('omega = %.1f rad/s, |Y| = %.3f output', ...
        omega,changed.theoreticalOutputAmplitude));
end
xlabel('Time (s)'); ylabel('True output y (output)');
title('Sweep 2: the plant filters faster disturbances');
legend('Location','best');

%% Changed view - separate absolute attenuation from feedback benefit
frequencyCases = zeros(size(disturbanceFrequenciesRadPerSec));
feedbackBenefit = zeros(size(disturbanceFrequenciesRadPerSec));
for k = 1:numel(disturbanceFrequenciesRadPerSec)
    changed = model(feedbackGain,disturbanceAmplitude, ...
        disturbanceFrequenciesRadPerSec(k),0,4,0.005);
    frequencyCases(k) = changed.theoreticalOutputAmplitude;
    feedbackBenefit(k) = changed.feedbackRejectionRatio;
end
figure('Name','P08 frequency sweep metrics');
yyaxis left;
semilogx(disturbanceFrequenciesRadPerSec,frequencyCases,'o-', ...
    'LineWidth',1.4);
ylabel('Absolute output amplitude (output)');
yyaxis right;
semilogx(disturbanceFrequenciesRadPerSec,feedbackBenefit,'s-', ...
    'LineWidth',1.4);
ylabel('With-feedback / no-feedback ratio');
xlabel('Disturbance frequency (rad/s)'); grid on;
title('Fast loads are smaller, but feedback adds less of their attenuation');

%% Read and explain sweep 2
% K reset to 4. Only disturbance frequency moved. Absolute output gets smaller
% because the first-order plant cannot follow a fast load. But the relative
% with-feedback/no-feedback ratio approaches one: the plant, not feedback,
% supplies most of the high-frequency attenuation.

%% Broken case - treat sensor bias as a plant-input disturbance
% The violated assumption is that measured output equals true output. With no
% physical load but a +0.5 output sensor bias, K=9 drives true output toward
% -0.45 output so the measured output appears to be only +0.05 output.
broken = model(9,0,0,0.5,8,0.005);
recovered = model(9,0,0,0,8,0.005);
figure('Name','P08 broken sensor-bias assumption and recovery');
subplot(2,1,1);
plot(broken.t,broken.trueOutput,'LineWidth',1.5, ...
    'DisplayName','True output y');
hold on;
plot(broken.t,broken.measuredOutput,'--','LineWidth',1.5, ...
    'DisplayName','Biased measurement y_m');
yline(0,'k:','Zero reference'); hold off; grid on;
xlabel('Time (s)'); ylabel('Output (output)');
title('Broken assumption: a small measurement hides a large true error');
legend('Location','best');
subplot(2,1,2);
plot(recovered.t,recovered.trueOutput,'LineWidth',1.5, ...
    'DisplayName','True output after sensor correction');
hold on; yline(0,'k:','Zero reference'); hold off; grid on;
xlabel('Time (s)'); ylabel('True output y (output)');
title('Recovery: validate and remove bias before changing gain');
legend('Location','best');
fprintf(['Broken steady values: true y %.3f, measured y_m %.3f, u %.3f output. ' ...
    'Recovered true y %.3f output.\n'],broken.stepTrueOutput, ...
    broken.stepMeasuredOutput,broken.stepControlEffort,recovered.stepTrueOutput);

%% Read and explain recovery
% Feedback rejects inputs according to where they enter. A plant-input load is
% attenuated in true output. A measurement bias is instead converted into real
% motion as the loop tries to zero the wrong signal. More gain makes the biased
% measurement smaller while true output approaches minus the bias. Sensor
% validation and correction recover the intended zero-output condition.
