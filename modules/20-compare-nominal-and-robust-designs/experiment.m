%% Read: a design claim needs an operating point and an uncertainty set
% P19 used the transparent held-input speed plant
%
%   v[k+1] = alpha*v[k] + beta*u[k]
%   alpha = exp(-a*dt), beta = (b/a)*(1-exp(-a*dt)).
%
% P20 compares P19's model-matched feedforward-plus-P controller with a PI
% candidate chosen by finite worst-case enumeration. The declared design
% set contains positive actuator ratios 0.5:0.25:1.5 and drag ratios
% [0.5 0.75 1 1.5 2]. “Robust” means only what this comparison establishes.

%% Make one prediction before the baseline
% On the exactly matched plant, which design will have smaller 12-second
% tracking-error integral: nominal feedforward plus P, or robust PI?

%% Visualize the deterministic baseline
baseline = model(1,1,1,1,12,0.02);
fprintf(['Baseline: nominal/robust tracking ISE %.4f / %.4f m^2/s; ' ...
    'command effort %.3f / %.3f m^2/s^3.\n'], ...
    baseline.nominal.trackingIntegralM2PerSec, ...
    baseline.robust.trackingIntegralM2PerSec, ...
    baseline.nominal.commandEffortIntegralM2PerSec3, ...
    baseline.robust.commandEffortIntegralM2PerSec3);
fprintf(['Selected robust gains: Kp %.1f 1/s, Ki %.1f 1/s^2; ' ...
    'worst-grid ISE %.4f m^2/s under a %.1f m^2/s^3 effort limit.\n'], ...
    baseline.robustProportionalGainPerSec, ...
    baseline.robustIntegralGainPerSec2, ...
    baseline.designSelection.selectedWorstTrackingIntegralM2PerSec, ...
    baseline.designSelection.commandEffortLimitM2PerSec3);

figure('Name','P20 baseline speed and command');
subplot(2,1,1);
plot(baseline.timeSec,baseline.referenceSpeed,'k:','LineWidth',1.5, ...
    'DisplayName','Reference speed');
hold on;
plot(baseline.timeSec,baseline.nominal.speedMPerSec,'b-', ...
    'LineWidth',1.7,'DisplayName','Nominal design');
plot(baseline.timeSec,baseline.robust.speedMPerSec,'m--', ...
    'LineWidth',1.7,'DisplayName','Robust design');
hold off; grid on;
xlabel('Time (s)'); ylabel('Speed (m/s)');
title('Baseline: the matched-model design tracks faster');
legend('Location','best');
subplot(2,1,2);
plot(baseline.timeSec,baseline.nominal.totalCommandMPerSec2,'b-', ...
    'LineWidth',1.7,'DisplayName','Nominal command');
hold on;
plot(baseline.timeSec,baseline.robust.totalCommandMPerSec2,'m--', ...
    'LineWidth',1.7,'DisplayName','Robust command');
hold off; grid on;
xlabel('Time (s)'); ylabel('Acceleration command (m/s^2)');
title('Complementary view: the designs spend command differently');
legend('Location','best');

figure('Name','P20 baseline metric tradeoff');
subplot(1,2,1);
bar([baseline.nominal.trackingIntegralM2PerSec ...
    baseline.robust.trackingIntegralM2PerSec]);
set(gca,'XTickLabel',{'Nominal','Robust'}); grid on;
ylabel('Tracking ISE (m^2/s)');
title('Matched tracking cost');
subplot(1,2,2);
bar([baseline.nominal.commandEffortIntegralM2PerSec3 ...
    baseline.robust.commandEffortIntegralM2PerSec3]);
set(gca,'XTickLabel',{'Nominal','Robust'}); grid on;
ylabel('Command effort integral (m^2/s^3)');
title('Matched command cost');

%% Read the robust selection mechanism
% Twelve visible PI candidates are evaluated on 25 positive plant models.
% A candidate is feasible only if every analytic pole is inside the unit
% circle and worst command effort is at most 90 m^2/s^3. Among feasible
% candidates, the smallest worst 12-second tracking ISE wins; exact ties
% retain the first lower-Kp, then lower-Ki candidate in declared order. The
% effort claim uses a 1 m/s step and dt=0.02 s; other amplitudes are exploratory.

