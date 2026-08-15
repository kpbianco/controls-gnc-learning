%% P17 - Balance State Error and Control Effort with LQR
% Guiding question:
% What inputs, observable effects, and failure modes matter when you balance State Error and Control Effort with LQR?
%
% P16 produced a covariance-weighted position/rate estimate. P17 treats
% that estimated state as the error to regulate and makes the design
% tradeoff between state error and commanded acceleration explicit.

%% Observe the deterministic baseline
% Run experiment one section at a time. Before its baseline, make one
% prediction: when position error receives more weight while effort price
% stays fixed, will initial commanded acceleration rise or fall?
experiment;

%% Move one lever at a time
% Sweep only q_p with r fixed. Reset q_p, then sweep only r. Compare state
% trajectories and command metrics rather than interpreting gain alone.

%% Explain the mechanism from the cost and Riccati equation
% Q prices normalized position and rate errors. R prices normalized input.
% The Riccati matrix P represents future cost, and
% K=(R+B'*P*B)^(-1)*B'*P*A chooses the least-cost command for that model.

%% Break, recover, check, and teach back
% Disconnect the actuator after designing for full authority. Commanded
% effort remains, applied effort vanishes, and position cannot move. Restore
% effectiveness to one, run run_checks, then give the checks.md teach-back.
