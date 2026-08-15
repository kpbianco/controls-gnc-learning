%% P13 - Test Controllability
%
% Guiding question:
% What inputs, observable effects, and failure modes matter when you test Controllability?
%
% Run one section at a time. Read the model, inspect the baseline, move one
% lever, inspect its changed view, then reset before moving the next.

%% Read - an input direction must spread through the dynamics
% P12 showed that requested effort and available effort can differ. Here the
% question is whether the input path can move every state direction at all:
%   d(position)/dt = coupling*rate
%   d(rate)/dt     = -damping*rate + inputGain*command
% The normalized state scales are 1 m and 1 m/s. Predict once: can a command
% that enters only rate eventually move position when coupling is intact?
inputGain = 1;                        % (m/s^2)/command
coupling = 1;                         % dimensionless
horizonSec = 2;                       % rest-to-rest maneuver time (s)
timeStepSec = 0.05;                   % held-command interval (s)
baseline = model(inputGain,coupling,horizonSec,timeStepSec);

%% Visualize baseline - the rest-to-rest target transfer
figure('Name','P13 baseline state transfer');
subplot(2,1,1);
plot(baseline.timeSec,baseline.stateTrajectory(1,:), ...
    'LineWidth',1.8,'DisplayName','Position');
hold on;
yline(baseline.targetPositionM,'k:', ...
    'DisplayName','Target position');
hold off; grid on;
xlabel('Time (s)'); ylabel('Position (m)');
title('Baseline: finite-horizon command reaches the position target');
legend('Location','best');
subplot(2,1,2);
plot(baseline.timeSec,baseline.stateTrajectory(2,:), ...
    'LineWidth',1.8,'DisplayName','Rate');
hold on;
yline(0,'k:','DisplayName','Target rate');
hold off; grid on;
xlabel('Time (s)'); ylabel('Rate (m/s)');
title('Rate rises, then returns to zero at the target');
legend('Location','best');

%% Changed view - see direct and propagated input effects
figure('Name','P13 baseline input effects');
subplot(2,1,1);
stairs(baseline.timeSec,[baseline.minimumEnergyCommand; ...
    baseline.minimumEnergyCommand(end)], ...
    'LineWidth',1.5,'DisplayName','Held command');
grid on;
xlabel('Time (s)'); ylabel('Command (command)');
title('Positive command builds rate; negative command removes it');
legend('Location','best');
subplot(2,1,2);
plot(baseline.timeSec,baseline.probeStateTrajectory(1,:), ...
    'LineWidth',1.8,'DisplayName','Position / 1 m');
hold on;
plot(baseline.timeSec,baseline.probeStateTrajectory(2,:),'--', ...
    'LineWidth',1.5,'DisplayName','Rate / 1 m/s');
hold off; grid on;
xlabel('Time (s)'); ylabel('Normalized state effect');
title('A fixed probe moves rate first and position through coupling');
legend('Location','best');
fprintf(['Baseline metrics: rank %d of 2; scaled sigma_min %.6f; ' ...
    'energy %.6f command^2*s; peak %.6f command; residual %.3g.\n'], ...
    baseline.controllabilityRank,baseline.minimumSingularValue, ...
    baseline.commandEnergyCommand2Sec,baseline.peakCommandMagnitude, ...
    baseline.terminalResidualNorm);

%% Read and explain the baseline mechanism
% The continuous columns [B,A*B] expose the direct rate direction and the
% position direction produced by coupling. For N held inputs, the exact
% finite-horizon columns are [Ad^(N-1)*Bd,...,Bd]. Their Gramian has two
% positive eigenvalues, so an explicit 2-by-2 solve can construct a command
% that reaches [1 m; 0 m/s]. Rank says possible, not easy or actuator-safe.

%% Sweep 1 - move only actuator effectiveness
inputGains = [0.25 0.5 1 1.5 2];
coupling = 1;
horizonSec = 2;
gainMinimumSingularValue = zeros(size(inputGains));
gainCommandEnergy = zeros(size(inputGains));
gainPeakCommand = zeros(size(inputGains));
for k = 1:numel(inputGains)
    changed = model(inputGains(k),coupling,horizonSec,0.05);
    gainMinimumSingularValue(k) = changed.minimumSingularValue;
    gainCommandEnergy(k) = changed.commandEnergyCommand2Sec;
    gainPeakCommand(k) = changed.peakCommandMagnitude;
