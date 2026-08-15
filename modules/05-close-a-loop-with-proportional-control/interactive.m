function interactive
%INTERACTIVE Move proportional gain and plant speed one lever at a time.
% Retain the P05 model even after launch_lesson removes this folder from the
% MATLAB path or another lesson clears the global name-resolution cache.
modelFunction = @model;
fig = uifigure('Name','P05 Proportional Feedback Loop', ...
    'Position',[100 100 1150 720]);
gridLayout = uigridlayout(fig,[2 6]);
gridLayout.RowHeight = {'1x',120};

axOutput = uiaxes(gridLayout);
axOutput.Layout.Row = 1;
axOutput.Layout.Column = [1 4];
axCommand = uiaxes(gridLayout);
axCommand.Layout.Row = 1;
axCommand.Layout.Column = [5 6];

gainLabel = uilabel(gridLayout,'Text','Proportional gain Kp (command/m)', ...
    'WordWrap','on');
gainLabel.Layout.Row = 2;
gainLabel.Layout.Column = 1;
gainControl = uislider(gridLayout,'Limits',[0 8], ...
    'Value',2,'MajorTicks',[0 0.5 1 2 4 8]);
gainControl.Layout.Row = 2;
gainControl.Layout.Column = 2;

timeLabel = uilabel(gridLayout,'Text','Plant time constant tau (s)', ...
    'WordWrap','on');
timeLabel.Layout.Row = 2;
timeLabel.Layout.Column = 3;
timeControl = uislider(gridLayout,'Limits',[0.25 3], ...
    'Value',1,'MajorTicks',[0.25 0.5 1 2 3]);
timeControl.Layout.Row = 2;
timeControl.Layout.Column = 4;

resetButton = uibutton(gridLayout,'Text','Reset baseline', ...
    'ButtonPushedFcn',@resetBaseline);
resetButton.Layout.Row = 2;
resetButton.Layout.Column = 5;
summary = uilabel(gridLayout,'WordWrap','on');
summary.Layout.Row = 2;
summary.Layout.Column = 6;

gainControl.ValueChangingFcn = @previewGain;
gainControl.ValueChangedFcn = @(~,~) updatePlots([],[]);
timeControl.ValueChangingFcn = @previewTimeConstant;
timeControl.ValueChangedFcn = @(~,~) updatePlots([],[]);
updatePlots([],[]);

    function previewGain(~,event)
        updatePlots(event.Value,[]);
    end

    function previewTimeConstant(~,event)
        updatePlots([],event.Value);
    end

    function resetBaseline(~,~)
        gainControl.Value = 2;
        timeControl.Value = 1;
        updatePlots([],[]);
    end

    function updatePlots(gainPreview,timePreview)
        if isempty(gainPreview)
            proportionalGain = gainControl.Value;
        else
            proportionalGain = gainPreview;
        end
        if isempty(timePreview)
            plantTimeConstantSec = timeControl.Value;
        else
            plantTimeConstantSec = timePreview;
        end
        viewDt = min(0.01,0.09*plantTimeConstantSec/(1+proportionalGain));
        result = modelFunction( ...
            proportionalGain,plantTimeConstantSec,1,1,0,-1,5,viewDt);

        cla(axOutput);
        plot(axOutput,result.t,ones(size(result.t)),'k:','LineWidth',1.2, ...
            'DisplayName','Reference r');
        hold(axOutput,'on');
        plot(axOutput,result.t,result.outputM,'LineWidth',1.5, ...
            'DisplayName','Measured output y');
        hold(axOutput,'off'); grid(axOutput,'on');
        xlabel(axOutput,'Time (s)');
        ylabel(axOutput,'Output position y (m)');
        title(axOutput,'Negative-feedback tracking');
        legend(axOutput,'Location','southeast');

        cla(axCommand);
        plot(axCommand,result.t,result.controlCommand,'LineWidth',1.5);
        grid(axCommand,'on');
        xlabel(axCommand,'Time (s)');
        ylabel(axCommand,'Control command u (command units)');
        title(axCommand,'Effort created by error');

        summary.Text = sprintf(['Kp = %.2f command/m\ntau = %.2f s\n' ...
            'tau_cl = %.3f s\ne_ss = %.3f m\nu(0) = %.2f'], ...
            proportionalGain,plantTimeConstantSec, ...
            result.closedLoopTimeConstantSec, ...
            result.predictedSteadyStateErrorM,result.initialControlCommand);
    end
end
