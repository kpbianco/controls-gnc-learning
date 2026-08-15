%% Read: one command can contain two different jobs
% The planned input u_plan generates a dynamically feasible reference for
% the damped cart. Feedforward anticipates that known input. Feedback reacts
% to tracking error e=x_ref-x. The mixer is
%
%   u_cmd = s_ff*alpha*u_plan + beta*[Kp Kv]*e
%
% where alpha and beta are dimensionless. u_plan is a held plant-input
% acceleration command, not the reference cart's kinematic acceleration.

%% Make one prediction before the baseline
% A -0.4 m/s^2 plant-input disturbance arrives from 4 s through 5 s. Which
% command component should be nearly silent before 4 s, then respond?

%% Visualize the deterministic baseline
baseline = model(1,1,1,0.6,0.4,12,0.02);
fprintf(['Baseline: position RMSE %.4f m, peak error %.4f m, recovery %.2f s, ' ...
    'feedback effort %.4f m^2/s^3.\n'],baseline.positionRmseM, ...
    baseline.maximumAbsolutePositionErrorM,baseline.recoveryTimeSec, ...
    baseline.feedbackEffortIntegralM2PerSec3);

figure('Name','P18 baseline tracking');
subplot(2,1,1);
plot(baseline.timeSec,baseline.referencePositionM,'k--','LineWidth',1.5, ...
    'DisplayName','Reference');
hold on;
plot(baseline.timeSec,baseline.actualPositionM,'b-','LineWidth',1.8, ...
    'DisplayName','Actual');
hold off; grid on;
xlabel('Time (s)'); ylabel('Position (m)');
title('Baseline: planned and actual position');
legend('Location','best');
subplot(2,1,2);
plot(baseline.timeSec,baseline.positionErrorM,'m-','LineWidth',1.8, ...
    'DisplayName','Position error (m)');
hold on;
plot(baseline.timeSec,baseline.rateErrorMPerSec,'Color',[0.1 0.55 0.3], ...
    'LineWidth',1.5,'DisplayName','Rate error (m/s)');
yline(baseline.positionToleranceM,'k:', ...
    'DisplayName','Position tolerance (m)');
yline(-baseline.positionToleranceM,'k:','HandleVisibility','off');
hold off; grid on;
xlabel('Time (s)'); ylabel('Error (m or m/s; see legend)');
title('Feedback reacts after the disturbance begins at 4 s');
legend('Location','best');

figure('Name','P18 baseline command decomposition');
plot(baseline.timeSec,baseline.feedforwardCommandMPerSec2,'b-', ...
    'LineWidth',1.6,'DisplayName','Feedforward');
hold on;
plot(baseline.timeSec,baseline.feedbackCommandMPerSec2,'m-', ...
    'LineWidth',1.6,'DisplayName','Feedback correction');
plot(baseline.timeSec,baseline.totalCommandMPerSec2,'k--', ...
    'LineWidth',1.8,'DisplayName','Total command');
plot(baseline.timeSec,baseline.disturbanceAccelerationMPerSec2,'r:', ...
    'LineWidth',1.6,'DisplayName','External disturbance');
hold off; grid on;
xlabel('Time (s)'); ylabel('Plant-input acceleration (m/s^2)');
title('Total command is the visible sum of two roles');
legend('Location','best');

%% Move lever 1: sweep only the feedforward scale
% Remove the disturbance for this sweep so alpha=1 is an exact matched-plan
% limit. Feedback scale, sign, plan, duration, and grid reset every run.
feedforwardScaleValues = [0 0.5 1 1.5];
feedforwardRmseM = zeros(size(feedforwardScaleValues));
feedforwardCorrectionEffortM2PerSec3 = zeros(size(feedforwardScaleValues));
for k = 1:numel(feedforwardScaleValues)
    changed = model(feedforwardScaleValues(k),1,1,0.6,0,12,0.02);
    assert(changed.feedbackScale == 1 && changed.feedforwardSign == 1 && ...
        changed.planAmplitudeMPerSec2 == 0.6 && ...
        changed.disturbanceMagnitudeMPerSec2 == 0 && ...
        changed.simulationDurationSec == 12 && changed.timeStepSec == 0.02, ...
        'Feedforward sweep changed a non-swept input.');
    feedforwardRmseM(k) = changed.positionRmseM;
    feedforwardCorrectionEffortM2PerSec3(k) = ...
        changed.feedbackEffortIntegralM2PerSec3;
end
figure('Name','P18 feedforward-scale sweep');
subplot(2,1,1);
plot(feedforwardScaleValues,feedforwardRmseM,'o-','LineWidth',1.7);
grid on; xlabel('Feedforward scale alpha (dimensionless)');
ylabel('Position RMSE (m)');
title('Sweep 1 changed view: matching the feasible plan removes nominal error');
subplot(2,1,2);
plot(feedforwardScaleValues,feedforwardCorrectionEffortM2PerSec3, ...
    's-','LineWidth',1.7);
