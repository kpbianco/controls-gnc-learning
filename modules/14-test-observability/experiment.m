%% P14 - Test Observability
%
% Guiding question:
% What inputs, observable effects, and failure modes matter when you test Observability?
%
% Run one section at a time. Read the model, inspect the baseline, move one
% lever, inspect its changed view, then reset before moving the next.

%% Read - a state direction must leave a distinct measurement history
% P13 exposed how an input direction spreads through state dynamics. P14
% follows the dual path from an initial state to a sensor:
%   d(position)/dt = rate
%   d(rate)/dt     = -0.5*rate
%   measurement    = positionSensorGain*position
% The normalized state scales are 1 m and 1 m/s. Predict once: can a sensor
% that directly measures only position reveal the initial rate over time?
sensorGain = 1;                       % sensor unit/m
observationWindowSec = 2;             % s
timeStepSec = 0.05;                   % s
measurePosition = true;
baseline = model(sensorGain,observationWindowSec,timeStepSec,measurePosition);

%% Visualize baseline - two initial states become distinguishable
figure('Name','P14 baseline candidate states');
subplot(2,1,1);
plot(baseline.timeSec,baseline.stateTrajectory(1,:), ...
    'LineWidth',1.8,'DisplayName','True position');
hold on;
plot(baseline.timeSec,baseline.alternativeStateTrajectory(1,:),'--', ...
    'LineWidth',1.6,'DisplayName','Position-offset candidate');
hold off; grid on;
xlabel('Time (s)'); ylabel('Position (m)');
title('The candidates retain a one-metre position separation');
legend('Location','best');
subplot(2,1,2);
plot(baseline.timeSec,baseline.stateTrajectory(2,:), ...
    'LineWidth',1.8,'DisplayName','True rate');
hold on;
plot(baseline.timeSec,baseline.alternativeStateTrajectory(2,:),'--', ...
    'LineWidth',1.6,'DisplayName','Candidate rate');
hold off; grid on;
xlabel('Time (s)'); ylabel('Rate (m/s)');
title('Both candidates have the same decaying rate');
legend('Location','best');

%% Changed view - inspect the sensor histories and information directions
figure('Name','P14 baseline measurement evidence');
subplot(2,1,1);
plot(baseline.timeSec,baseline.measurementHistory, ...
    'LineWidth',1.8,'DisplayName','True measurement');
hold on;
plot(baseline.timeSec,baseline.alternativeMeasurementHistory,'--', ...
    'LineWidth',1.6,'DisplayName','Offset-state measurement');
hold off; grid on;
xlabel('Time (s)'); ylabel('Sensor output (sensor unit)');
title('Position measurement separates the two candidate states');
legend('Location','best');
subplot(2,1,2);
plot(baseline.timeSec,baseline.scaledObservationMatrix(:,1), ...
    'LineWidth',1.8,'DisplayName','1 m initial-position effect');
hold on;
plot(baseline.timeSec,baseline.scaledObservationMatrix(:,2),'--', ...
    'LineWidth',1.6,'DisplayName','1 m/s initial-rate effect');
hold off; grid on;
xlabel('Time (s)'); ylabel('Output effect (sensor unit)');
title('Rate becomes visible through its accumulated position effect');
legend('Location','best');
fprintf(['Baseline metrics: rank %d of 2; scaled sigma_min %.6f sensor unit; ' ...
    'condition %.3f; state error %.3g; output separation RMS %.3f sensor unit.\n'], ...
    baseline.observabilityRank,baseline.minimumSingularValue, ...
    baseline.observabilityConditionNumber,baseline.initialStateErrorNorm, ...
    baseline.outputDifferenceRmsSensorUnits);

%% Read and explain the baseline mechanism
% The continuous rows [C;C*A] expose the direct position measurement and
% the rate direction carried into future position. For N+1 samples, the
% exact finite-window rows are [C;C*Ad;...;C*Ad^N]. Two independent columns
% make the noise-free initial state unique. Rank says distinct, not robust.

%% Sweep 1 - move only position-sensor sensitivity
sensorGains = [0.25 0.5 1 1.5 2];
observationWindowSec = 2;
gainMinimumSingularValue = zeros(size(sensorGains));
gainOutputSeparation = zeros(size(sensorGains));
gainNoiseAmplification = zeros(size(sensorGains));
for k = 1:numel(sensorGains)
    changed = model(sensorGains(k),observationWindowSec,0.05,true);
    gainMinimumSingularValue(k) = changed.minimumSingularValue;
    gainOutputSeparation(k) = changed.outputDifferenceRmsSensorUnits;
    gainNoiseAmplification(k) = changed.worstCaseStateErrorGain;
