function run_checks
a = model(1,0.8,4,1,12);
assert(abs(a.steady-0.25)<eps,'Static equilibrium must be F/k.');
assert(abs(a.position(end)-a.steady)<0.02,'Baseline must settle.');
low = model(1,0.2,4,1,12);
high = model(1,4,4,1,12);
assert(low.overshoot_percent > high.overshoot_percent,'More damping should reduce overshoot here.');
assert(all(real(a.poles)<0),'Positive m,c,k baseline should be stable.');
disp('P01 checks passed.');
end
