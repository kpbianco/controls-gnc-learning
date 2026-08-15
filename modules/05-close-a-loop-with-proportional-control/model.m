function out = model(proportionalGain,plantTimeConstantSec,plantGainMPerCommand, ...
    referenceM,initialOutputM,feedbackSign,tEnd,dt)
%MODEL Propagate a transparent proportional-feedback first-order loop.
%   The plant and controller are
%       tau*y' = -y + G*u
%       u = Kp*(r + feedbackSign*y).
%   feedbackSign = -1 subtracts the measurement (negative feedback), while
%   feedbackSign = +1 deliberately reverses it. The constant-reference
%   closed-loop equation is propagated exactly over every requested interval.
arguments
    proportionalGain (1,1) double {mustBeReal,mustBeNonnegative,mustBeFinite} = 2
    plantTimeConstantSec (1,1) double {mustBeReal,mustBePositive,mustBeFinite} = 1
    plantGainMPerCommand (1,1) double {mustBeReal,mustBePositive,mustBeFinite} = 1
    referenceM (1,1) double {mustBeReal,mustBeFinite} = 1
    initialOutputM (1,1) double {mustBeReal,mustBeFinite} = 0
    feedbackSign (1,1) double {mustBeReal,mustBeFinite} = -1
    tEnd (1,1) double {mustBeReal,mustBePositive,mustBeFinite} = 5
    dt (1,1) double {mustBeReal,mustBePositive,mustBeFinite} = 0.01
end

if proportionalGain > 50
    error('P05:GainRange','proportionalGain must not exceed 50.');
end
if plantTimeConstantSec < 0.05 || plantTimeConstantSec > 20
    error('P05:TimeConstantRange', ...
        'plantTimeConstantSec must be between 0.05 and 20 s.');
end
if plantGainMPerCommand < 0.05 || plantGainMPerCommand > 10
    error('P05:PlantGainRange', ...
        'plantGainMPerCommand must be between 0.05 and 10 m/command.');
end
if abs(referenceM) > 100 || abs(initialOutputM) > 100
    error('P05:SignalRange', ...
        'referenceM and initialOutputM must have magnitude at most 100 m.');
end
if feedbackSign ~= -1 && feedbackSign ~= 1
    error('P05:FeedbackSign', ...
        'feedbackSign must be -1 for subtraction or +1 for the broken addition.');
end
if tEnd > 100
    error('P05:HorizonRange','tEnd must not exceed 100 s.');
end

loopGain = plantGainMPerCommand*proportionalGain;
closedLoopPolePerSec = (feedbackSign*loopGain-1)/plantTimeConstantSec;
inputRateMPerSec = loopGain*referenceM/plantTimeConstantSec;
maxGrowthExponent = log(1e8);
if closedLoopPolePerSec > 0 && ...
        closedLoopPolePerSec*tEnd > maxGrowthExponent
    error('P05:ResponseBound', ...
        'Positive-feedback growth exceeds the bounded learning view.');
end

maxSamples = 20001;
intervalCount = floor(tEnd/dt);
lastRegularTime = intervalCount*dt;
timeTolerance = 8*eps(max(tEnd,dt));
appendEnd = intervalCount == 0 || tEnd-lastRegularTime > timeTolerance;
sampleCount = intervalCount + 1 + double(appendEnd);
if sampleCount > maxSamples
    error('P05:TooManySamples', ...
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
maxPoleStep = 0.1;
if abs(closedLoopPolePerSec)*maxInterval > maxPoleStep
    error('P05:TimeResolution', ...
        '|closed-loop pole|*maxInterval must not exceed %.1f for a visible transient.', ...
        maxPoleStep);
end

outputM = zeros(sampleCount,1);
outputM(1) = initialOutputM;
if closedLoopPolePerSec == 0
    equilibriumOutputM = NaN;
    for k = 1:sampleCount-1
        step = t(k+1)-t(k);
        outputM(k+1) = outputM(k) + inputRateMPerSec*step;
    end
else
    equilibriumOutputM = -inputRateMPerSec/closedLoopPolePerSec;
    for k = 1:sampleCount-1
        step = t(k+1)-t(k);
        poleStep = closedLoopPolePerSec*step;
        outputM(k+1) = outputM(k)*exp(poleStep) + ...
            inputRateMPerSec*expm1(poleStep)/closedLoopPolePerSec;
    end
end

if any(~isfinite(outputM)) || max(abs(outputM)) > 1e9
    error('P05:ResponseBound', ...
        'The requested loop exceeds the bounded learning view.');
end

trackingErrorM = referenceM-outputM;
controllerInputM = referenceM+feedbackSign*outputM;
controlCommand = proportionalGain*controllerInputM;
outputRateMPerSec = ...
    (-outputM+plantGainMPerCommand*controlCommand)/plantTimeConstantSec;
closedLoopStable = closedLoopPolePerSec < 0;
if closedLoopStable
    closedLoopTimeConstantSec = -1/closedLoopPolePerSec;
    predictedSteadyStateOutputM = equilibriumOutputM;
    predictedSteadyStateErrorM = referenceM-equilibriumOutputM;
    twoPercentSettlingTimeSec = ...
        -log(0.02)*closedLoopTimeConstantSec;
else
    closedLoopTimeConstantSec = Inf;
    predictedSteadyStateOutputM = NaN;
    predictedSteadyStateErrorM = NaN;
    twoPercentSettlingTimeSec = Inf;
end

if feedbackSign == -1
    feedbackLabel = 'negative: measurement subtracted';
else
    feedbackLabel = 'positive: measurement added';
end

out = struct( ...
    't',t, ...
    'outputM',outputM, ...
    'trackingErrorM',trackingErrorM, ...
    'controllerInputM',controllerInputM, ...
    'controlCommand',controlCommand, ...
    'outputRateMPerSec',outputRateMPerSec, ...
    'proportionalGain',proportionalGain, ...
    'plantTimeConstantSec',plantTimeConstantSec, ...
    'plantGainMPerCommand',plantGainMPerCommand, ...
    'referenceM',referenceM, ...
    'initialOutputM',initialOutputM, ...
    'feedbackSign',feedbackSign, ...
    'feedbackLabel',feedbackLabel, ...
    'loopGain',loopGain, ...
    'closedLoopPolePerSec',closedLoopPolePerSec, ...
    'closedLoopStable',closedLoopStable, ...
    'closedLoopTimeConstantSec',closedLoopTimeConstantSec, ...
    'twoPercentSettlingTimeSec',twoPercentSettlingTimeSec, ...
    'equilibriumOutputM',equilibriumOutputM, ...
    'predictedSteadyStateOutputM',predictedSteadyStateOutputM, ...
    'predictedSteadyStateErrorM',predictedSteadyStateErrorM, ...
    'initialControlCommand',controlCommand(1), ...
    'initialOutputRateMPerSec',outputRateMPerSec(1), ...
    'finalTrackingErrorM',trackingErrorM(end), ...
    'maxAbsControlCommand',max(abs(controlCommand)), ...
    'maxAbsOutputM',max(abs(outputM)), ...
    'maxPoleStep',maxPoleStep, ...
    'maxInterval',maxInterval, ...
    'sampleCount',sampleCount);
end
