%% P01 - Watch a Mass-Spring-Damper Respond
% Guiding question:
% How do mass, stiffness, and damping determine visible motion?
%
% Mental model:
% A mass stores momentum, a spring stores potential energy, and a damper removes energy. Their balance determines oscillation, settling, and overshoot.

%% Read the baseline lesson
disp('How do mass, stiffness, and damping determine visible motion?');
disp('A mass stores momentum, a spring stores potential energy, and a damper removes energy. Their balance determines oscillation, settling, and overshoot.');

%% Run the deterministic experiment
experiment;

%% Open the live lever panel
% Move one control at a time and connect the visible change to the model.
interactive;
