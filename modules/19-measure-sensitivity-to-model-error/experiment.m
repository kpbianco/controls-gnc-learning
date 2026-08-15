%% Read: model error is a parameter change with an observable consequence
% P18 combined a nominal feedforward command with error-driven feedback.
% P19 keeps that controller fixed, then asks whether the real speed plant
% has the actuator effectiveness b and drag a used by its nominal predictor:
%
%   u[k] = (a0/b0)*r[k] + K*(r[k]-v[k])
%   v[k+1] = exp(-a*dt)*v[k] + (b/a)*(1-exp(-a*dt))*u[k]
%
% u[k] is held between samples. A finite sensitivity is delta output divided by a fractional parameter
% change; its small-change limit is the local derivative used below.

%% Make one prediction before the baseline
% If the actual actuator is 20 percent weaker than the nominal model, will
% measured steady speed sit above or below the model prediction?

%% Visualize the deterministic baseline
baseline = model(1,1,1,1,10,0.02);
fprintf(['Baseline: prediction-gap RMSE %.4f m/s, actual pole %.4f, ' ...
    'gain sensitivity %.3f and drag sensitivity %.3f m/s per fraction.\n'], ...
    baseline.predictionGapRmseMPerSec,baseline.actualClosedLoopPole, ...
    baseline.actuatorGainSensitivityMPerSecPerFraction, ...
    baseline.dragSensitivityMPerSecPerFraction);

figure('Name','P19 baseline prediction and measurement');
subplot(2,1,1);
plot(baseline.timeSec,baseline.referenceSpeed,'k:','LineWidth',1.5, ...
    'DisplayName','Reference speed');
hold on;
plot(baseline.timeSec,baseline.predictedSpeedMPerSec,'b--', ...
    'LineWidth',1.7,'DisplayName','Nominal prediction');
plot(baseline.timeSec,baseline.actualSpeedMPerSec,'m-', ...
    'LineWidth',1.5,'DisplayName','Actual speed');
hold off; grid on;
xlabel('Time (s)'); ylabel('Speed (m/s)');
title('Baseline: nominal and actual parameters agree');
legend('Location','best');
subplot(2,1,2);
plot(baseline.timeSec,baseline.speedPredictionGapMPerSec,'r-', ...
    'LineWidth',1.7,'DisplayName','Actual minus predicted');
hold on; yline(0,'k:','HandleVisibility','off'); hold off; grid on;
xlabel('Time (s)'); ylabel('Prediction gap (m/s)');
title('A matched model has zero prediction gap');
legend('Location','best');

figure('Name','P19 baseline command comparison');
plot(baseline.timeSec,baseline.nominalTotalCommandMPerSec2,'b--', ...
    'LineWidth',1.7,'DisplayName','Command predicted by model');
hold on;
plot(baseline.timeSec,baseline.actualTotalCommandMPerSec2,'m-', ...
    'LineWidth',1.5,'DisplayName','Command used on actual plant');
plot(baseline.timeSec,baseline.actualFeedbackCommandMPerSec2,'r:', ...
    'LineWidth',1.6,'DisplayName','Actual feedback correction');
hold off; grid on;
xlabel('Time (s)'); ylabel('Acceleration command (m/s^2)');
title('Model error changes the correction requested from feedback');
legend('Location','best');

%% Move lever 1: sweep only actuator effectiveness
% Drag ratio, sign, reference, duration, and grid reset every run. The
% changed view differentiates steady output with respect to fractional gain
% error, so it shows the local slope at each operating ratio.
actuatorGainRatioValues = [0.6 0.8 1 1.2 1.4];
actuatorSteadySpeedMPerSec = zeros(size(actuatorGainRatioValues));
actuatorGapRmseMPerSec = zeros(size(actuatorGainRatioValues));
actuatorLocalSensitivityMPerSecPerFraction = ...
    zeros(size(actuatorGainRatioValues));
for k = 1:numel(actuatorGainRatioValues)
    changed = model(actuatorGainRatioValues(k),1,1,1,10,0.02);
    assert(changed.dragRatio == 1 && changed.actuatorSign == 1 && ...
        changed.referenceSpeedMPerSec == 1 && ...
        changed.simulationDurationSec == 10 && ...
        changed.timeStepSec == 0.02, ...
        'Actuator sweep changed a non-swept input.');
    actuatorSteadySpeedMPerSec(k) = changed.actualSteadyStateSpeedMPerSec;
    actuatorGapRmseMPerSec(k) = changed.predictionGapRmseMPerSec;
    actuatorLocalSensitivityMPerSecPerFraction(k) = ...
        changed.actuatorGainSensitivityMPerSecPerFraction;
end
figure('Name','P19 actuator-gain model-error sweep');
subplot(3,1,1);
plot(actuatorGainRatioValues,actuatorSteadySpeedMPerSec,'o-', ...
    'LineWidth',1.7);
hold on; yline(1,'k:','DisplayName','Nominal prediction'); hold off; grid on;
xlabel('Actual / nominal actuator gain (dimensionless)');
ylabel('Steady speed (m/s)');
title('Sweep 1 changed view: actuator error shifts the measured speed');
subplot(3,1,2);
plot(actuatorGainRatioValues,actuatorGapRmseMPerSec,'s-', ...
    'LineWidth',1.7);
