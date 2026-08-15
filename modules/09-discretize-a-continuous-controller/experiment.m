%% P09 - Discretize a Continuous Controller
%
% Guiding question:
% What inputs, observable effects, and failure modes matter when you discretize a Continuous Controller?
%
% Run one section at a time. Observe each changed view before reading its
% mechanism, and reset the first lever before moving the second.

%% Read - connect continuous feedback to sampled computation
% P08 treated feedback as continuously available. Here y'=-y+u remains a
% continuous plant, but a digital PI controller reads e=1-y every Ts seconds
% and holds u between updates. Predict whether sampling is more obvious in
% plant output or held controller effort.
samplePeriodSec = 0.05;               % Ts (s)
discretizationMethod = 'backward-euler';
tEnd = 12;                            % observation duration (s)
displayStepSec = 0.01;                % display grid only (s)
% Fixed Ki uses (1/s); natural frequency is reported in (rad/s).
baseline = model(samplePeriodSec,discretizationMethod,tEnd,displayStepSec);

%% Visualize baseline - continuous target and sampled-data output
figure('Name','P09 baseline output');
plot(baseline.t,baseline.continuousOutput,'k--','LineWidth',1.3, ...
    'DisplayName','Continuous PI target');
hold on;
plot(baseline.t,baseline.digitalOutput,'LineWidth',1.7, ...
    'DisplayName','Digital PI output');
plot(baseline.sampleTimes,baseline.digitalOutputSamples,'o', ...
    'MarkerSize',3,'DisplayName','Output at controller samples');
hold off; grid on;
xlabel('Time (s)'); ylabel('Plant output y (output)');
title('Baseline: backward Euler at Ts = 0.05 s follows the continuous target');
legend('Location','best');

%% Changed view - make the zero-order hold visible
figure('Name','P09 baseline held effort');
plot(baseline.t,baseline.continuousControl,'k--','LineWidth',1.3, ...
    'DisplayName','Continuous PI command');
hold on;
stairs(baseline.sampleTimes,baseline.controlSamples,'LineWidth',1.6, ...
    'DisplayName','Held digital command');
hold off; grid on;
xlabel('Time (s)'); ylabel('Control effort u (output)');
title('The controller command changes only at sample instants');
legend('Location','best');
fprintf(['Baseline metrics: Ts %.3f s, %.1f samples/natural period, ' ...
    'max gap %.4f output, overshoot %.2f%%, pole magnitude %.4f.\n'], ...
    baseline.samplePeriodSec,baseline.samplesPerNaturalPeriod, ...
    baseline.maximumAbsTrackingGap,baseline.overshootPercent, ...
    baseline.spectralRadius);

%% Read and explain the baseline mechanism
% The plant output stays smooth because y'=-y+u continues between samples.
% The command is a staircase because zero-order hold preserves u[k]. The exact
% held-plant transition is y_next=exp(-Ts)*y+(1-exp(-Ts))*u. At small Ts the
% discrete pole locations and trajectory remain close to the continuous target.

%% Sweep 1 - move only sample period
samplePeriodsSec = [0.02 0.05 0.1 0.2 0.4];
figure('Name','P09 sweep 1 - sample period'); hold on; grid on;
for k = 1:numel(samplePeriodsSec)
    changed = model(samplePeriodsSec(k),'backward-euler',8,0.01);
    plot(changed.t,changed.digitalOutput,'LineWidth',1.2, ...
        'DisplayName',sprintf('Ts=%.2f s, gap=%.3f, |p|max=%.3f', ...
        changed.samplePeriodSec,changed.maximumAbsTrackingGap, ...
        changed.spectralRadius));
end
plot(baseline.t,baseline.continuousOutput,'k--','LineWidth',1.3, ...
    'DisplayName','Continuous PI target');
xlabel('Time (s)'); ylabel('Plant output y (output)');
title('Sweep 1: fewer controller updates change the closed-loop trajectory');
legend('Location','best');

%% Changed view - sample-period metrics and units
sampleGap = zeros(size(samplePeriodsSec));
samplePoleMagnitude = zeros(size(samplePeriodsSec));
samplesPerPeriod = zeros(size(samplePeriodsSec));
for k = 1:numel(samplePeriodsSec)
    changed = model(samplePeriodsSec(k),'backward-euler',8,0.01);
    sampleGap(k) = changed.maximumAbsTrackingGap;
    samplePoleMagnitude(k) = changed.spectralRadius;
    samplesPerPeriod(k) = changed.samplesPerNaturalPeriod;
