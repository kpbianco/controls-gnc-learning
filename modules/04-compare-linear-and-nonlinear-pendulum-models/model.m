function out = model(initialAngleDeg,initialRateDegPerSec,lengthM,dampingRatio,tEnd,dt)
%MODEL Compare transparent linear and nonlinear pendulum calculations.
%   Both models begin from the same angle and angular rate and obey
%       linear:    theta'' + 2*zeta*wn*theta' + wn^2*theta = 0
%       nonlinear: theta'' + 2*zeta*wn*theta' + wn^2*sin(theta) = 0
%   where wn = sqrt(g/lengthM). A fixed-step RK4 calculation keeps the
%   governing restoring terms visible without an ODE or toolbox black box.
arguments
    initialAngleDeg (1,1) double {mustBeReal,mustBeFinite} = 20
    initialRateDegPerSec (1,1) double {mustBeReal,mustBeFinite} = 0
    lengthM (1,1) double {mustBeReal,mustBePositive,mustBeFinite} = 1
    dampingRatio (1,1) double {mustBeReal,mustBeNonnegative,mustBeFinite} = 0.02
    tEnd (1,1) double {mustBeReal,mustBePositive,mustBeFinite} = 12
    dt (1,1) double {mustBeReal,mustBePositive,mustBeFinite} = 0.01
end

if abs(initialAngleDeg) >= 180
    error('P04:InitialAngleRange', ...
        'abs(initialAngleDeg) must be less than 180 degrees.');
end
if abs(initialRateDegPerSec) > 720
    error('P04:InitialRateRange', ...
        'abs(initialRateDegPerSec) must not exceed 720 deg/s.');
end
if lengthM < 0.05 || lengthM > 20
    error('P04:LengthRange','lengthM must be between 0.05 and 20 m.');
end
if dampingRatio > 2
    error('P04:DampingRange','dampingRatio must not exceed 2.');
end