grid on; xlabel('Feedforward scale alpha (dimensionless)');
ylabel('Feedback effort integral (m^2/s^3)');
title('Feedback need not recreate a known plant input');

%% Explain lever 1 from the error recurrence
% With no disturbance, e[k+1]=(A-B*beta*K)e[k]
% +B*(1-alpha)*u_plan[k]. Matching alpha=1 removes the forcing term. Values
% equally far above and below one create sign-reversed errors with equal
% quadratic metrics; total component energies are not additive because the
% square of a sum contains a cross term.

%% Reset, then move lever 2: sweep only feedback authority
% Feedforward returns to one and the same -0.4 m/s^2 disturbance returns.
% This sweep isolates how quickly error-driven correction removes the load.
feedbackScaleValues = [0 0.25 0.5 1 1.5 2];
feedbackPositionIseM2Sec = zeros(size(feedbackScaleValues));
feedbackCorrectionEffortM2PerSec3 = zeros(size(feedbackScaleValues));
feedbackRecoverySec = zeros(size(feedbackScaleValues));
for k = 1:numel(feedbackScaleValues)
    changed = model(1,feedbackScaleValues(k),1,0.6,0.4,12,0.02);
    assert(changed.feedforwardScale == 1 && changed.feedforwardSign == 1 && ...
        changed.planAmplitudeMPerSec2 == 0.6 && ...
        changed.disturbanceMagnitudeMPerSec2 == 0.4 && ...
        changed.simulationDurationSec == 12 && changed.timeStepSec == 0.02, ...
        'Feedback sweep changed a non-swept input.');
    feedbackPositionIseM2Sec(k) = changed.positionErrorIntegralM2Sec;
    feedbackCorrectionEffortM2PerSec3(k) = ...
        changed.feedbackEffortIntegralM2PerSec3;
    feedbackRecoverySec(k) = changed.recoveryTimeSec;
end
figure('Name','P18 feedback-scale sweep');
subplot(2,1,1);
plot(feedbackScaleValues,feedbackPositionIseM2Sec,'o-','LineWidth',1.7);
grid on; xlabel('Feedback scale beta (dimensionless)');
ylabel('Position-error integral (m^2 s)');
title('Sweep 2 changed view: feedback removes unplanned error');
subplot(2,1,2);
plot(feedbackScaleValues,feedbackCorrectionEffortM2PerSec3, ...
    's-','LineWidth',1.7);
grid on; xlabel('Feedback scale beta (dimensionless)');
ylabel('Feedback effort integral (m^2/s^3)');
title('Faster correction asks more from the reactive path');

%% Explain lever 2 from the poles
% At beta=0 the error dynamics retain a pole at one: feedforward follows the
% plan but cannot remove the position offset left by the disturbance. For
% positive beta in this bounded sweep, the poles move inside the unit circle
% and the feedback path trades more correction effort for faster recovery.

%% Deliberately broken case: reverse the feedforward mixer sign
% The planner and actuator must agree on command sign. The broken mixer sends
% -u_plan while the reference was generated by +u_plan. Feedback then spends
% most of its authority fighting a deterministic wiring error.
broken = model(1,1,-1,0.6,0.4,12,0.02);
recovered = model(1,1,1,0.6,0.4,12,0.02);
assert(isequaln(recovered,baseline), ...
    'Restoring the feedforward sign must recover the exact baseline.');
figure('Name','P18 broken feedforward sign');
subplot(2,1,1);
plot(broken.timeSec,broken.referencePositionM,'k--','LineWidth',1.5, ...
    'DisplayName','Reference');
hold on;
plot(broken.timeSec,broken.actualPositionM,'r-','LineWidth',1.8, ...
    'DisplayName','Actual with reversed feedforward');
hold off; grid on;
xlabel('Time (s)'); ylabel('Position (m)');
title('Broken case: feedback chases a command-path sign error');
legend('Location','best');
subplot(2,1,2);
plot(broken.timeSec,broken.feedforwardCommandMPerSec2,'b-', ...
    'LineWidth',1.5,'DisplayName','Wrong-sign feedforward');
hold on;
plot(broken.timeSec,broken.feedbackCommandMPerSec2,'m-', ...
    'LineWidth',1.5,'DisplayName','Feedback correction');
plot(broken.timeSec,broken.totalCommandMPerSec2,'k--', ...
    'LineWidth',1.7,'DisplayName','Total command');
hold off; grid on;
xlabel('Time (s)'); ylabel('Plant-input acceleration (m/s^2)');
title('Recognizable symptom: large opposing command components');
legend('Location','best');

%% Check, recover, and teach back
% Run the independent numerical invariants, then answer in two sentences:
% what feedforward needs, what feedback observes, and why neither path alone
% handles both the known plan and an unplanned disturbance.
clear run_checks;
run_checks;