end
figure('Name','P09 sample-period sweep metrics');
subplot(2,1,1);
plot(samplePeriodsSec,sampleGap,'o-','LineWidth',1.4); grid on;
xlabel('Sample period Ts (s)'); ylabel('Maximum target gap (output)');
title('Coarser timing departs farther from the continuous target');
subplot(2,1,2);
plot(samplePeriodsSec,samplePoleMagnitude,'s-','LineWidth',1.4); grid on;
hold on; yline(1,'r:','Stability boundary'); hold off;
xlabel('Sample period Ts (s)'); ylabel('Maximum pole magnitude (dimensionless)');
title('Pole magnitude reports convergence or growth');

%% Read and explain sweep 1
% Only Ts moved; backward Euler, Kp=2, Ki=4 1/s, plant, reference, and horizon
% stayed fixed. Increasing Ts reduces samples per natural period. The digital
% controller sees less of the changing error, holds each command longer, and
% no longer approximates the continuous design as closely.

%% Sweep 2 - reset sample period and move only the integration rule
samplePeriodSec = 0.05;
discretizationMethods = {'forward-euler','backward-euler'};
figure('Name','P09 sweep 2 - discretization rule'); hold on; grid on;
for k = 1:numel(discretizationMethods)
    changed = model(samplePeriodSec,discretizationMethods{k},8,0.01);
    plot(changed.t,changed.digitalOutput,'LineWidth',1.5, ...
        'DisplayName',sprintf('%s, gap=%.4f output', ...
        discretizationMethods{k},changed.maximumAbsTrackingGap));
end
referenceCase = model(samplePeriodSec,'backward-euler',8,0.01);
plot(referenceCase.t,referenceCase.continuousOutput,'k--','LineWidth',1.3, ...
    'DisplayName','Continuous PI target');
xlabel('Time (s)'); ylabel('Plant output y (output)');
title('Sweep 2: current versus previous error changes integral timing');
legend('Location','best');

%% Changed view - compare held commands for the rule sweep
forwardCase = model(samplePeriodSec,'forward-euler',4,0.01);
backwardCase = model(samplePeriodSec,'backward-euler',4,0.01);
figure('Name','P09 rule sweep held effort');
stairs(forwardCase.sampleTimes,forwardCase.controlSamples,'LineWidth',1.4, ...
    'DisplayName','Forward Euler: previous error');
hold on;
stairs(backwardCase.sampleTimes,backwardCase.controlSamples,'LineWidth',1.4, ...
    'DisplayName','Backward Euler: current error');
hold off; grid on;
xlabel('Time (s)'); ylabel('Held control effort u (output)');
title('The rule changes when sampled error enters controller memory');
legend('Location','best');

%% Read and explain sweep 2
% Ts reset to 0.05 s. Only the integration rule moved. Forward Euler uses its
% stored integral before adding e[k]; backward Euler adds e[k] before forming
% u[k]. Their first commands are therefore 2.0 and 2.2 output. As Ts shrinks,
% that one-sample distinction shrinks and both approach the continuous target.

%% Broken case - violate the resolved-sampling assumption
% The continuous PI target is stable, but forward Euler with Ts=0.8 s has a
% discrete closed-loop pole magnitude above one. Sparse updates and long holds
% produce growing oscillation. A smooth line through samples would hide the cause.
broken = model(0.8,'forward-euler',12,0.01);
recovered = model(0.05,'forward-euler',12,0.01);
figure('Name','P09 broken coarse sampling and recovery');
subplot(2,1,1);
plot(broken.t,broken.digitalOutput,'LineWidth',1.6, ...
    'DisplayName','Broken digital output');
hold on; plot(broken.t,broken.reference,'k:','DisplayName','Reference');
hold off; grid on;
xlabel('Time (s)'); ylabel('Plant output y (output)');
title(sprintf('Broken: Ts=0.8 s, maximum pole magnitude %.3f', ...
    broken.spectralRadius));
legend('Location','best');
subplot(2,1,2);
plot(recovered.t,recovered.digitalOutput,'LineWidth',1.6, ...
    'DisplayName','Recovered digital output');
hold on; plot(recovered.t,recovered.continuousOutput,'k--', ...
    'DisplayName','Continuous PI target'); hold off; grid on;
xlabel('Time (s)'); ylabel('Plant output y (output)');
title(sprintf('Recovery: Ts=0.05 s, maximum pole magnitude %.3f', ...
    recovered.spectralRadius));
legend('Location','best');
fprintf(['Broken pole magnitude %.4f and final error %.3f output; ' ...
    'recovered pole magnitude %.4f and final error %.6f output.\n'], ...
    broken.spectralRadius,broken.finalError,recovered.spectralRadius, ...
    recovered.finalError);

%% Read and explain recovery
% Discretization preserves a continuous design only within a timing regime.
% The explicit two-state pole calculation exposes the failed assumption before
% presentation choices can hide it. Reducing Ts gives the controller more than
% sixty samples per natural period, returns both poles inside the unit circle,
% and restores convergence without changing the continuous PI gains.