maxSamples = 20001;
intervalCount = floor(tEnd/dt);
lastRegularTime = intervalCount*dt;
timeTolerance = 8*eps(max(tEnd,dt));
appendEnd = intervalCount == 0 || tEnd-lastRegularTime > timeTolerance;
sampleCount = intervalCount + 1 + double(appendEnd);
if sampleCount > maxSamples
    error('P04:TooManySamples', ...
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

gravityMPerSec2 = 9.81;
naturalFrequencyRadPerSec = sqrt(gravityMPerSec2/lengthM);
maxDimensionlessStep = 0.075;
if naturalFrequencyRadPerSec*maxInterval > maxDimensionlessStep
    error('P04:TimeResolution', ...
        'wn*maxInterval must not exceed %.2f; reduce dt for this length.', ...
        maxDimensionlessStep);
end

initialAngleRad = initialAngleDeg*pi/180;
initialRateRadPerSec = initialRateDegPerSec*pi/180;
linearAngleRad = zeros(sampleCount,1);
nonlinearAngleRad = zeros(sampleCount,1);
linearRateRadPerSec = zeros(sampleCount,1);
nonlinearRateRadPerSec = zeros(sampleCount,1);
linearAngleRad(1) = initialAngleRad;
nonlinearAngleRad(1) = initialAngleRad;
linearRateRadPerSec(1) = initialRateRadPerSec;
nonlinearRateRadPerSec(1) = initialRateRadPerSec;

for k = 1:sampleCount-1
    step = t(k+1)-t(k);
    [linearAngleRad(k+1),linearRateRadPerSec(k+1)] = rk4Step( ...
        linearAngleRad(k),linearRateRadPerSec(k),step, ...
        naturalFrequencyRadPerSec,dampingRatio,false);
    [nonlinearAngleRad(k+1),nonlinearRateRadPerSec(k+1)] = rk4Step( ...
        nonlinearAngleRad(k),nonlinearRateRadPerSec(k),step, ...
        naturalFrequencyRadPerSec,dampingRatio,true);
end

if any(~isfinite(linearAngleRad)) || any(~isfinite(nonlinearAngleRad)) || ...
        any(~isfinite(linearRateRadPerSec)) || ...
        any(~isfinite(nonlinearRateRadPerSec))
    error('P04:NonfiniteOutput', ...
        'Inputs produce nonfinite motion; reduce the state or horizon.');
end

linearAngleDeg = linearAngleRad*180/pi;
nonlinearAngleDeg = nonlinearAngleRad*180/pi;
angleErrorDeg = nonlinearAngleDeg-linearAngleDeg;
linearSpecificEnergyJPerKg = 0.5*(lengthM*linearRateRadPerSec).^2 + ...
    0.5*gravityMPerSec2*lengthM*linearAngleRad.^2;
nonlinearSpecificEnergyJPerKg = 0.5*(lengthM*nonlinearRateRadPerSec).^2 + ...
    gravityMPerSec2*lengthM*(1-cos(nonlinearAngleRad));

comparisonLimitRad = max([abs(linearAngleRad);abs(nonlinearAngleRad);pi/180]);
restoringAngleRad = linspace(-comparisonLimitRad,comparisonLimitRad,181)';
linearRestoringAccelerationRadPerSec2 = ...
    -naturalFrequencyRadPerSec^2*restoringAngleRad;
nonlinearRestoringAccelerationRadPerSec2 = ...
    -naturalFrequencyRadPerSec^2*sin(restoringAngleRad);

rootOffset = naturalFrequencyRadPerSec*sqrt(complex(dampingRatio^2-1));
linearPolesPerSec = [-dampingRatio*naturalFrequencyRadPerSec+rootOffset; ...
    -dampingRatio*naturalFrequencyRadPerSec-rootOffset];
smallAnglePeriodSec = 2*pi/naturalFrequencyRadPerSec;
if dampingRatio < 1
    dampedLinearPeriodSec = smallAnglePeriodSec/sqrt(1-dampingRatio^2);
else
    dampedLinearPeriodSec = Inf;
end
linearFirstZeroSec = firstZeroCrossing(t,linearAngleRad);
nonlinearFirstZeroSec = firstZeroCrossing(t,nonlinearAngleRad);
if isfinite(linearFirstZeroSec) && isfinite(nonlinearFirstZeroSec)
    nonlinearZeroDelayPercent = ...
        100*(nonlinearFirstZeroSec-linearFirstZeroSec)/linearFirstZeroSec;
else
    nonlinearZeroDelayPercent = NaN;
end

out = struct( ...
    't',t, ...
    'linearAngleRad',linearAngleRad, ...
    'nonlinearAngleRad',nonlinearAngleRad, ...
    'linearAngleDeg',linearAngleDeg, ...
    'nonlinearAngleDeg',nonlinearAngleDeg, ...
    'linearRateRadPerSec',linearRateRadPerSec, ...
    'nonlinearRateRadPerSec',nonlinearRateRadPerSec, ...
    'angleErrorDeg',angleErrorDeg, ...
    'linearSpecificEnergyJPerKg',linearSpecificEnergyJPerKg, ...
    'nonlinearSpecificEnergyJPerKg',nonlinearSpecificEnergyJPerKg, ...
    'restoringAngleRad',restoringAngleRad, ...
    'linearRestoringAccelerationRadPerSec2',linearRestoringAccelerationRadPerSec2, ...
    'nonlinearRestoringAccelerationRadPerSec2',nonlinearRestoringAccelerationRadPerSec2, ...
    'initialAngleDeg',initialAngleDeg, ...
    'initialRateDegPerSec',initialRateDegPerSec, ...
    'lengthM',lengthM, ...
    'dampingRatio',dampingRatio, ...
    'gravityMPerSec2',gravityMPerSec2, ...
    'naturalFrequencyRadPerSec',naturalFrequencyRadPerSec, ...
    'linearPolesPerSec',linearPolesPerSec, ...
    'smallAnglePeriodSec',smallAnglePeriodSec, ...
    'dampedLinearPeriodSec',dampedLinearPeriodSec, ...
    'linearFirstZeroSec',linearFirstZeroSec, ...
    'nonlinearFirstZeroSec',nonlinearFirstZeroSec, ...
    'nonlinearZeroDelayPercent',nonlinearZeroDelayPercent, ...
    'initialLinearAccelerationRadPerSec2', ...
        -naturalFrequencyRadPerSec^2*initialAngleRad - ...
        2*dampingRatio*naturalFrequencyRadPerSec*initialRateRadPerSec, ...
    'initialNonlinearAccelerationRadPerSec2', ...
        -naturalFrequencyRadPerSec^2*sin(initialAngleRad) - ...
        2*dampingRatio*naturalFrequencyRadPerSec*initialRateRadPerSec, ...
    'maxAbsErrorDeg',max(abs(angleErrorDeg)), ...
    'rmsErrorDeg',sqrt(mean(angleErrorDeg.^2)), ...
    'maxRestoringDifferenceRadPerSec2',max(abs( ...
        nonlinearRestoringAccelerationRadPerSec2- ...
        linearRestoringAccelerationRadPerSec2)), ...
    'maxInterval',maxInterval, ...
    'sampleCount',sampleCount);
end

function [nextAngle,nextRate] = rk4Step(angle,rate,step,wn,zeta,useNonlinear)
% One explicit fourth-order Runge-Kutta step for [angle; angular rate].
[k1Angle,k1Rate] = derivative(angle,rate,wn,zeta,useNonlinear);
[k2Angle,k2Rate] = derivative(angle+0.5*step*k1Angle, ...
    rate+0.5*step*k1Rate,wn,zeta,useNonlinear);
[k3Angle,k3Rate] = derivative(angle+0.5*step*k2Angle, ...
    rate+0.5*step*k2Rate,wn,zeta,useNonlinear);
[k4Angle,k4Rate] = derivative(angle+step*k3Angle, ...
    rate+step*k3Rate,wn,zeta,useNonlinear);
nextAngle = angle + step*(k1Angle+2*k2Angle+2*k3Angle+k4Angle)/6;
nextRate = rate + step*(k1Rate+2*k2Rate+2*k3Rate+k4Rate)/6;
end

function [angleDerivative,rateDerivative] = derivative(angle,rate,wn,zeta,useNonlinear)
angleDerivative = rate;
if useNonlinear
    restoringAngle = sin(angle);
else
    restoringAngle = angle;
end
rateDerivative = -2*zeta*wn*rate-wn^2*restoringAngle;
end

function crossingTime = firstZeroCrossing(t,angle)
crossingTime = NaN;
nonzeroIndex = find(angle ~= 0,1,'first');
if isempty(nonzeroIndex)
    return;
end
direction = sign(angle(nonzeroIndex));
for k = nonzeroIndex+1:numel(angle)
    if direction*angle(k) <= 0
        before = abs(angle(k-1));
        after = abs(angle(k));
        crossingTime = t(k-1) + (t(k)-t(k-1))*before/(before+after);
        return;
    end
end
end
