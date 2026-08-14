function run_checks
%RUN_CHECKS Independent numerical, limiting-case, and input checks for P02.
tolerance = 1e-12;

baselineA = model(1,2,1,10,0.02);
baselineB = model(1,2,1,10,0.02);
assert(isequaln(baselineA,baselineB), ...
    'Identical inputs must produce identical deterministic outputs.');
assert(max(abs(baselineA.integrator-baselineA.t)) < tolerance, ...
    'The unit-step integrator must equal independently calculated A*t.');
assert(abs(baselineA.integratorFinal-10) < tolerance, ...
    'A unit input must accumulate to 10 command s after 10 s.');
assert(all(diff(baselineA.firstOrder) >= -tolerance), ...
    'A positive first-order step must be monotone.');
assert(all(baselineA.firstOrder >= -tolerance) && ...
    all(baselineA.firstOrder <= baselineA.firstOrderSteady+tolerance), ...
    'The exact positive first-order response must remain bounded by equilibrium.');

oneTau = model(1,2,1,2,0.02);
expectedOneTau = 1-exp(-1);
assert(abs(oneTau.firstOrder(end)-expectedOneTau) < tolerance, ...
    'At one tau the response must independently equal 1-exp(-1).');
zeroInput = model(0,2,3,10,0.02);
assert(all(zeroInput.integrator == 0) && all(zeroInput.firstOrder == 0), ...
    'Zero input and zero initial state must be a zero-response limiting case.');

doubleInput = model(2,2,1,10,0.02);
assert(max(abs(doubleInput.integrator-2*baselineA.integrator)) < tolerance, ...
    'Amplitude must scale integrator accumulation independently.');
assert(max(abs(doubleInput.firstOrder-2*baselineA.firstOrder)) < tolerance, ...
    'Amplitude must scale first-order output independently.');
fast = model(1,0.5,1,10,0.02);
slow = model(1,5,1,10,0.02);
assert(fast.firstOrder(51) > slow.firstOrder(51), ...
    'Smaller tau must close more of the gap at t=1 s.');
assert(fast.firstOrderSteady == slow.firstOrderSteady, ...
    'Tau must not change the K*A equilibrium.');

fineEulerError = max(abs(baselineA.eulerFirstOrder-baselineA.firstOrder));
assert(fineEulerError < 0.003, ...
    'A fine explicit-Euler interval should remain close to the exact reference.');
broken = model(1,1,1,18,3);
assert(broken.eulerRatio > 2, ...
    'The broken case must violate the explicit-Euler stability interval.');
assert(any(broken.eulerFirstOrder < 0) && broken.maxAbsEuler > 10, ...
    'Coarse Euler must show alternating growth for the stable exact system.');
assert(all(broken.firstOrder >= 0) && all(broken.firstOrder <= 1), ...
    'The exact broken-case reference must remain physically bounded.');

assertAnyError(@() model(NaN,2,1,10,0.02), ...
    'Non-finite amplitude must be rejected.');
assertAnyError(@() model(1,2,Inf,10,0.02), ...
    'Non-finite gain must be rejected.');
assertAnyError(@() model(1+1i,2,1,10,0.02), ...
    'A nonreal amplitude must be rejected.');
assertAnyError(@() model([1 2],2,1,10,0.02), ...
    'A nonscalar amplitude must be rejected.');
assertAnyError(@() model(1,0,1,10,0.02), ...
    'A nonpositive time constant must be rejected.');
assertAnyError(@() model(1,2,1,-10,0.02), ...
    'A nonpositive duration must be rejected.');
assertAnyError(@() model(1,2,1,10,0), ...
    'A nonpositive interval must be rejected.');
nonIntegerGrid = model(1,1,1,0.033,0.011);
assert(nonIntegerGrid.sampleCount == 4 && ...
    all(diff(nonIntegerGrid.t) > 0) && nonIntegerGrid.t(end) == 0.033, ...
    'An integer interval ratio must not create a duplicate final timestamp.');
shortHorizon = model(1,1,1,0.5,2);
assert(shortHorizon.sampleCount == 2 && ...
    abs(shortHorizon.maxInterval-0.5) < tolerance && ...
    abs(shortHorizon.eulerRatio-0.5) < tolerance, ...
    'Euler diagnostics must report the actual endpoint-clipped interval.');
atResourceLimit = model(1,2,1,20,0.001);
assert(atResourceLimit.sampleCount == 20001, ...
    'The declared maximum calculation grid must remain accepted.');
assertErrorId(@() model(1,2,1,100,0.001), ...
    'P02:TooManySamples','An excessive calculation grid must be rejected.');

disp('P02 checks passed: exact invariants, limiting cases, levers, broken case, and input bounds.');
end

function assertAnyError(operation,message)
didError = false;
try
    operation();
catch
    didError = true;
end
assert(didError,message);
end

function assertErrorId(operation,expectedIdentifier,message)
actualIdentifier = '';
try
    operation();
catch exception
    actualIdentifier = exception.identifier;
end
assert(strcmp(actualIdentifier,expectedIdentifier),message);
end
