function out = model(stepAmplitude,tau,gain,tEnd,dt)
%MODEL Deterministic integrator and first-order step responses.
%   The exact calculations expose x_I(t)=A*t and
%   y(t)=K*A*(1-exp(-t/tau)). Explicit Euler is retained only so the lesson
%   can show how an interval that is too coarse invents instability.
arguments
    stepAmplitude (1,1) double {mustBeReal,mustBeFinite} = 1
    tau (1,1) double {mustBeReal,mustBePositive,mustBeFinite} = 2
    gain (1,1) double {mustBeReal,mustBeFinite} = 1
    tEnd (1,1) double {mustBeReal,mustBePositive,mustBeFinite} = 10
    dt (1,1) double {mustBeReal,mustBePositive,mustBeFinite} = 0.02
end

maxSamples = 20001;
intervalCount = floor(tEnd/dt);
lastRegularTime = intervalCount*dt;
timeTolerance = 8*eps(max(tEnd,dt));
appendEnd = intervalCount == 0 || tEnd-lastRegularTime > timeTolerance;
sampleCount = intervalCount + 1 + double(appendEnd);
if sampleCount > maxSamples
    error('P02:TooManySamples', ...
        'Requested %d samples; increase dt or shorten tEnd (maximum %d).', ...
        sampleCount,maxSamples);
end

t = (0:intervalCount)'*dt;
if appendEnd
    t(end+1,1) = tEnd;
else
    t(end) = tEnd;
end
maxInterval = max(diff(t));
u = stepAmplitude*ones(size(t));
integrator = stepAmplitude*t;
firstOrderSteady = gain*stepAmplitude;
firstOrder = firstOrderSteady*(1-exp(-t/tau));
integratorRate = u;
firstOrderRate = (gain*u-firstOrder)/tau;

eulerFirstOrder = zeros(size(t));
for k = 1:numel(t)-1
    interval = t(k+1)-t(k);
    eulerFirstOrder(k+1) = eulerFirstOrder(k) + ...
        interval*(gain*u(k)-eulerFirstOrder(k))/tau;
end

out = struct( ...
    't',t, ...
    'input',u, ...
    'integrator',integrator, ...
    'firstOrder',firstOrder, ...
    'integratorRate',integratorRate, ...
    'firstOrderRate',firstOrderRate, ...
    'eulerFirstOrder',eulerFirstOrder, ...
    'integratorSlope',stepAmplitude, ...
    'integratorFinal',integrator(end), ...
    'firstOrderSteady',firstOrderSteady, ...
    'timeConstant',tau, ...
    'settlingTimeEstimate',4*tau, ...
    'maxInterval',maxInterval, ...
    'eulerRatio',maxInterval/tau, ...
    'maxAbsEuler',max(abs(eulerFirstOrder)), ...
    'sampleCount',sampleCount);
end
