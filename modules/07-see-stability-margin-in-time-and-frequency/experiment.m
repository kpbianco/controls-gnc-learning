%% P07 - See Stability Margin in Time and Frequency
%
% Guiding question:
% What inputs, observable effects, and failure modes matter when you see Stability Margin in Time and Frequency?
%
% Run one section at a time. Observe each changed view before reading its
% mechanism, and reset the first lever before moving the second.

%% Read - connect P06 tuning to reserve around the loop
% P06 judged a controller from closed-loop traces. Here the open loop is
% L(s)=K/[s(s+b)(tau*s+1)] with b=1/s. The same factors create the closed-loop time
% response. Predict whether increasing actuator lag tau adds or removes phase
% reserve at the unity-magnitude crossover.
loopGain = 1;          % controller gain K (1/s^2)
actuatorLagSec = 0.2; % actuator time constant tau (s)
tEnd = 20;            % observation duration (s)
dt = 0.01;            % requested calculation interval (s)
baseline = model(loopGain,actuatorLagSec,tEnd,dt);

%% Visualize baseline - time response first
figure('Name','P07 baseline time response');
plot(baseline.t,baseline.reference*ones(size(baseline.t)),'k:', ...
    'LineWidth',1.2,'DisplayName','Reference r');
hold on;
plot(baseline.t,baseline.output,'LineWidth',1.5, ...
    'DisplayName','Output y');
hold off; grid on;
xlabel('Time (s)'); ylabel('Output y (normalized)');
title('Baseline time view: positive margin, decaying oscillation');
legend('Location','southeast');
fprintf(['Time metrics: overshoot %.3f normalized, settling time %.2f s, ' ...
    'max |actuator| %.3f output/s^2.\n'],baseline.overshoot, ...
    baseline.settlingTimeSec,baseline.maxAbsActuator);

%% Changed view - reveal magnitude and phase for the same baseline
figure('Name','P07 baseline frequency response');
subplot(2,1,1);
semilogx(baseline.omegaRadPerSec,baseline.openLoopMagnitudeDb, ...
    'LineWidth',1.4,'DisplayName','|L(j omega)|');
hold on;
plot(baseline.gainCrossoverRadPerSec,0,'o','DisplayName','Gain crossover');
yline(0,'k:','0 dB'); hold off; grid on;
xlabel('Angular frequency (rad/s)'); ylabel('Magnitude (dB)');
title('Open-loop magnitude'); legend('Location','southwest');
subplot(2,1,2);
semilogx(baseline.omegaRadPerSec,baseline.openLoopPhaseDeg, ...
    'LineWidth',1.4,'DisplayName','angle L(j omega)');
hold on;
plot(baseline.gainCrossoverRadPerSec, ...
    -180+baseline.phaseMarginDeg,'o','DisplayName','Phase at crossover');
yline(-180,'k:','-180 deg'); hold off; grid on;
xlabel('Angular frequency (rad/s)'); ylabel('Phase (deg)');
title('Open-loop phase and reserve'); legend('Location','southwest');
fprintf(['Frequency metrics: crossover %.3f rad/s, phase margin %.2f deg, ' ...
    'gain margin %.2f dB.\n'],baseline.gainCrossoverRadPerSec, ...
    baseline.phaseMarginDeg,baseline.gainMarginDb);

%% Read and explain the baseline mechanism
% Gain crossover is where the open-loop error cycle returns with unit
% magnitude. Its phase is still baseline.phaseMarginDeg short of -180 deg, so
% the returned correction remains net negative feedback. The time oscillation
% therefore decays rather than grows.

%% Sweep 1 - move only loop gain
loopGains = [0.5 1 5.5];
figure('Name','P07 sweep 1 - loop gain'); hold on; grid on;
for k = 1:numel(loopGains)
    changed = model(loopGains(k),actuatorLagSec,30,0.01);
    plot(changed.t,changed.output,'LineWidth',1.3,'DisplayName', ...
        sprintf('K = %.1f 1/s^2, PM = %.1f deg, overshoot = %.3f', ...
        loopGains(k),changed.phaseMarginDeg,changed.overshoot));