grid on;
xlabel('Actual / nominal actuator gain (dimensionless)');
ylabel('Prediction-gap RMSE (m/s)');
title('Raw discrepancy is zero only for the matched model');
subplot(3,1,3);
plot(actuatorGainRatioValues, ...
    actuatorLocalSensitivityMPerSecPerFraction,'d-','LineWidth',1.7);
grid on;
xlabel('Actual / nominal actuator gain (dimensionless)');
ylabel('Local sensitivity (m/s per fraction)');
title('Local slope per fractional actuator-gain error');

%% Explain lever 1 from the equilibrium quotient
% At steady state v=b*(a0/b0+K)*r/(a+b*K). At the nominal point, the local
% linearization has slope 0.4 m/s per unit fractional actuator-gain change.
% Feedback attenuates the open-loop one-for-one gain sensitivity; it does
% not make model error disappear.

%% Reset, then move lever 2: sweep only drag
% Actuator ratio and sign return to one. The same reference and controller
% isolate how an incorrect loss model changes measured steady speed.
dragRatioValues = [0.5 0.75 1 1.5 2];
dragSteadySpeedMPerSec = zeros(size(dragRatioValues));
dragGapRmseMPerSec = zeros(size(dragRatioValues));
dragLocalSensitivityMPerSecPerFraction = zeros(size(dragRatioValues));
for k = 1:numel(dragRatioValues)
    changed = model(1,dragRatioValues(k),1,1,10,0.02);
    assert(changed.actuatorGainRatio == 1 && changed.actuatorSign == 1 && ...
        changed.referenceSpeedMPerSec == 1 && ...
        changed.simulationDurationSec == 10 && ...
        changed.timeStepSec == 0.02, ...
        'Drag sweep changed a non-swept input.');
    dragSteadySpeedMPerSec(k) = changed.actualSteadyStateSpeedMPerSec;
    dragGapRmseMPerSec(k) = changed.predictionGapRmseMPerSec;
    dragLocalSensitivityMPerSecPerFraction(k) = ...
        changed.dragSensitivityMPerSecPerFraction;
end
figure('Name','P19 drag model-error sweep');
subplot(3,1,1);
plot(dragRatioValues,dragSteadySpeedMPerSec,'o-','LineWidth',1.7);
hold on; yline(1,'k:','DisplayName','Nominal prediction'); hold off; grid on;
xlabel('Actual / nominal drag (dimensionless)');
ylabel('Steady speed (m/s)');
title('Sweep 2 changed view: extra drag lowers measured speed');
subplot(3,1,2);
plot(dragRatioValues,dragGapRmseMPerSec,'s-','LineWidth',1.7, ...
    'DisplayName','Prediction-gap RMSE');
grid on;
xlabel('Actual / nominal drag (dimensionless)');
ylabel('Prediction-gap RMSE (m/s)');
title('Raw discrepancy is zero only for the matched model');
subplot(3,1,3);
plot(dragRatioValues,dragLocalSensitivityMPerSecPerFraction, ...
    'd-','LineWidth',1.7);
grid on;
xlabel('Actual / nominal drag (dimensionless)');
ylabel('Local sensitivity (m/s per fraction)');
title('The sensitivity sign identifies the direction of the effect');

%% Explain lever 2 from the same mechanism
% Drag enters the denominator. More drag therefore creates a negative speed
% sensitivity, while more actuator effectiveness creates a positive one.
% The signs are physical information, not plot decoration.

%% Deliberately broken case: reverse the actuator sign
% Feedback assumes positive command raises speed. Reversing that convention
% makes a positive tracking error command the plant farther from reference.
broken = model(1,1,-1,1,10,0.02);
recovered = model(1,1,1,1,10,0.02);
assert(isequaln(recovered,baseline), ...
    'Restoring actuator polarity must recover the exact baseline.');
figure('Name','P19 broken actuator sign');
subplot(2,1,1);
plot(broken.timeSec,broken.predictedSpeedMPerSec,'b--','LineWidth',1.7, ...
    'DisplayName','Nominal prediction');
hold on;
plot(broken.timeSec,broken.actualSpeedMPerSec,'r-','LineWidth',1.7, ...
    'DisplayName','Actual speed with reversed actuator');
hold off; grid on;
xlabel('Time (s)'); ylabel('Speed (m/s)');
title(sprintf('Broken sign: pole magnitude %.3f exceeds one', ...
    abs(broken.actualClosedLoopPole)));
legend('Location','best');
subplot(2,1,2);
plot(broken.timeSec,broken.actualTotalCommandMPerSec2,'m-', ...
    'LineWidth',1.7,'DisplayName','Actual command');
grid on; xlabel('Time (s)'); ylabel('Acceleration command (m/s^2)');
title('Correction reinforces the error instead of opposing it');
legend('Location','best');

%% Check, recover, and teach back
run_checks;
% Teach back in exactly two sentences: name the two uncertain parameters and
% the observable used to measure each sensitivity. Then explain why the
% reversed-sign pole is a failed assumption, not merely a large model error.
