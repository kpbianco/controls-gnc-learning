function out = model(poleReal,poleImag,initialPosition,initialVelocity,tEnd,dt)
%MODEL Exact free motion associated with the pole pair sigma +/- j*omega.
%   The transparent calculation solves
%       x'' - 2*sigma*x' + (sigma^2+omega^2)*x = 0
%   from position x(0) and velocity v(0). poleImag=0 uses the exact
%   repeated-real-pole limit instead of dividing by zero.
arguments
    poleReal (1,1) double {mustBeReal,mustBeFinite} = -0.5
    poleImag (1,1) double {mustBeReal,mustBeFinite,mustBeNonnegative} = 2
    initialPosition (1,1) double {mustBeReal,mustBeFinite} = 1
    initialVelocity (1,1) double {mustBeReal,mustBeFinite} = 0
    tEnd (1,1) double {mustBeReal,mustBePositive,mustBeFinite} = 12
    dt (1,1) double {mustBeReal,mustBePositive,mustBeFinite} = 0.01
end

maxSamples = 20001;
maxAbsExponent = 300;
if abs(poleReal)*tEnd > maxAbsExponent
    error('P03:ExponentRange', ...
        'abs(poleReal)*tEnd must not exceed %g.',maxAbsExponent);
end

intervalCount = floor(tEnd/dt);
lastRegularTime = intervalCount*dt;
timeTolerance = 8*eps(max(tEnd,dt));
appendEnd = intervalCount == 0 || tEnd-lastRegularTime > timeTolerance;
sampleCount = intervalCount + 1 + double(appendEnd);
if sampleCount > maxSamples
    error('P03:TooManySamples', ...
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
exponential = exp(poleReal*t);
repeatedCoefficient = initialVelocity-poleReal*initialPosition;

if poleImag > 0
    sineCoefficient = repeatedCoefficient/poleImag;
    cosineTerm = cos(poleImag*t);
    sineTerm = sin(poleImag*t);
    position = exponential.*(initialPosition*cosineTerm + ...
        sineCoefficient*sineTerm);
    velocity = exponential.*(initialVelocity*cosineTerm + ...
        (poleReal*sineCoefficient-poleImag*initialPosition)*sineTerm);
    initialEnvelope = hypot(initialPosition,sineCoefficient);
    envelope = initialEnvelope*exponential;
    oscillationPeriod = 2*pi/poleImag;
else
    sineCoefficient = 0;
    position = exponential.*(initialPosition+repeatedCoefficient*t);
    velocity = exponential.*(initialVelocity+ ...
        poleReal*repeatedCoefficient*t);
    envelope = exponential.*(abs(initialPosition)+ ...
        abs(repeatedCoefficient)*t);
    initialEnvelope = abs(initialPosition);
    oscillationPeriod = Inf;
end

naturalFrequency = hypot(poleReal,poleImag);
acceleration = 2*poleReal*velocity-naturalFrequency^2*position;
energy = 0.5*velocity.^2 + 0.5*naturalFrequency^2*position.^2;
if any(~isfinite(position)) || any(~isfinite(velocity)) || ...
        any(~isfinite(envelope)) || any(~isfinite(energy))
    error('P03:NonfiniteOutput', ...
        'Inputs produce nonfinite motion; reduce state magnitude or horizon.');
end

if naturalFrequency > 0
    dampingRatio = -poleReal/naturalFrequency;
else
    dampingRatio = NaN;
end
if poleReal < 0
    envelopeTimeConstant = -1/poleReal;
    settlingTimeEstimate = log(50)/(-poleReal);
elseif poleReal > 0
    envelopeTimeConstant = 1/poleReal;
    settlingTimeEstimate = Inf;
else
    envelopeTimeConstant = Inf;
    settlingTimeEstimate = Inf;
end

out = struct( ...
    't',t, ...
    'position',position, ...
    'velocity',velocity, ...
    'acceleration',acceleration, ...
    'envelope',envelope, ...
    'energy',energy, ...
    'poles',[poleReal+1i*poleImag; poleReal-1i*poleImag], ...
    'poleReal',poleReal, ...
    'poleImag',poleImag, ...
    'naturalFrequency',naturalFrequency, ...
    'dampingRatio',dampingRatio, ...
    'oscillationPeriod',oscillationPeriod, ...
    'envelopeTimeConstant',envelopeTimeConstant, ...
    'settlingTimeEstimate',settlingTimeEstimate, ...
    'initialEnvelope',initialEnvelope, ...
    'exponentialScaleRatio',exp(poleReal*tEnd), ...
    'sineCoefficient',sineCoefficient, ...
    'repeatedCoefficient',repeatedCoefficient, ...
    'maxAbsPosition',max(abs(position)), ...
    'initialEnergy',energy(1), ...
    'finalEnergy',energy(end), ...
    'maxInterval',maxInterval, ...
    'sampleCount',sampleCount);
end