end
figure('Name','P13 sweep 1 - actuator effectiveness');
subplot(2,1,1);
plot(inputGains,gainMinimumSingularValue,'o-','LineWidth',1.5); grid on;
xlabel('Input gain ((m/s^2)/command)');
ylabel('Scaled minimum singular value');
title('Stronger input scales every finite-horizon reachability column');
subplot(2,1,2);
plot(inputGains,gainCommandEnergy,'s-','LineWidth',1.5); grid on;
xlabel('Input gain ((m/s^2)/command)');
ylabel('Command energy (command^2*s)');
title('The same target needs less command energy as authority grows');

%% Read and explain sweep 1
% Only input gain moved. Every nonzero case remains rank two, but R scales
% with input gain. Halving gain halves both scaled singular values and needs
% four times the command-energy proxy. A mathematically controllable weak
% actuator can therefore be impractical once P11/P12 limits are restored.

%% Sweep 2 - reset effectiveness and move only maneuver time
inputGain = 1;
maneuverTimesSec = [0.5 1 2 3 4];
timeMinimumSingularValue = zeros(size(maneuverTimesSec));
timeCommandEnergy = zeros(size(maneuverTimesSec));
timePeakCommand = zeros(size(maneuverTimesSec));
for k = 1:numel(maneuverTimesSec)
    changed = model(inputGain,1,maneuverTimesSec(k),0.05);
    timeMinimumSingularValue(k) = changed.minimumSingularValue;
    timeCommandEnergy(k) = changed.commandEnergyCommand2Sec;
    timePeakCommand(k) = changed.peakCommandMagnitude;
end
figure('Name','P13 sweep 2 - maneuver time');
subplot(2,1,1);
plot(maneuverTimesSec,timeMinimumSingularValue,'o-','LineWidth',1.5); grid on;
xlabel('Maneuver time (s)');
ylabel('Scaled minimum singular value');
title('More input opportunities strengthen the weakest target direction');
subplot(2,1,2);
semilogy(maneuverTimesSec,timeCommandEnergy,'s-','LineWidth',1.5, ...
    'DisplayName','Energy');
hold on;
semilogy(maneuverTimesSec,timePeakCommand,'d--','LineWidth',1.5, ...
    'DisplayName','Peak magnitude');
hold off; grid on;
xlabel('Maneuver time (s)');
ylabel('Command metric (log scale)');
title('Short rest-to-rest transfers demand much more command');
legend('Location','best');

%% Read and explain sweep 2
% Input gain reset to 1, and A, B, target, damping, coupling, and held-input
% interval remain fixed. A longer horizon adds earlier reachability columns.
% Those inputs have more time to create rate, move position, and remove rate
% again, so energy and peak command fall without changing structural rank.

%% Broken case - disconnect rate from position, then recover
% The actuator is still healthy: the exact same probe changes rate. But with
% coupling=0, rate has no path into position. The A*B position direction
% disappears, rank falls to one, and the position target is unreachable.
broken = model(1,0,2,0.05);
recovered = model(1,1,2,0.05);
figure('Name','P13 broken state coupling and recovery');
subplot(2,1,1);
plot(broken.timeSec,broken.probeStateTrajectory(1,:),'--', ...
    'LineWidth',1.7,'DisplayName','Broken position');
hold on;
plot(recovered.timeSec,recovered.probeStateTrajectory(1,:), ...
    'LineWidth',1.8,'DisplayName','Restored position');
hold off; grid on;
xlabel('Time (s)'); ylabel('Probe position (m)');
title('Broken coupling freezes position despite a working rate actuator');
legend('Location','best');
subplot(2,1,2);
plot(broken.timeSec,broken.probeStateTrajectory(2,:),'--', ...
    'LineWidth',1.7,'DisplayName','Broken rate');
hold on;
plot(recovered.timeSec,recovered.probeStateTrajectory(2,:), ...
    'LineWidth',1.4,'DisplayName','Restored rate');
hold off; grid on;
xlabel('Time (s)'); ylabel('Probe rate (m/s)');
title('Rate response is unchanged: the missing path is rate to position');
legend('Location','best');
fprintf(['Broken/recovered metrics: rank %d / %d; terminal position ' ...
    'residual %.3f / %.3g m; probe peak rate %.3f / %.3f m/s.\n'], ...
    broken.controllabilityRank,recovered.controllabilityRank, ...
    broken.terminalResidual(1),recovered.terminalResidual(1), ...
    max(abs(broken.probeStateTrajectory(2,:))), ...
    max(abs(recovered.probeStateTrajectory(2,:))));

%% Check and teach back
% Run run_checks. Then answer in two sentences: which input path reaches each
% state, what visible symptom reveals a missing path, and why does full rank
% not guarantee a feasible command for a limited actuator?
run_checks;