%% Move lever 1: sweep only actuator effectiveness
% Drag, sign, reference, duration, and grid reset on every call. Final error
% complements finite-time ISE: it shows what remains at the horizon.
actuatorGainRatioValues = [0.5 0.75 1 1.25 1.5];
nominalActuatorIseM2PerSec = zeros(size(actuatorGainRatioValues));
robustActuatorIseM2PerSec = zeros(size(actuatorGainRatioValues));
nominalActuatorFinalErrorMPerSec = zeros(size(actuatorGainRatioValues));
robustActuatorFinalErrorMPerSec = zeros(size(actuatorGainRatioValues));
for k = 1:numel(actuatorGainRatioValues)
    changed = model(actuatorGainRatioValues(k),1,1,1,12,0.02);
    assert(changed.dragRatio == 1 && changed.actuatorSign == 1 && ...
        changed.referenceSpeedMPerSec == 1 && ...
        changed.simulationDurationSec == 12 && ...
        changed.timeStepSec == 0.02, ...
        'Actuator sweep changed a non-swept input.');
    nominalActuatorIseM2PerSec(k) = ...
        changed.nominal.trackingIntegralM2PerSec;
    robustActuatorIseM2PerSec(k) = changed.robust.trackingIntegralM2PerSec;
    nominalActuatorFinalErrorMPerSec(k) = ...
        changed.nominal.finalAbsoluteTrackingErrorMPerSec;
    robustActuatorFinalErrorMPerSec(k) = ...
        changed.robust.finalAbsoluteTrackingErrorMPerSec;
end
figure('Name','P20 actuator-gain sweep');
subplot(2,1,1);
plot(actuatorGainRatioValues,nominalActuatorIseM2PerSec,'bo-', ...
    'LineWidth',1.7,'DisplayName','Nominal design');
hold on;
plot(actuatorGainRatioValues,robustActuatorIseM2PerSec,'ms--', ...
    'LineWidth',1.7,'DisplayName','Robust design');
hold off; grid on;
xlabel('Actual / nominal actuator gain (dimensionless)');
ylabel('Tracking ISE (m^2/s)');
title('Sweep 1 changed view: command effectiveness reshapes tracking');
legend('Location','best');
subplot(2,1,2);
plot(actuatorGainRatioValues,nominalActuatorFinalErrorMPerSec,'bo-', ...
    'LineWidth',1.7,'DisplayName','Nominal design');
hold on;
plot(actuatorGainRatioValues,robustActuatorFinalErrorMPerSec,'ms--', ...
    'LineWidth',1.7,'DisplayName','Robust design');
hold off; grid on;
xlabel('Actual / nominal actuator gain (dimensionless)');
ylabel('Final absolute tracking error (m/s)');
title('Integral action reduces the remaining positive-plant error');
legend('Location','best');

%% Explain lever 1 from command effectiveness and integral correction
% The fixed nominal feedforward is exact only at the modeled gain. PI does
% not know b, but accumulated error keeps changing its command. That reduces
% final error at weak and strong positive gains, at the cost of a slower
% matched transient and no claim beyond the tested positive range.

%% Reset, then move lever 2: sweep only drag
% Actuator gain and sign return to one. Reference, duration, and grid remain
% fixed so the changed view isolates loss rather than mixing uncertainties.
dragRatioValues = [0.5 0.75 1 1.5 2];
nominalDragIseM2PerSec = zeros(size(dragRatioValues));
robustDragIseM2PerSec = zeros(size(dragRatioValues));
nominalDragFinalErrorMPerSec = zeros(size(dragRatioValues));
robustDragFinalErrorMPerSec = zeros(size(dragRatioValues));
robustSteadyCommandMPerSec2 = zeros(size(dragRatioValues));
for k = 1:numel(dragRatioValues)
    changed = model(1,dragRatioValues(k),1,1,12,0.02);
    assert(changed.actuatorGainRatio == 1 && ...
        changed.actuatorSign == 1 && ...
        changed.referenceSpeedMPerSec == 1 && ...
        changed.simulationDurationSec == 12 && ...
        changed.timeStepSec == 0.02, ...
        'Drag sweep changed a non-swept input.');
    nominalDragIseM2PerSec(k) = changed.nominal.trackingIntegralM2PerSec;
    robustDragIseM2PerSec(k) = changed.robust.trackingIntegralM2PerSec;
    nominalDragFinalErrorMPerSec(k) = ...
        changed.nominal.finalAbsoluteTrackingErrorMPerSec;
    robustDragFinalErrorMPerSec(k) = ...
        changed.robust.finalAbsoluteTrackingErrorMPerSec;
    robustSteadyCommandMPerSec2(k) = ...
        changed.robust.steadyStateCommandMPerSec2;
