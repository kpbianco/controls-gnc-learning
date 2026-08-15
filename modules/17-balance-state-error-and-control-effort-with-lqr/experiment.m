%% P17 - Balance State Error and Control Effort with LQR
%
% Guiding question:
% What inputs, observable effects, and failure modes matter when you balance State Error and Control Effort with LQR?
%
% Run one section at a time: read, inspect the baseline, move one lever,
% inspect the changed view, reset, and then move the other lever.

%% Read - turn a tradeoff into state feedback
% P16 supplied an estimate x=[position; rate]. P17 chooses u=-K*x to
% minimize the accumulated normalized cost
%   J = dt*sum(q_p*(p/1 m)^2 + (v/(1 m/s))^2 + r*(u/(1 m/s^2))^2).
% Q says which state errors matter; R says how expensive command effort is.
% The common positive dt gives J seconds but does not change its minimizing
% K. The transparent Riccati iteration works backward from future cost to K.
% Predict once: if position error becomes more expensive while R is fixed,
% should the cart move harder or more gently at the first sample?
positionErrorWeight = 4;       % dimensionless, q_p
controlEffortWeight = 1;       % dimensionless, r
actuatorEffectiveness = 1;     % fraction of commanded acceleration applied
initialPositionM = 1;          % m
simulationDurationSec = 12;    % s
timeStepSec = 0.02;            % s
baseline = model(positionErrorWeight,controlEffortWeight, ...
    actuatorEffectiveness,initialPositionM,simulationDurationSec,timeStepSec);

%% Visualize baseline - state error returns to zero
figure('Name','P17 baseline state regulation');
subplot(2,1,1);
plot(baseline.timeSec,baseline.positionErrorM,'b-', ...
    'LineWidth',1.8,'DisplayName','Position error');
hold on;
yline(baseline.positionToleranceM,'k:','2% position band');
yline(-baseline.positionToleranceM,'k:');
hold off; grid on;
xlabel('Time (s)'); ylabel('Position error (m)');
title('LQR drives the estimated state toward the origin');
legend('Location','best');
subplot(2,1,2);
plot(baseline.timeSec,baseline.rateErrorMPerSec,'Color',[0.1 0.55 0.3], ...
    'LineWidth',1.8);
grid on; xlabel('Time (s)'); ylabel('Rate error (m/s)');
title('Rate changes first, then settles with position');

%% Changed view - see the effort paired with that response
figure('Name','P17 baseline control effort');
plot(baseline.timeSec,baseline.commandedAccelerationMPerSec2,'r-', ...
    'LineWidth',1.8,'DisplayName','Commanded acceleration');
hold on;
plot(baseline.timeSec,baseline.appliedAccelerationMPerSec2,'k--', ...
    'LineWidth',1.2,'DisplayName','Applied acceleration');
hold off; grid on;
xlabel('Time (s)'); ylabel('Acceleration (m/s^2)');
title('Nominal actuator applies the command used in the cost');
legend('Location','best');
fprintf(['Baseline: K=[%.4f %.4f], spectral radius %.5f, ' ...
    'settling %.2f s, position ISE %.3f m^2 s, effort integral ' ...
    '%.3f m^2/s^3, peak command %.3f m/s^2.\n'], ...
    baseline.feedbackGain(1),baseline.feedbackGain(2), ...
    baseline.nominalSpectralRadius,baseline.settlingTimeSec, ...
    baseline.positionIntegralSquaredM2Sec, ...
    baseline.commandedEffortIntegralM2PerSec3, ...
    baseline.peakCommandedAccelerationMPerSec2);

%% Sweep 1 - move only the position-error weight
positionErrorWeightValues = [0 0.25 1 4 16];
positionGains = zeros(size(positionErrorWeightValues));
positionIntegralSquaredM2Sec = zeros(size(positionErrorWeightValues));
commandEnergyM2PerSec3 = zeros(size(positionErrorWeightValues));
for k = 1:numel(positionErrorWeightValues)
    changed = model(positionErrorWeightValues(k),1,1,1,12,0.02);
    positionGains(k) = changed.feedbackGain(1);
    positionIntegralSquaredM2Sec(k) = ...
        changed.positionIntegralSquaredM2Sec;
    commandEnergyM2PerSec3(k) = ...
        changed.commandedEffortIntegralM2PerSec3;
end
figure('Name','P17 position-weight sweep');
subplot(2,1,1);
plot(positionErrorWeightValues,positionGains,'o-', ...
    'LineWidth',1.8);
grid on; xlabel('Position-error weight q_p (dimensionless)');
ylabel('Position feedback gain (1/s^2)');
title('Making position error expensive raises its feedback gain');
subplot(2,1,2);
yyaxis left;
plot(positionErrorWeightValues,positionIntegralSquaredM2Sec,'s-', ...
    'LineWidth',1.8);
