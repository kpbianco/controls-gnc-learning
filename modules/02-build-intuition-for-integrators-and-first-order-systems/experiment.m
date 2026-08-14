%% P02 - Build Intuition for Integrators and First-Order Systems
% Guiding question:
% What inputs, observable effects, and failure modes matter when you build Intuition for Integrators and First-Order Systems?
%
% Run one section at a time. Read the explanation after each changed view
% before moving the next lever.

%% Read - governing mechanisms and baseline controls
% The integrator stores every bit of input: dx_I/dt = u.
% The first-order state closes its remaining gap: tau*dy/dt + y = K*u.
% Predict which output can settle under a constant positive command.
stepAmplitude = 1.0;  % normalized command
tau = 2.0;            % first-order time constant (s)
gain = 1.0;           % first-order steady-state gain
tEnd = 10.0;          % observation duration (s)
dt = 0.02;            % calculation interval (s)
baseline = model(stepAmplitude,tau,gain,tEnd,dt);

%% Visualize baseline - accumulated value and bounded response
figure('Name','P02 baseline outputs');
subplot(2,1,1);
plot(baseline.t,baseline.integrator,'LineWidth',1.4,'DisplayName','Integrator x_I');
hold on;
plot(baseline.t,baseline.firstOrder,'LineWidth',1.4,'DisplayName','First-order y');
yline(baseline.firstOrderSteady,'--','K A','DisplayName','First-order equilibrium');
hold off; grid on;
xlabel('Time (s)'); ylabel('Output (command for y; command s for x_I)');
title('Same step: accumulation versus settling'); legend('Location','best');

subplot(2,1,2);
plot(baseline.t,baseline.integratorRate,'LineWidth',1.4,'DisplayName','dx_I/dt');
hold on;
plot(baseline.t,baseline.firstOrderRate,'LineWidth',1.4,'DisplayName','dy/dt');
hold off; grid on;
xlabel('Time (s)'); ylabel('Rate (command for dx_I/dt; command/s for dy/dt)');
title('Rate view: constant accumulation versus a shrinking gap');
legend('Location','best');

fprintf(['Baseline metrics: integrator slope = %.2f command, x_I(%.1f s) = %.2f command s, ' ...
    'first-order equilibrium = %.2f command, four-tau settling estimate = %.2f s.\n'], ...
    baseline.integratorSlope,tEnd,baseline.integratorFinal, ...
    baseline.firstOrderSteady,baseline.settlingTimeEstimate);

%% Read and explain the baseline mechanism
% A positive constant input leaves the integrator slope positive forever.
% The first-order rate is (K*u-y)/tau, so it is largest at the start and
% approaches zero as y closes the gap to K*u. The curve does not stop
% because time ran out; it settles because its governing rate vanishes.

%% Sweep 1 - move only input amplitude
amplitudes = [0.5 1.0 1.5];
figure('Name','P02 sweep 1 - input amplitude'); hold on; grid on;
for k = 1:numel(amplitudes)
    changed = model(amplitudes(k),tau,gain,tEnd,dt);
    plot(changed.t,changed.integrator,'LineWidth',1.3,'DisplayName', ...
        sprintf('A = %.1f, slope = %.1f',amplitudes(k),changed.integratorSlope));
end
xlabel('Time (s)'); ylabel('Integrator output (normalized command s)');
title('Sweep 1: input amplitude changes the accumulation slope');
legend('Location','northwest');

%% Read and explain sweep 1
% Doubling A doubles the area accumulated per second and therefore doubles
% x_I at every positive time. Tau and gain did not move in this sweep.

%% Sweep 2 - reset amplitude and move only time constant
timeConstants = [0.5 2.0 5.0];
figure('Name','P02 sweep 2 - time constant'); hold on; grid on;
for k = 1:numel(timeConstants)
    changed = model(stepAmplitude,timeConstants(k),gain,tEnd,dt);
    plot(changed.t,changed.firstOrder,'LineWidth',1.3,'DisplayName', ...
        sprintf('tau = %.1f s',timeConstants(k)));
end
yline(gain*stepAmplitude,'--','K A');
xlabel('Time (s)'); ylabel('First-order output (normalized command)');
title('Sweep 2: tau changes speed, not equilibrium');
legend('Location','southeast');

%% Read and explain sweep 2
% At t = tau every curve has completed 1-exp(-1), about 63.2 percent, of
% its own total change. Increasing tau stretches time without changing K*A.

%% Broken case - a coarse explicit-Euler interval invents instability
% Explicit Euler is stable for this decay only when 0 < dt/tau < 2.
% Here dt/tau = 3. The continuous first-order system is still stable, but
% the numerical update multiplies each equilibrium error by 1-dt/tau = -2.
brokenTau = 1.0;
brokenDt = 3.0;
broken = model(stepAmplitude,brokenTau,gain,18.0,brokenDt);
figure('Name','P02 broken case - coarse Euler');
plot(broken.t,broken.firstOrder,'LineWidth',1.4,'DisplayName','Exact first-order');
hold on;
plot(broken.t,broken.eulerFirstOrder,'o--','LineWidth',1.2, ...
    'DisplayName','Broken explicit Euler, dt/tau = 3');
yline(broken.firstOrderSteady,'--','K A');
hold off; grid on;
xlabel('Time (s)'); ylabel('First-order output (normalized command)');
title('Broken assumption: the calculation interval resolves the dynamics');
legend('Location','best');

fprintf(['Broken-case metric: max Euler magnitude = %.2f command while the exact ' ...
    'equilibrium is %.2f command.\n'],broken.maxAbsEuler,broken.firstOrderSteady);
