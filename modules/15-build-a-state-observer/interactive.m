function interactive
%INTERACTIVE Explore observer speed, interference, and sensor calibration.
modelFunction = @model;
fig = uifigure('Name','P15 Build a State Observer', ...
    'Position',[80 80 1320 780]);
gridLayout = uigridlayout(fig,[2 10]);
gridLayout.RowHeight = {'1x',160};

axPosition = uiaxes(gridLayout);
axPosition.Layout.Row = 1;
axPosition.Layout.Column = [1 5];
axError = uiaxes(gridLayout);
axError.Layout.Row = 1;
axError.Layout.Column = [6 10];

speedLabel = uilabel(gridLayout, ...
    'Text','Observer pole speed (1/s)','WordWrap','on');
speedLabel.Layout.Row = 2;
speedLabel.Layout.Column = 1;
speedControl = uislider(gridLayout,'Limits',[1 5],'Value',2, ...
    'MajorTicks',[1 2 3 4 5]);
speedControl.Layout.Row = 2;
speedControl.Layout.Column = [2 3];

interferenceLabel = uilabel(gridLayout, ...
    'Text','Measurement interference amplitude (m)','WordWrap','on');
interferenceLabel.Layout.Row = 2;
interferenceLabel.Layout.Column = 4;
interferenceControl = uispinner(gridLayout,'Limits',[0 0.05], ...
    'Step',0.005,'Value',0,'ValueDisplayFormat','%.3f');
interferenceControl.Layout.Row = 2;
interferenceControl.Layout.Column = 5;

calibrationControl = uidropdown(gridLayout, ...
    'Items',{'Calibrated sensor','+0.15 m bias (broken)'}, ...
    'Value','Calibrated sensor');
calibrationControl.Layout.Row = 2;
calibrationControl.Layout.Column = [6 7];
resetButton = uibutton(gridLayout,'Text','Reset baseline');
resetButton.Layout.Row = 2;
resetButton.Layout.Column = 8;
summary = uilabel(gridLayout,'WordWrap','on');
summary.Layout.Row = 2;
summary.Layout.Column = [9 10];

speedControl.ValueChangingFcn = @(~,event) ...
    redraw(event.Value,interferenceControl.Value,calibrationControl.Value);
speedControl.ValueChangedFcn = @(~,~) ...
    redraw(speedControl.Value,interferenceControl.Value,calibrationControl.Value);
interferenceControl.ValueChangedFcn = @(~,~) ...
    redraw(speedControl.Value,interferenceControl.Value,calibrationControl.Value);
calibrationControl.ValueChangedFcn = @(~,~) ...
    redraw(speedControl.Value,interferenceControl.Value,calibrationControl.Value);
resetButton.ButtonPushedFcn = @(~,~) resetBaseline();
redraw(2,0,'Calibrated sensor');

    function resetBaseline
        speedControl.Value = 2;
        interferenceControl.Value = 0;
        calibrationControl.Value = 'Calibrated sensor';
        redraw(2,0,'Calibrated sensor');
    end

    function redraw(observerPoleSpeedPerSec,interferenceAmplitudeM,calibration)
        observerPoleSpeedPerSec = round(observerPoleSpeedPerSec*10)/10;
        speedControl.Value = observerPoleSpeedPerSec;
        interferenceAmplitudeM = ...
            round(interferenceAmplitudeM/0.005)*0.005;
        interferenceControl.Value = interferenceAmplitudeM;
        if strcmp(calibration,'Calibrated sensor')
            sensorBiasM = 0;
        else
            sensorBiasM = 0.15;
        end
        result = modelFunction(observerPoleSpeedPerSec, ...
            interferenceAmplitudeM,sensorBiasM,0.4,8,0.02);

        cla(axPosition);
        plot(axPosition,result.timeSec,result.trueState(1,:), ...
            'LineWidth',1.8,'DisplayName','True position');
        hold(axPosition,'on');
        plot(axPosition,result.timeSec,result.estimatedState(1,:),'--', ...
            'LineWidth',1.6,'DisplayName','Estimated position');
        hold(axPosition,'off'); grid(axPosition,'on');
        xlabel(axPosition,'Time (s)');
        ylabel(axPosition,'Position (m)');
        title(axPosition,'Measured position and observer estimate');
        legend(axPosition,'Location','best');

        cla(axError);
        plot(axError,result.timeSec,result.estimationError(1,:), ...
            'LineWidth',1.8,'DisplayName','Position error (m)');
        hold(axError,'on');
        plot(axError,result.timeSec,result.estimationError(2,:),'--', ...
            'LineWidth',1.6,'DisplayName','Rate error (m/s)');
        plot(axError,result.timeSec,result.innovationM,':', ...
            'LineWidth',1.4,'DisplayName','Innovation (m)');
        hold(axError,'off'); grid(axError,'on');
        xlabel(axError,'Time (s)');
        ylabel(axError,'Error in stated units');
        title(axError,'Correction evidence and hidden bias symptom');
        legend(axError,'Location','best');

        if sensorBiasM ~= 0 && ...
                abs(result.innovationM(end)) < 0.01 && ...
                abs(result.estimationError(1,end)) > 0.1
            stateText = 'quiet innovation, biased position';
        elseif interferenceAmplitudeM > 0
            stateText = 'measurement ripple enters both estimates';
        else
            stateText = 'matched observer converging';
        end
        summary.Text = sprintf([ ...
            'q %.4f | gain norm %.3g | tail RMS %.3g m, %.3g m/s | ' ...
            'final innovation %.3g m | %s'], ...
            result.desiredErrorPole,norm(result.normalizedObserverGain), ...
            result.positionErrorRmsTailM,result.rateErrorRmsTailMPerSec, ...
            result.innovationM(end),stateText);
    end
end