ylabel('Position integral squared error (m^2 s)');
yyaxis right;
plot(positionErrorWeightValues,commandEnergyM2PerSec3,'d--', ...
    'LineWidth',1.8);
ylabel('Squared-command effort integral (m^2/s^3)');
grid on; xlabel('Position-error weight q_p (dimensionless)');
title('Less position error is purchased with more command effort');

%% Read and explain sweep 1 - Q changes what error is expensive
% Every run resets R, actuator authority, initial state, duration, and step.
% Increasing q_p makes future position error contribute more to J, so the
% Riccati solution raises position feedback. The zero-q_p endpoint is a
% limiting case: with zero initial rate, position costs nothing and K_p=0,
% so an offset can remain even though the arithmetic is well formed.

%% Sweep 2 - reset Q and move only the control-effort weight
controlEffortWeightValues = [0.1 0.25 1 4 10];
peakCommandMPerSec2 = zeros(size(controlEffortWeightValues));
settlingTimeSec = zeros(size(controlEffortWeightValues));
commandEnergyForEffortSweepM2PerSec3 = ...
    zeros(size(controlEffortWeightValues));
for k = 1:numel(controlEffortWeightValues)
    changed = model(4,controlEffortWeightValues(k),1,1,12,0.02);
    peakCommandMPerSec2(k) = ...
        changed.peakCommandedAccelerationMPerSec2;
    settlingTimeSec(k) = changed.settlingTimeSec;
    commandEnergyForEffortSweepM2PerSec3(k) = ...
        changed.commandedEffortIntegralM2PerSec3;
end
figure('Name','P17 effort-weight sweep');
subplot(2,1,1);
plot(controlEffortWeightValues,peakCommandMPerSec2,'o-', ...
    'LineWidth',1.8);
set(gca,'XScale','log'); grid on;
xlabel('Control-effort weight r (dimensionless)');
ylabel('Peak command magnitude (m/s^2)');
title('Making control expensive lowers the demanded acceleration');
subplot(2,1,2);
yyaxis left;
plot(controlEffortWeightValues,settlingTimeSec,'s-', ...
    'LineWidth',1.8);
ylabel('Settling time (s)');
yyaxis right;
plot(controlEffortWeightValues, ...
    commandEnergyForEffortSweepM2PerSec3,'d--','LineWidth',1.8);
ylabel('Squared-command effort integral (m^2/s^3)');
set(gca,'XScale','log'); grid on;
xlabel('Control-effort weight r (dimensionless)');
title('Gentler commands spend less effort and settle more slowly');

%% Read and explain sweep 2 - R prices the input
% Q and the initial state have returned to baseline. Increasing r enlarges
% the scalar denominator R+B'*P*B in K, so both gains and the command fall.
% LQR does not promise the smallest error and smallest effort separately;
% it minimizes their declared weighted sum for the model it was given.

%% Broken case - design for an actuator that is disconnected
broken = model(4,1,0,1,12,0.02);
recovered = model(4,1,1,1,12,0.02);
figure('Name','P17 broken actuator-assumption case');
subplot(2,1,1);
plot(broken.timeSec,broken.positionErrorM,'b-', ...
    'LineWidth',1.8,'DisplayName','Position error');
grid on; xlabel('Time (s)'); ylabel('Position error (m)');
title('Broken symptom: disconnected actuator leaves error unchanged');
legend('Location','best');
subplot(2,1,2);
plot(broken.timeSec,broken.commandedAccelerationMPerSec2,'r-', ...
    'LineWidth',1.8,'DisplayName','Commanded acceleration');
hold on;
plot(broken.timeSec,broken.appliedAccelerationMPerSec2,'k--', ...
    'LineWidth',1.4,'DisplayName','Applied acceleration');
hold off; grid on;
xlabel('Time (s)'); ylabel('Acceleration (m/s^2)');
title('The optimal command cannot create missing control authority');
legend('Location','best');
fprintf(['Broken actuator: final position error %.3f m, commanded effort ' ...
    'integral %.3f m^2/s^3, applied effort integral %.3f m^2/s^3. ' ...
    'Recovered final error %.6f m.\n'],broken.positionErrorM(end), ...
    broken.commandedEffortIntegralM2PerSec3, ...
    broken.appliedEffortIntegralM2PerSec3,recovered.positionErrorM(end));

%% Read and explain the broken mechanism
% K was designed with P16's nominal B, which assumes full actuator authority.
% Setting actual effectiveness to zero violates that governing model. The
% controller keeps requesting acceleration from the unchanged state, but
% applied acceleration is zero. LQR optimality cannot repair lost
% controllability. A fresh nominal call exactly recovers the baseline.

%% Check and teach back
% Clear a generic run_checks cached from another module before dispatch.
clear run_checks;
run_checks;
% Then answer in two sentences: name Q, R, the state estimate, and actuator
% model; describe the visible error/effort tradeoff; explain the disconnect.
