function out = model(m,c,k,force,tEnd)
%MODEL Mass-spring-damper step response.
arguments
    m (1,1) double {mustBePositive} = 1
    c (1,1) double {mustBeNonnegative} = 0.8
    k (1,1) double {mustBePositive} = 4
    force (1,1) double = 1
    tEnd (1,1) double {mustBePositive} = 12
end
ode = @(t,x) [x(2); (force - c*x(2) - k*x(1))/m];
t = linspace(0,tEnd,1200);
[~,x] = ode45(ode,t,[0;0]);
wn = sqrt(k/m);
zeta = c/(2*sqrt(k*m));
steady = force/k;
out = struct('t',t(:),'position',x(:,1),'velocity',x(:,2), ...
    'wn',wn,'zeta',zeta,'steady',steady,'poles',roots([m c k]));
out.peak = max(out.position);
out.overshoot_percent = max(0,(out.peak-steady)/max(abs(steady),eps)*100);
end