end
figure('Name','P14 sweep 1 - sensor sensitivity');
subplot(2,1,1);
plot(sensorGains,gainMinimumSingularValue,'o-','LineWidth',1.5); grid on;
xlabel('Position-sensor gain (sensor unit/m)');
ylabel('Scaled minimum singular value (sensor unit)');
title('Sensitivity scales the weakest visible state direction');
subplot(2,1,2);
semilogy(sensorGains,gainOutputSeparation,'s-','LineWidth',1.5, ...
    'DisplayName','Candidate separation');
hold on;
semilogy(sensorGains,gainNoiseAmplification,'d--','LineWidth',1.5, ...
    'DisplayName','Worst-case state-error gain');
hold off; grid on;
xlabel('Position-sensor gain (sensor unit/m)');
ylabel('Scaled diagnostic (log scale)');
title('More sensitivity separates outputs and reduces inverse noise gain');
legend('Location','best');

%% Read and explain sweep 1
% Only position-sensor gain moved. Every nonzero case remains rank two, but
% every observation row scales with gain. Halving gain halves both singular
% values and output separation, while doubling the worst-case inverse gain.

%% Sweep 2 - reset sensitivity and move only observation-window duration
sensorGain = 1;
observationWindowsSec = [0.1 0.25 0.5 1 2 4];
windowMinimumSingularValue = zeros(size(observationWindowsSec));
windowNoiseAmplification = zeros(size(observationWindowsSec));
windowConditionNumber = zeros(size(observationWindowsSec));
for k = 1:numel(observationWindowsSec)
    changed = model(sensorGain,observationWindowsSec(k),0.05,true);
    windowMinimumSingularValue(k) = changed.minimumSingularValue;
    windowNoiseAmplification(k) = changed.worstCaseStateErrorGain;
    windowConditionNumber(k) = changed.observabilityConditionNumber;
end
figure('Name','P14 sweep 2 - observation window');
subplot(2,1,1);
plot(observationWindowsSec,windowMinimumSingularValue,'o-', ...
    'LineWidth',1.5); grid on;
xlabel('Observation window (s)');
ylabel('Scaled minimum singular value (sensor unit)');
title('More position history accumulates evidence about initial rate');
subplot(2,1,2);
semilogy(observationWindowsSec,windowNoiseAmplification,'s-', ...
    'LineWidth',1.5,'DisplayName','Worst-case state-error gain');
hold on;
semilogy(observationWindowsSec,windowConditionNumber,'d--', ...
    'LineWidth',1.5,'DisplayName','Condition number');
hold off; grid on;
xlabel('Observation window (s)');
ylabel('Scaled diagnostic (log scale)');
title('A longer window reduces ambiguity without changing the sensor');
legend('Location','best');

%% Read and explain sweep 2
% Sensor gain reset to 1 sensor unit/m. Dynamics, initial states, and sample
% interval stay fixed. Later rows contain more accumulated initial-rate
% effect, so the weakest observation direction grows and inverse noise gain
% falls. The benefit eventually saturates as the rate decays.

%% Broken case - measure rate only, then recover position measurement
% The rate sensor is healthy and both candidates really do have the same
% rate. Their one-metre position offset never enters the rate equation, so
% every measured sample is identical. Rank falls to one and initial position
% is not unique. Restoring position measurement makes the offset visible.
broken = model(1,2,0.05,false);
recovered = model(1,2,0.05,true);
figure('Name','P14 broken measurement and recovery');
subplot(2,1,1);
plot(broken.timeSec,broken.measurementHistory, ...
    'LineWidth',1.8,'DisplayName','Broken true output');
hold on;
plot(broken.timeSec,broken.alternativeMeasurementHistory,'--', ...
    'LineWidth',1.6,'DisplayName','Broken offset-state output');
hold off; grid on;
xlabel('Time (s)'); ylabel('Rate-sensor output (sensor unit)');
title('Broken: two different positions produce identical rate histories');
legend('Location','best');
subplot(2,1,2);
plot(recovered.timeSec,recovered.measurementHistory, ...
    'LineWidth',1.8,'DisplayName','Recovered true output');
hold on;
plot(recovered.timeSec,recovered.alternativeMeasurementHistory,'--', ...
    'LineWidth',1.6,'DisplayName','Recovered offset-state output');
hold off; grid on;
xlabel('Time (s)'); ylabel('Position-sensor output (sensor unit)');
title('Recovered: position measurement exposes the hidden offset');
legend('Location','best');
fprintf(['Broken/recovered metrics: rank %d / %d; output separation RMS ' ...
    '%.3f / %.3f sensor unit; unique estimate %d / %d.\n'], ...
    broken.observabilityRank,recovered.observabilityRank, ...
    broken.outputDifferenceRmsSensorUnits, ...
    recovered.outputDifferenceRmsSensorUnits, ...
    broken.initialStateUnique,recovered.initialStateUnique);

%% Check and teach back
% Run run_checks. Then answer in two sentences: which measurement path
% reveals each state, what symptom exposes a hidden state direction, and why
% does full rank not guarantee a reliable estimate with an imperfect sensor?
run_checks;
