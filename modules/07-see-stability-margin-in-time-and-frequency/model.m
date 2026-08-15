function out = model(loopGain,actuatorLagSec,tEnd,dt)
%MODEL Evaluate one transparent feedback loop in time and frequency.
%   With plant damping rate b=1/s, the open loop is
%       L(s)=K/[s(s+b)(tau*s+1)], with K in 1/s^2.
%   The matching normalized-output time model is
%       y' = v,  v' = a-b*v,  tau*a' = K*(r-y)-a.
%   When tau is zero, a=K*(r-y) is applied without actuator dynamics.
arguments
    loopGain (1,1) double {mustBeReal,mustBeFinite,mustBeNonnegative} = 1
    actuatorLagSec (1,1) double {mustBeReal,mustBeFinite,mustBeNonnegative} = 0.2
    tEnd (1,1) double {mustBeReal,mustBeFinite,mustBePositive} = 20
    dt (1,1) double {mustBeReal,mustBeFinite,mustBePositive} = 0.01
end

if loopGain > 25
    error('P07:LoopGainRange','loopGain must not exceed 25 1/s^2.');
end
if actuatorLagSec > 2
    error('P07:ActuatorLagRange', ...
        'actuatorLagSec must not exceed 2 s.');
end
if tEnd > 40
    error('P07:HorizonRange','tEnd must not exceed 40 s.');
end