end
figure('Name','P20 drag sweep');
subplot(3,1,1);
plot(dragRatioValues,nominalDragIseM2PerSec,'bo-', ...
    'LineWidth',1.7,'DisplayName','Nominal design');
hold on;
plot(dragRatioValues,robustDragIseM2PerSec,'ms--', ...
    'LineWidth',1.7,'DisplayName','Robust design');
hold off; grid on;
xlabel('Actual / nominal drag (dimensionless)');
ylabel('Tracking ISE (m^2/s)');
title('Sweep 2 changed view: loss changes finite-time tracking');
legend('Location','best');
subplot(3,1,2);
plot(dragRatioValues,nominalDragFinalErrorMPerSec,'bo-', ...
    'LineWidth',1.7,'DisplayName','Nominal design');
hold on;
plot(dragRatioValues,robustDragFinalErrorMPerSec,'ms--', ...
    'LineWidth',1.7,'DisplayName','Robust design');
hold off; grid on;
xlabel('Actual / nominal drag (dimensionless)');
ylabel('Final absolute tracking error (m/s)');
title('Finite-horizon error is distinct from the PI equilibrium limit');
legend('Location','best');
subplot(3,1,3);
plot(dragRatioValues,robustSteadyCommandMPerSec2,'kd-', ...
    'LineWidth',1.7);
grid on;
xlabel('Actual / nominal drag (dimensionless)');
ylabel('Required steady command (m/s^2)');
title('More drag requires proportionally more equilibrium command');

%% Explain lever 2 and inspect the declared worst corner
% Stable PI makes steady error zero on a positive plant, but a slow corner
% can retain error after 12 seconds. Worst-case means maximum over the named
% grid and metric, not that every individual run favors the robust design.
worstCorner = model(0.5,2,1,1,12,0.02);
figure('Name','P20 declared worst tracking corner');
plot(worstCorner.timeSec,worstCorner.referenceSpeed,'k:', ...
    'LineWidth',1.5,'DisplayName','Reference speed');
hold on;
plot(worstCorner.timeSec,worstCorner.nominal.speedMPerSec,'b-', ...
    'LineWidth',1.7,'DisplayName','Nominal design');
plot(worstCorner.timeSec,worstCorner.robust.speedMPerSec,'m--', ...
    'LineWidth',1.7,'DisplayName','Robust design');
hold off; grid on;
xlabel('Time (s)'); ylabel('Speed (m/s)');
title('Weak actuator plus high drag: robust has lower finite-grid ISE');
legend('Location','best');

%% Deliberately broken case: reverse actuator polarity
% The selection grid assumes b is positive. With b negative, positive
% tracking error commands motion in the wrong direction. Both analytic pole
% tests fail, and the bounded recurrence stops each diverging trace.
broken = model(1,1,-1,1,12,0.02);
recovered = model(1,1,1,1,12,0.02);
assert(isequaln(recovered,baseline), ...
    'Restoring positive polarity must recover the exact baseline.');
figure('Name','P20 broken actuator polarity');
subplot(2,1,1);
plot(broken.timeSec,broken.nominal.speedMPerSec,'b-', ...
    'LineWidth',1.7,'DisplayName','Nominal design');
hold on;
plot(broken.timeSec,broken.robust.speedMPerSec,'m--', ...
    'LineWidth',1.7,'DisplayName','Robust design');
hold off; grid on;
xlabel('Time (s)'); ylabel('Speed (m/s)');
title('Broken assumption: negative actuator effectiveness diverges');
legend('Location','best');
subplot(2,1,2);
bar([broken.nominal.closedLoopPoleMagnitude ...
    broken.robust.closedLoopPoleMagnitude]);
hold on; yline(1,'r:','Stability boundary'); hold off; grid on;
set(gca,'XTickLabel',{'Nominal','Robust'});
ylabel('Closed-loop pole magnitude (dimensionless)');
title('Both designs lie outside the unit-circle stability boundary');

%% Check, recover, and teach back
run_checks;
% Teach back in exactly two sentences: name actuator gain and drag, then
% compare matched ISE, worst-grid ISE, and command effort. State that the
% positive grid excludes reversed polarity and identify its symptom.
