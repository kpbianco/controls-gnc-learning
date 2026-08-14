%% P03 - Relate Poles to Visible Motion
% Guiding question:
% What inputs, observable effects, and failure modes matter when you relate Poles to Visible Motion?
%
% Run one section at a time. Observe the changed view before reading its
% mechanism, and reset each lever before moving the next one.

%% Read - pole coordinates and the free-motion baseline
% P02 connected a first-order pole at -1/tau to exponential settling. A
% conjugate pair p = sigma +/- j*omega adds oscillation: sigma (1/s) sets
% the exponential envelope and omega (rad/s) sets the cycle spacing.
% Predict what the displacement will do for sigma < 0 before plotting it.
poleReal = -0.5;       % sigma, exponential decay rate (1/s)
poleImag = 2.0;        % omega, oscillation rate (rad/s)
initialPosition = 1.0; % released displacement (m)
initialVelocity = 0.0; % released velocity (m/s)
tEnd = 12.0;           % observation duration (s)
dt = 0.01;             % calculation interval (s)
baseline = model(poleReal,poleImag,initialPosition,initialVelocity,tEnd,dt);

%% Visualize baseline - visible motion inside its envelope
figure('Name','P03 baseline motion');
plot(baseline.t,baseline.position,'LineWidth',1.4, ...
    'DisplayName','Displacement x');
hold on;
plot(baseline.t,baseline.envelope,'--','LineWidth',1.1, ...
    'DisplayName','Positive envelope');
plot(baseline.t,-baseline.envelope,'--','LineWidth',1.1, ...
    'DisplayName','Negative envelope');
hold off; grid on;
xlabel('Time (s)'); ylabel('Displacement (m)');
title('Baseline: a left-half-plane pair produces shrinking oscillation');
legend('Location','northeast');

%% Changed view - locate the same mechanism in the pole plane
figure('Name','P03 baseline pole plane');
plot(real(baseline.poles),imag(baseline.poles),'x','MarkerSize',12, ...
    'LineWidth',2,'DisplayName','p = sigma +/- j omega');
hold on;
plot([0 0],[-4.5 4.5],'k--','DisplayName','Imaginary axis');
hold off; grid on; axis([-1.5 0.5 -4.5 4.5]);
xlabel('Real part sigma (1/s)'); ylabel('Imaginary part omega (rad/s)');
title('The baseline pair lies in the left half-plane');
legend('Location','best');

fprintf(['Baseline metrics: poles = %.2f +/- j%.2f 1/s, envelope constant = %.2f s, ' ...
    'period = %.3f s, end exponential scale = %.5f.\n'], ...
    baseline.poleReal,baseline.poleImag,baseline.envelopeTimeConstant, ...
    baseline.oscillationPeriod,baseline.exponentialScaleRatio);

%% Read and explain the baseline mechanism
% The real coordinate is negative, so exp(sigma*t) shrinks. The imaginary
% coordinate is nonzero, so sine and cosine alternate the displacement.
% The pole-plane marks and the motion curve are two views of one equation,
% not separate facts to memorize.

%% Sweep 1 - move only the pole real part
realParts = [-1.0 -0.5 -0.2];
figure('Name','P03 sweep 1 - pole real part'); hold on; grid on;
for k = 1:numel(realParts)
    changed = model(realParts(k),poleImag,initialPosition,initialVelocity,tEnd,dt);
    plot(changed.t,changed.position,'LineWidth',1.3,'DisplayName', ...
        sprintf('sigma = %.1f 1/s, tau_e = %.1f s', ...
        realParts(k),changed.envelopeTimeConstant));
end
xlabel('Time (s)'); ylabel('Displacement (m)');
title('Sweep 1: real part changes decay while cycle spacing stays fixed');
legend('Location','northeast');

%% Read and explain sweep 1
% Only sigma moved. A more-negative sigma makes the envelope contract more
% rapidly. omega stayed at 2 rad/s, so every curve retains period pi s.

%% Sweep 2 - reset real part and move only imaginary magnitude
imaginaryParts = [1.0 2.0 4.0];
figure('Name','P03 sweep 2 - pole imaginary part'); hold on; grid on;
for k = 1:numel(imaginaryParts)
    changed = model(poleReal,imaginaryParts(k),initialPosition,initialVelocity,tEnd,dt);
    plot(changed.t,changed.position,'LineWidth',1.3,'DisplayName', ...
        sprintf('omega = %.1f rad/s, T = %.2f s', ...
        imaginaryParts(k),changed.oscillationPeriod));
end
xlabel('Time (s)'); ylabel('Displacement (m)');
title('Sweep 2: imaginary magnitude changes cycle spacing');
legend('Location','northeast');

%% Read and explain sweep 2
% Only omega moved. Larger imaginary magnitude packs more cycles into the
% same time window because T = 2*pi/omega. sigma reset to -0.5 1/s, so all
% three envelopes shrink by the same ratio exp(-0.5*t).

%% Broken case - move the pair into the right half-plane
% The named violated assumption is that the mode dissipates energy and its
% poles remain in the left half-plane. sigma = +0.25 1/s reverses the
% envelope: the exact motion now grows even though omega is unchanged.
broken = model(0.25,poleImag,initialPosition,initialVelocity,tEnd,dt);
recovered = model(-0.25,poleImag,initialPosition,initialVelocity,tEnd,dt);
figure('Name','P03 broken and recovered pole locations');
subplot(2,1,1);
plot(broken.t,broken.position,'LineWidth',1.4, ...
    'DisplayName','Broken: sigma = +0.25 1/s');
hold on;
plot(recovered.t,recovered.position,'LineWidth',1.4, ...
    'DisplayName','Recovered: sigma = -0.25 1/s');
hold off; grid on;
xlabel('Time (s)'); ylabel('Displacement (m)');
title('Same cycle spacing, opposite envelope direction');
legend('Location','best');

subplot(2,1,2);
semilogy(broken.t,broken.energy,'LineWidth',1.4, ...
    'DisplayName','Broken unit-mass energy');
hold on;
semilogy(recovered.t,recovered.energy,'LineWidth',1.4, ...
    'DisplayName','Recovered unit-mass energy');
hold off; grid on;
xlabel('Time (s)'); ylabel('Mechanical energy for unit mass (J)');
title('Right-half-plane energy grows; left-half-plane energy decays');
legend('Location','best');

fprintf(['Broken-case metric: envelope grows by %.2f; restoring sigma to -0.25 1/s ' ...
    'shrinks it to %.4f of its initial scale.\n'], ...
    broken.exponentialScaleRatio,recovered.exponentialScaleRatio);

%% Read and explain recovery
% Changing the sign of sigma crosses the imaginary-axis stability boundary.
% The recovered poles have the same imaginary coordinates and therefore the
% same cycle spacing, but their negative real coordinates restore decay.
