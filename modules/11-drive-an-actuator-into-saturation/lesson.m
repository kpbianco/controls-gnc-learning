%% P11 - Drive an Actuator into Saturation
% Guiding question:
% What inputs, observable effects, and failure modes matter when you drive an Actuator into Saturation?
%
% P10 separated a computed command from the command that reaches the plant.
% Now timing is fixed and actuator amplitude is bounded. Predict which trace
% reveals clipping first: requested control, applied control, or plant output.

%% Read the amplitude constraint
% The plant is tau*y'=-y+g*uApplied, with tau=1 s and
% g=1 output/actuator. Proportional feedback with Kp=4 actuator/output
% requests uRequested=Kp*(r-y). The actuator clips that request to +/-uLimit. A clipped
% command changes the plant trajectory because the missing effort never reaches it.

%% Visualize the deterministic baseline
baseline = model(1,2,5,0.01);
figure('Name','P11 lesson baseline');
subplot(2,1,1);
plot(baseline.t,baseline.reference,'k:','LineWidth',1.2, ...
    'DisplayName','Reference');
hold on;
plot(baseline.t,baseline.unlimitedOutput,'--','LineWidth',1.3, ...
    'DisplayName','Unlimited actuator');
plot(baseline.t,baseline.plantOutput,'LineWidth',1.7, ...
    'DisplayName','Limited actuator');
hold off; grid on;
xlabel('Time (s)'); ylabel('Plant output y (output)');
title('Baseline output: transient saturation slows the response');
legend('Location','best');
subplot(2,1,2);
stairs(baseline.t,baseline.requestedControl,'--','LineWidth',1.3, ...
    'DisplayName','Requested control');
hold on;
stairs(baseline.t,baseline.appliedControl,'LineWidth',1.7, ...
    'DisplayName','Applied control');
plot(baseline.t,baseline.controlUpperLimit,'r:', ...
    'DisplayName','Actuator limit');
hold off; grid on;
xlabel('Time (s)'); ylabel('Control command u (actuator)');
title('The actuator clips the initial four-unit request to two');
legend('Location','best');

%% Read and explain the observed difference
% Saturation is an amplitude mismatch, not a time delay. The controller still
% asks for 4*(r-y), but the plant receives at most uLimit. When the requested
% effort falls inside the limit, both commands meet and ordinary P feedback resumes.

%% Move one lever at a time
% Run experiment.m for an isolated reference sweep, reset, an isolated
% actuator-limit sweep, an infeasible case, and a recovery that changes only
% available actuator authority. Use interactive.m to move those same controls.

%% Check and teach back
% Run run_checks.m. Then explain in two sentences how r and uLimit determine
% clipping, name one visible symptom, and distinguish transient saturation from
% a demand that available actuator authority cannot support.
