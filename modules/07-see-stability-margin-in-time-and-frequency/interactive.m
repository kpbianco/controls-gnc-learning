function interactive
%INTERACTIVE Move loop gain and actuator lag in matching time/frequency views.
% Retain the P07 model even after launch_lesson removes this folder from the
% MATLAB path or another lesson clears the global name-resolution cache.
modelFunction = @model;
fig = uifigure('Name','P07 Stability Margin in Time and Frequency', ...
    'Position',[80 80 1280 760]);
gridLayout = uigridlayout(fig,[2 6]);
gridLayout.RowHeight = {'1x',125};

axTime = uiaxes(gridLayout);
axTime.Layout.Row = 1;
axTime.Layout.Column = [1 3];
axFrequency = uiaxes(gridLayout);
axFrequency.Layout.Row = 1;
axFrequency.Layout.Column = [4 6];

gainLabel = uilabel(gridLayout,'Text','Loop gain K (1/s^2)', ...
    'WordWrap','on');
gainLabel.Layout.Row = 2;
gainLabel.Layout.Column = 1;
gainControl = uislider(gridLayout,'Limits',[0.25 5.5], ...
    'Value',1,'MajorTicks',[0.25 1 2 3 4 5.5]);
gainControl.Layout.Row = 2;
gainControl.Layout.Column = 2;

lagLabel = uilabel(gridLayout,'Text','Actuator lag tau (s)', ...
    'WordWrap','on');
lagLabel.Layout.Row = 2;
lagLabel.Layout.Column = 3;
lagControl = uislider(gridLayout,'Limits',[0.05 0.8], ...
    'Value',0.2,'MajorTicks',[0.05 0.2 0.4 0.6 0.8]);
lagControl.Layout.Row = 2;
lagControl.Layout.Column = 4;

resetButton = uibutton(gridLayout,'Text','Reset baseline', ...
    'ButtonPushedFcn',@resetBaseline);
resetButton.Layout.Row = 2;
resetButton.Layout.Column = 5;
summary = uilabel(gridLayout,'WordWrap','on');
summary.Layout.Row = 2;
summary.Layout.Column = 6;

gainControl.ValueChangingFcn = @previewGain;
gainControl.ValueChangedFcn = @(~,~) updatePlots([],[]);
lagControl.ValueChangingFcn = @previewLag;
lagControl.ValueChangedFcn = @(~,~) updatePlots([],[]);
updatePlots([],[]);

    function previewGain(~,event)
        updatePlots(event.Value,[]);
    end

    function previewLag(~,event)
        updatePlots([],event.Value);
    end

    function resetBaseline(~,~)
        gainControl.Value = 1;
        lagControl.Value = 0.2;
        updatePlots([],[]);
    end

    function updatePlots(gainPreview,lagPreview)
        if isempty(gainPreview)
            loopGain = gainControl.Value;
        else
            loopGain = gainPreview;
        end
        if isempty(lagPreview)
            actuatorLagSec = lagControl.Value;
        else
            actuatorLagSec = lagPreview;
        end
        viewDt = min(0.01,0.08/max([1 sqrt(loopGain) 1/actuatorLagSec]));
        result = modelFunction(loopGain,actuatorLagSec,20,viewDt);

        cla(axTime);
        plot(axTime,result.t,result.reference*ones(size(result.t)), ...
            'k:','LineWidth',1.2,'DisplayName','Reference r');
        hold(axTime,'on');
        plot(axTime,result.t,result.output,'LineWidth',1.5, ...
            'DisplayName','Output y');
        hold(axTime,'off'); grid(axTime,'on');
        xlabel(axTime,'Time (s)');
        ylabel(axTime,'Output y (normalized)');
        title(axTime,'Closed-loop time response');
        legend(axTime,'Location','southeast');

        cla(axFrequency);
        semilogx(axFrequency,result.omegaRadPerSec, ...
            result.openLoopPhaseDeg,'LineWidth',1.5, ...
            'DisplayName','angle L(j omega)');
        hold(axFrequency,'on');
        plot(axFrequency,result.gainCrossoverRadPerSec, ...
            result.phaseAtGainCrossoverDeg,'o', ...
            'DisplayName','Gain crossover');
        yline(axFrequency,-180,'k:','-180 deg');
        hold(axFrequency,'off'); grid(axFrequency,'on');
        xlabel(axFrequency,'Angular frequency (rad/s)');
        ylabel(axFrequency,'Open-loop phase (deg)');
        title(axFrequency,'Phase reserve at unity magnitude');
        legend(axFrequency,'Location','southwest');

        summary.Text = sprintf(['K %.2f 1/s^2\ntau %.2f s\nwc %.2f rad/s\n' ...
            'PM %.1f deg\nGM %.1f dB\novershoot %.3f'], ...
            loopGain,actuatorLagSec,result.gainCrossoverRadPerSec, ...
            result.phaseMarginDeg,result.gainMarginDb,result.overshoot);
    end
end
