function interactive
%INTERACTIVE Move feedback gain and disturbance frequency independently.
% Retain the P08 model even after launch_lesson removes this folder from the
% MATLAB path or another lesson clears the global name-resolution cache.
modelFunction = @model;
fig = uifigure('Name','P08 Disturbance Rejection with Feedback', ...
    'Position',[80 80 1280 760]);
gridLayout = uigridlayout(fig,[2 6]);
gridLayout.RowHeight = {'1x',130};

axTime = uiaxes(gridLayout);
axTime.Layout.Row = 1;
axTime.Layout.Column = [1 3];
axFrequency = uiaxes(gridLayout);
axFrequency.Layout.Row = 1;
axFrequency.Layout.Column = [4 6];

gainLabel = uilabel(gridLayout,'Text','Feedback gain K (dimensionless)', ...
    'WordWrap','on');
gainLabel.Layout.Row = 2;
gainLabel.Layout.Column = 1;
gainControl = uislider(gridLayout,'Limits',[0 10],'Value',4, ...
    'MajorTicks',[0 1 4 7 10]);
gainControl.Layout.Row = 2;
gainControl.Layout.Column = 2;

frequencyLabel = uilabel(gridLayout, ...
    'Text','Disturbance frequency omega (rad/s; 0 = step)', ...
    'WordWrap','on');
frequencyLabel.Layout.Row = 2;
frequencyLabel.Layout.Column = 3;
frequencyControl = uislider(gridLayout,'Limits',[0 10],'Value',0, ...
    'MajorTicks',[0 1 2 5 10]);
frequencyControl.Layout.Row = 2;
frequencyControl.Layout.Column = 4;

resetButton = uibutton(gridLayout,'Text','Reset baseline');
resetButton.Layout.Row = 2;
resetButton.Layout.Column = 5;
summary = uilabel(gridLayout,'WordWrap','on');
summary.Layout.Row = 2;
summary.Layout.Column = 6;

gainControl.ValueChangingFcn = @(~,event) ...
    redraw(event.Value,frequencyControl.Value);
frequencyControl.ValueChangingFcn = @(~,event) ...
    redraw(gainControl.Value,event.Value);
gainControl.ValueChangedFcn = @(~,~) ...
    redraw(gainControl.Value,frequencyControl.Value);
frequencyControl.ValueChangedFcn = @(~,~) ...
    redraw(gainControl.Value,frequencyControl.Value);
resetButton.ButtonPushedFcn = @(~,~) resetBaseline();
redraw(gainControl.Value,frequencyControl.Value);

    function resetBaseline
        gainControl.Value = 4;
        frequencyControl.Value = 0;
        redraw(4,0);
    end

    function redraw(feedbackGain,disturbanceFrequencyRadPerSec)
        viewDt = min(0.01,0.08/max(1+feedbackGain, ...
            disturbanceFrequencyRadPerSec));
        result = modelFunction(feedbackGain,1, ...
            disturbanceFrequencyRadPerSec,0,12,viewDt);

        cla(axTime);
        plot(axTime,result.t,result.disturbanceInput,'k--','LineWidth',1.1, ...
            'DisplayName','Disturbance d');
        hold(axTime,'on');
        plot(axTime,result.t,result.trueOutput,'LineWidth',1.6, ...
            'DisplayName','True output y');
        plot(axTime,result.t,result.controlEffort,'LineWidth',1.2, ...
            'DisplayName','Control effort u');
        hold(axTime,'off'); grid(axTime,'on');
        xlabel(axTime,'Time (s)'); ylabel(axTime,'Amplitude (output)');
        title(axTime,'Time view: disturbance, output, and correction');
        legend(axTime,'Location','best');

        cla(axFrequency);
        relativeRatio = result.closedLoopDisturbanceMagnitude./ ...
            result.openLoopDisturbanceMagnitude;
        semilogx(axFrequency,result.omegaRadPerSec,relativeRatio, ...
            'LineWidth',1.6,'DisplayName','Feedback rejection ratio');
        hold(axFrequency,'on');
        selectedRatio = sqrt(1+disturbanceFrequencyRadPerSec^2)/ ...
            sqrt((1+feedbackGain)^2+disturbanceFrequencyRadPerSec^2);
        selectedFrequency = max(disturbanceFrequencyRadPerSec,0.01);
        plot(axFrequency,selectedFrequency,selectedRatio,'o', ...
            'MarkerSize',8,'DisplayName','Selected disturbance');
        hold(axFrequency,'off'); grid(axFrequency,'on');
        ylim(axFrequency,[0 1.05]);
        xlabel(axFrequency,'Disturbance frequency (rad/s)');
        ylabel(axFrequency,'With-feedback / no-feedback ratio');
        title(axFrequency,'Additional attenuation supplied by feedback');
        legend(axFrequency,'Location','southeast');

        if disturbanceFrequencyRadPerSec == 0
            inputKind = 'step';
        else
            inputKind = sprintf('sine at %.2f rad/s', ...
                disturbanceFrequencyRadPerSec);
        end
        summary.Text = sprintf([ ...
            '%s | |Y| = %.3f output | feedback ratio %.3f | ' ...
            'attenuation %.2f dB | tau_cl = %.3f s'],inputKind, ...
            result.theoreticalOutputAmplitude,result.feedbackRejectionRatio, ...
            result.additionalAttenuationDb,result.closedLoopTimeConstantSec);
    end
end