end
plot(baseline.t,baseline.reference*ones(size(baseline.t)),'k:', ...
    'LineWidth',1.2,'DisplayName','Reference r');
xlabel('Time (s)'); ylabel('Output y (normalized)');
title('Sweep 1: gain raises crossover and spends phase reserve');
legend('Location','southeast');

%% Read and explain sweep 1
% Only K moved; tau stayed 0.2 s. Gain does not directly change the phase
% formula, but it moves unity magnitude to a higher frequency. At that higher
% frequency both dynamic factors contribute more lag, so margin shrinks and
% overshoot grows.

%% Sweep 2 - reset gain and move only actuator lag
actuatorLagsSec = [0.05 0.2 0.8];
figure('Name','P07 sweep 2 - actuator lag'); hold on; grid on;
for k = 1:numel(actuatorLagsSec)
    changed = model(loopGain,actuatorLagsSec(k),30,0.004);
    plot(changed.t,changed.output,'LineWidth',1.3,'DisplayName', ...
        sprintf('tau = %.2f s, PM = %.1f deg, overshoot = %.3f', ...
        actuatorLagsSec(k),changed.phaseMarginDeg,changed.overshoot));
end
plot(baseline.t,baseline.reference*ones(size(baseline.t)),'k:', ...
    'LineWidth',1.2,'DisplayName','Reference r');
xlabel('Time (s)'); ylabel('Output y (normalized)');
title('Sweep 2: actuator lag removes phase reserve');
legend('Location','southeast');

%% Read and explain sweep 2
% K reset to 1. Only tau moved. The actuator factor contributes
% -atan(tau*omega), so a larger tau subtracts phase sooner. The frequency
% margin falls and the time response rings more even though controller gain is
% unchanged.

%% Broken case - trust an instantaneous actuator at high gain
% The violated assumption is omitted actuator lag. K=4 is stable when tau=0,
% but the actual tau=0.5 s loop has Kcritical=3, gain margin below one, and a
% negative phase margin. Its oscillation grows instead of decaying.
optimistic = model(4,0,20,0.005);
broken = model(4,0.5,30,0.005);
recovered = model(1,0.5,30,0.005);
figure('Name','P07 broken omitted-lag assumption and recovery');
subplot(2,1,1);
plot(optimistic.t,optimistic.output,'LineWidth',1.3, ...
    'DisplayName','Assumed tau = 0 s');
hold on;
plot(broken.t,broken.output,'LineWidth',1.5, ...
    'DisplayName','Actual tau = 0.5 s');
plot(broken.t,broken.reference*ones(size(broken.t)),'k:', ...
    'LineWidth',1.2,'DisplayName','Reference r');
hold off; grid on;
xlabel('Time (s)'); ylabel('Output y (normalized)');
title('Broken assumption: omitted lag hides instability');
legend('Location','best');
subplot(2,1,2);
plot(recovered.t,recovered.output,'LineWidth',1.5, ...
    'DisplayName','Recovered K = 1, tau = 0.5 s');
hold on;
plot(recovered.t,recovered.reference*ones(size(recovered.t)),'k:', ...
    'LineWidth',1.2,'DisplayName','Reference r');
hold off; grid on;
xlabel('Time (s)'); ylabel('Output y (normalized)');
title('Recovery: restore positive margin by reducing gain');
legend('Location','southeast');
fprintf(['Broken: Kcritical %.1f, GM %.2f dB, PM %.2f deg, max |y| %.2f. ' ...
    'Recovered: GM %.2f dB, PM %.2f deg, max |y| %.2f.\n'], ...
    broken.criticalLoopGain,broken.gainMarginDb,broken.phaseMarginDeg, ...
    broken.maxAbsOutput,recovered.gainMarginDb,recovered.phaseMarginDeg, ...
    recovered.maxAbsOutput);

%% Read and explain recovery
% This is not merely a slow actuator. The missing lag spent more phase than
% the design owned. Retaining the real tau=0.5 s and reducing K below
% Kcritical restores positive gain and phase margins; only then does the time
% oscillation decay.
