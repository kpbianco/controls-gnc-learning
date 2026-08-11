%% P01 - Watch a Mass-Spring-Damper Respond
close all; clc;

%% Baseline controls
m = 1.0; c = 0.8; k = 4.0; force = 1.0; tEnd = 12;
out = model(m,c,k,force,tEnd);

%% Baseline plots
figure('Name','P01 baseline');
subplot(2,1,1);
plot(out.t,out.position,'LineWidth',1.3); hold on;
yline(out.steady,'--','Static equilibrium');
grid on; xlabel('Time (s)'); ylabel('Position');
title(sprintf('Step response: zeta = %.2f, omega_n = %.2f rad/s',out.zeta,out.wn));

subplot(2,1,2);
plot(out.position,out.velocity,'LineWidth',1.2);
grid on; xlabel('Position'); ylabel('Velocity');
title('Phase plane: energy spirals toward equilibrium');

%% Sweep 1 - damping
damping = [0.1 0.8 4.0];
figure('Name','P01 damping sweep'); hold on; grid on;
for i = 1:numel(damping)
    s = model(m,damping(i),k,force,tEnd);
    plot(s.t,s.position,'LineWidth',1.2,'DisplayName', ...
        sprintf('c = %.1f, zeta = %.2f',damping(i),s.zeta));
end
yline(force/k,'--'); xlabel('Time (s)'); ylabel('Position');
title('Damping trades ringing against sluggishness'); legend('Location','best');

%% Sweep 2 - stiffness
stiffness = [1 4 12];
figure('Name','P01 stiffness sweep'); hold on; grid on;
for i = 1:numel(stiffness)
    s = model(m,c,stiffness(i),force,tEnd);
    plot(s.t,s.position,'LineWidth',1.2,'DisplayName',sprintf('k = %.1f',stiffness(i)));
end
xlabel('Time (s)'); ylabel('Position'); title('Stiffness changes speed and static deflection');
legend('Location','best');

%% Broken case - explicit Euler with a step that is too large
dt = 1.0;
tb = 0:dt:tEnd;
xb = zeros(size(tb)); vb = zeros(size(tb));
for n = 1:numel(tb)-1
    xb(n+1) = xb(n) + dt*vb(n);
    vb(n+1) = vb(n) + dt*(force-c*vb(n)-k*xb(n))/m;
end
figure('Name','P01 broken integration');
plot(out.t,out.position,'LineWidth',1.3,'DisplayName','ode45 reference'); hold on;
plot(tb,xb,'o--','DisplayName','Euler, dt = 1 s');
grid on; xlabel('Time (s)'); ylabel('Position');
title('Broken: a poor numerical step can invent instability'); legend('Location','best');

fprintf('zeta = %.3f, natural frequency = %.3f rad/s, overshoot = %.2f%%\n', ...
    out.zeta,out.wn,out.overshoot_percent);
assert(abs(out.position(end)-out.steady) < 0.02,'Response should settle near F/k.');
