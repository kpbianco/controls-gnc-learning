%% P05 - Close a Loop with Proportional Control
%
% Guiding question:
% What inputs, observable effects, and failure modes matter when you close a Loop with Proportional Control?
%
% Run one section at a time. Observe the changed view before reading its
% mechanism, and reset each lever before moving the next one.

%% Read - close one simple plant around measured error
% P04 kept model assumptions visible. Here the plant is intentionally simple:
% tau*y' = -y + G*u. Negative feedback measures y, forms e = r-y, and
% commands u = Kp*e. Predict whether finite Kp reaches r exactly.
proportionalGain = 2;       % Kp (command/m)
plantTimeConstantSec = 1;   % tau (s)
plantGainMPerCommand = 1;   % G (m/command)
referenceM = 1;             % requested position (m)
initialOutputM = 0;         % initial measured position (m)
feedbackSign = -1;          % -1 subtracts the measurement
tEnd = 5;                   % observation duration (s)
dt = 0.005;                 % requested output interval (s)
baseline = model(proportionalGain,plantTimeConstantSec, ...
    plantGainMPerCommand,referenceM,initialOutputM,feedbackSign,tEnd,dt);

%% Visualize baseline - reference and measured output
figure('Name','P05 baseline closed-loop position');
plot(baseline.t,referenceM*ones(size(baseline.t)),'k:', ...
    'LineWidth',1.2,'DisplayName','Reference r');
hold on;
plot(baseline.t,baseline.outputM,'LineWidth',1.5, ...
    'DisplayName','Measured output y');
hold off; grid on;
xlabel('Time (s)'); ylabel('Output position y (m)');
title('Baseline negative feedback: fast but not exact tracking');
legend('Location','southeast');

fprintf(['Baseline metrics: pole = %.3f (1/s), closed-loop time constant = %.3f s, ' ...
    'predicted steady error = %.3f m, initial command = %.3f command units.\n'], ...
    baseline.closedLoopPolePerSec,baseline.closedLoopTimeConstantSec, ...
    baseline.predictedSteadyStateErrorM,baseline.initialControlCommand);

%% Changed view - tracking error and proportional effort
figure('Name','P05 baseline error and command');
subplot(2,1,1);
plot(baseline.t,baseline.trackingErrorM,'LineWidth',1.5); grid on;
xlabel('Time (s)'); ylabel('Tracking error e (m)');
title('Residual error supplies the holding command');
subplot(2,1,2);
plot(baseline.t,baseline.controlCommand,'LineWidth',1.5); grid on;
xlabel('Time (s)'); ylabel('Control command u (command units)');
title('u = Kp e: effort falls as the error shrinks');

%% Read and explain the baseline mechanism
% The closed-loop pole is -(1+G*Kp)/tau, so feedback speeds this ideal plant.
% At equilibrium, y_ss = G*Kp*r/(1+G*Kp). A finite error remains because
% u_ss = Kp*e_ss is the command required to hold y away from zero.

%% Sweep 1 - move only proportional gain
proportionalGains = [0.5 2 8];
figure('Name','P05 sweep 1 - proportional gain'); hold on; grid on;
for k = 1:numel(proportionalGains)
    changed = model(proportionalGains(k),plantTimeConstantSec, ...
        plantGainMPerCommand,referenceM,initialOutputM,-1,tEnd,dt);
    plot(changed.t,changed.outputM,'LineWidth',1.3,'DisplayName', ...
        sprintf('Kp = %.1f, e_ss = %.3f m, u(0) = %.1f', ...
        proportionalGains(k),changed.predictedSteadyStateErrorM, ...
        changed.initialControlCommand));
end
plot(baseline.t,referenceM*ones(size(baseline.t)),'k:', ...
    'LineWidth',1.2,'DisplayName','Reference r');
xlabel('Time (s)'); ylabel('Output position y (m)');
title('Sweep 1: gain trades smaller error and faster response for more effort');
legend('Location','southeast');

%% Read and explain sweep 1
% Only Kp moved. Tau, G, reference, initial output, and feedback sign stayed
% fixed. Larger Kp moves the pole left and reduces e_ss, but u(0) = Kp*r
% rises. Proportional gain approaches exact tracking but never reaches it at
% finite gain for this plant.

%% Sweep 2 - reset gain and move only plant time constant
plantTimeConstantsSec = [0.25 1 3];
figure('Name','P05 sweep 2 - plant time constant'); hold on; grid on;
for k = 1:numel(plantTimeConstantsSec)
    changed = model(proportionalGain,plantTimeConstantsSec(k), ...
        plantGainMPerCommand,referenceM,initialOutputM,-1,tEnd,dt);
    plot(changed.t,changed.outputM,'LineWidth',1.3,'DisplayName', ...
        sprintf('tau = %.2f s, tau_cl = %.3f s', ...
        plantTimeConstantsSec(k),changed.closedLoopTimeConstantSec));
end
plot(baseline.t,referenceM*ones(size(baseline.t)),'k:', ...
    'LineWidth',1.2,'DisplayName','Reference r');
xlabel('Time (s)'); ylabel('Output position y (m)');
title('Sweep 2: plant time constant stretches only the transient');
legend('Location','southeast');

%% Read and explain sweep 2
% Kp reset to 2. Only tau moved, so the closed-loop time constant scales
% with tau. The predicted steady output, residual error, and initial command
% stay fixed because none of them depends on tau.

%% Broken case - add the measurement instead of subtracting it
% The violated assumption is negative feedback: measured y must oppose the
% reference error. With feedbackSign = +1 and G*Kp > 1, the closed-loop pole
% is positive. Every positive output increases the next command and the
% response grows away from the reference.
broken = model(2,1,1,1,0,1,4,0.005);
recovered = model(2,1,1,1,0,-1,4,0.005);
figure('Name','P05 broken and recovered feedback sign');
subplot(2,1,1);
plot(broken.t,broken.outputM,'LineWidth',1.5, ...
    'DisplayName','Broken: measurement added');
hold on;
plot(broken.t,ones(size(broken.t)),'k:','LineWidth',1.2, ...
    'DisplayName','Reference r');
hold off; grid on;
xlabel('Time (s)'); ylabel('Output position y (m)');
title('Broken sign: positive pole drives exponential growth');
legend('Location','northwest');

subplot(2,1,2);
plot(recovered.t,recovered.outputM,'LineWidth',1.5, ...
    'DisplayName','Recovered: measurement subtracted');
hold on;
plot(recovered.t,ones(size(recovered.t)),'k:','LineWidth',1.2, ...
    'DisplayName','Reference r');
hold off; grid on;
xlabel('Time (s)'); ylabel('Output position y (m)');
title('Recovery: restore negative feedback before retuning gain');
legend('Location','southeast');

fprintf(['Broken-case metric: pole = %.2f (1/s), final |y| = %.1f m. ' ...
    'Recovered pole = %.2f (1/s), final error = %.3f m.\n'], ...
    broken.closedLoopPolePerSec,abs(broken.outputM(end)), ...
    recovered.closedLoopPolePerSec,recovered.finalTrackingErrorM);

%% Read and explain recovery
% This failure is a polarity error, not ordinary proportional offset and not
% an actuator limit. Restore subtraction first. The recovered loop is bounded
% and fast, while its finite residual error remains the expected P-only tradeoff.