maxSamples = 20001;
intervalCount = floor(tEnd/dt);
lastRegularTime = intervalCount*dt;
timeTolerance = 8*eps(max(tEnd,dt));
appendEnd = intervalCount == 0 || tEnd-lastRegularTime > timeTolerance;
sampleCount = intervalCount + 1 + double(appendEnd);
if sampleCount > maxSamples
    error('P07:TooManySamples', ...
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
characteristicRatePerSec = max(1,sqrt(loopGain));
if actuatorLagSec > 0
    characteristicRatePerSec = max(characteristicRatePerSec,1/actuatorLagSec);
end
maxDimensionlessStep = 0.1;
if characteristicRatePerSec*maxInterval > ...
        maxDimensionlessStep+16*eps(maxDimensionlessStep)
    error('P07:TimeResolution', ...
        'Characteristic rate times maxInterval must not exceed %.2f.', ...
        maxDimensionlessStep);
end

reference = 1;
plantDampingRatePerSec = 1;
output = zeros(sampleCount,1);
velocityPerSec = zeros(sampleCount,1);
actuator = zeros(sampleCount,1);
if actuatorLagSec > 0
    state = [0;0;0];
else
    state = [0;0];
    actuator(1) = loopGain*reference;
end
responseLimit = 1e4;
for k = 1:sampleCount-1
    step = t(k+1)-t(k);
    k1 = stateRate(state,loopGain,actuatorLagSec, ...
        plantDampingRatePerSec,reference);
    k2 = stateRate(state+0.5*step*k1,loopGain,actuatorLagSec, ...
        plantDampingRatePerSec,reference);
    k3 = stateRate(state+0.5*step*k2,loopGain,actuatorLagSec, ...
        plantDampingRatePerSec,reference);
    k4 = stateRate(state+step*k3,loopGain,actuatorLagSec, ...
        plantDampingRatePerSec,reference);
    state = state + step*(k1+2*k2+2*k3+k4)/6;
    if any(~isfinite(state)) || max(abs(state)) > responseLimit
        error('P07:ResponseBound', ...
            'The requested loop response exceeds the bounded learning view.');
    end
    output(k+1) = state(1);
    velocityPerSec(k+1) = state(2);
    if actuatorLagSec > 0
        actuator(k+1) = state(3);
    else
        actuator(k+1) = loopGain*(reference-state(1));
    end
end

trackingError = reference-output;
controllerCommand = loopGain*trackingError;
accelerationPerSec2 = actuator- ...
    plantDampingRatePerSec*velocityPerSec;
if actuatorLagSec > 0
    actuatorRatePerSec = (controllerCommand-actuator)/actuatorLagSec;
else
    actuatorRatePerSec = zeros(sampleCount,1);
end

omegaRadPerSec = logspace(-2,2,401)';
openLoopMagnitude = loopGain./(omegaRadPerSec.* ...
    sqrt(plantDampingRatePerSec^2+omegaRadPerSec.^2).* ...
    sqrt(1+(actuatorLagSec*omegaRadPerSec).^2));
openLoopMagnitudeDb = 20*log10(max(openLoopMagnitude,realmin));
openLoopPhaseDeg = -90- ...
    atan(omegaRadPerSec/plantDampingRatePerSec)*180/pi- ...
    atan(actuatorLagSec*omegaRadPerSec)*180/pi;

if loopGain == 0
    gainCrossoverRadPerSec = 0;
    phaseAtGainCrossoverDeg = NaN;
    phaseMarginDeg = Inf;
else
    gainCrossoverRadPerSec = findGainCrossover( ...
        loopGain,actuatorLagSec,plantDampingRatePerSec);
    phaseAtGainCrossoverDeg = -90- ...
        atan(gainCrossoverRadPerSec/plantDampingRatePerSec)*180/pi- ...
        atan(actuatorLagSec*gainCrossoverRadPerSec)*180/pi;
    phaseMarginDeg = 180+phaseAtGainCrossoverDeg;
end
if actuatorLagSec == 0
    phaseCrossoverRadPerSec = Inf;
    criticalLoopGain = Inf;
    gainMarginRatio = Inf;
    gainMarginDb = Inf;
else
    phaseCrossoverRadPerSec = ...
        sqrt(plantDampingRatePerSec/actuatorLagSec);
    criticalLoopGain = plantDampingRatePerSec* ...
        (1+plantDampingRatePerSec*actuatorLagSec)/actuatorLagSec;
    if loopGain == 0
        gainMarginRatio = Inf;
    else
        gainMarginRatio = criticalLoopGain/loopGain;
    end
    gainMarginDb = 20*log10(gainMarginRatio);
end

if loopGain == 0
    stabilityClass = 'uncontrolled: pole at origin';
    closedLoopStable = false;
elseif isinf(criticalLoopGain) || loopGain < criticalLoopGain
    stabilityClass = 'stable: positive margin';
    closedLoopStable = true;
elseif abs(loopGain-criticalLoopGain) <= ...
        64*eps(max(loopGain,criticalLoopGain))
    stabilityClass = 'marginal: zero margin';
    closedLoopStable = false;
else
    stabilityClass = 'unstable: negative margin';
    closedLoopStable = false;
end

overshoot = max(max(output-reference),0);
settlingBand = 0.02;
outsideBand = find(abs(trackingError) > settlingBand);
if isempty(outsideBand)
    settlingTimeSec = 0;
elseif outsideBand(end) == sampleCount || ~closedLoopStable
    settlingTimeSec = Inf;
else
    settlingTimeSec = t(outsideBand(end)+1);
end
riseIndex = find(output >= 0.9*reference,1,'first');
if isempty(riseIndex)
    riseTimeSec = Inf;
else
    riseTimeSec = t(riseIndex);
end

out = struct( ...
    't',t, ...
    'reference',reference, ...
    'output',output, ...
    'velocityPerSec',velocityPerSec, ...
    'accelerationPerSec2',accelerationPerSec2, ...
    'trackingError',trackingError, ...
    'controllerCommand',controllerCommand, ...
    'actuator',actuator, ...
    'actuatorRatePerSec',actuatorRatePerSec, ...
    'loopGain',loopGain, ...
    'actuatorLagSec',actuatorLagSec, ...
    'plantDampingRatePerSec',plantDampingRatePerSec, ...
    'omegaRadPerSec',omegaRadPerSec, ...
    'openLoopMagnitude',openLoopMagnitude, ...
    'openLoopMagnitudeDb',openLoopMagnitudeDb, ...
    'openLoopPhaseDeg',openLoopPhaseDeg, ...
    'gainCrossoverRadPerSec',gainCrossoverRadPerSec, ...
    'phaseAtGainCrossoverDeg',phaseAtGainCrossoverDeg, ...
    'phaseMarginDeg',phaseMarginDeg, ...
    'phaseCrossoverRadPerSec',phaseCrossoverRadPerSec, ...
    'criticalLoopGain',criticalLoopGain, ...
    'gainMarginRatio',gainMarginRatio, ...
    'gainMarginDb',gainMarginDb, ...
    'closedLoopStable',closedLoopStable, ...
    'stabilityClass',stabilityClass, ...
    'overshoot',overshoot, ...
    'settlingTimeSec',settlingTimeSec, ...
    'riseTimeSec',riseTimeSec, ...
    'maxAbsOutput',max(abs(output)), ...
    'maxAbsActuator',max(abs(actuator)), ...
    'characteristicRatePerSec',characteristicRatePerSec, ...
    'maxDimensionlessStep',maxDimensionlessStep, ...
    'maxInterval',maxInterval, ...
    'sampleCount',sampleCount);
end

function rate = stateRate(state,loopGain,actuatorLagSec, ...
    plantDampingRatePerSec,reference)
output = state(1);
velocityPerSec = state(2);
controllerCommand = loopGain*(reference-output);
if actuatorLagSec > 0
    actuator = state(3);
    actuatorRatePerSec = (controllerCommand-actuator)/actuatorLagSec;
    rate = [velocityPerSec;actuator- ...
        plantDampingRatePerSec*velocityPerSec;actuatorRatePerSec];
else
    actuator = controllerCommand;
    rate = [velocityPerSec;actuator- ...
        plantDampingRatePerSec*velocityPerSec];
end
end

function crossover = findGainCrossover(loopGain,actuatorLagSec, ...
    plantDampingRatePerSec)
lower = 0;
% Since the denominator is at least b*omega, K/b is a valid upper
% bracket for every finite positive K, including values far below eps.
upper = loopGain/plantDampingRatePerSec;
for iteration = 1:80
    midpoint = 0.5*(lower+upper);
    if magnitudeDenominator(midpoint,actuatorLagSec, ...
            plantDampingRatePerSec) < loopGain
        lower = midpoint;
    else
        upper = midpoint;
    end
end
crossover = 0.5*(lower+upper);
end

function denominator = magnitudeDenominator(omega,actuatorLagSec, ...
    plantDampingRatePerSec)
denominator = omega*sqrt(plantDampingRatePerSec^2+omega^2)* ...
    sqrt(1+(actuatorLagSec*omega)^2);
end
