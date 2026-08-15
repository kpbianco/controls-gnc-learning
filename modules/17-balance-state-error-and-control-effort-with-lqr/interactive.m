function interactive
%INTERACTIVE Explore P17 LQR weights and the actuator-assumption failure.
modelFunction = @model;
window = uifigure('Name','P17 LQR error-effort tradeoff', ...
    'Position',[100 100 1180 680]);
gridLayout = uigridlayout(window,[2 10]);
gridLayout.RowHeight = {'1x',105};
gridLayout.ColumnWidth = {'1x','1x','1x','1x','1x', ...
    '1x','1x','1x','1x','1x'};

axState = uiaxes(gridLayout);
axState.Layout.Row = 1;
axState.Layout.Column = [1 5];
axEffort = uiaxes(gridLayout);
axEffort.Layout.Row = 1;
axEffort.Layout.Column = [6 10];

positionWeightLabel = uilabel(gridLayout, ...
    'Text','Position-error weight q_p','WordWrap','on');
positionWeightLabel.Layout.Row = 2;
positionWeightLabel.Layout.Column = 1;
positionWeightControl = uislider(gridLayout,'Limits',[0 16], ...
    'Value',4,'MajorTicks',[0 1 4 8 16]);
positionWeightControl.Layout.Row = 2;
positionWeightControl.Layout.Column = [2 3];

effortWeightLabel = uilabel(gridLayout, ...
    'Text','Control-effort weight r','WordWrap','on');
effortWeightLabel.Layout.Row = 2;
effortWeightLabel.Layout.Column = 4;
effortWeightControl = uispinner(gridLayout,'Limits',[0.05 20], ...
    'Step',0.05,'Value',1,'ValueDisplayFormat','%.2f');
effortWeightControl.Layout.Row = 2;
effortWeightControl.Layout.Column = 5;

actuatorControl = uidropdown(gridLayout, ...
    'Items',{'Full actuator authority','Disconnected actuator (broken)'}, ...
    'Value','Full actuator authority');
actuatorControl.Layout.Row = 2;
actuatorControl.Layout.Column = [6 7];
resetButton = uibutton(gridLayout,'Text','Reset baseline');
resetButton.Layout.Row = 2;
resetButton.Layout.Column = 8;
summary = uilabel(gridLayout,'WordWrap','on');
summary.Layout.Row = 2;
summary.Layout.Column = [9 10];

positionWeightControl.ValueChangingFcn = @(~,event) ...
    redraw(event.Value,effortWeightControl.Value,actuatorControl.Value);
positionWeightControl.ValueChangedFcn = @(~,~) ...
    redraw(positionWeightControl.Value,effortWeightControl.Value, ...
    actuatorControl.Value);
effortWeightControl.ValueChangedFcn = @(~,~) ...
    redraw(positionWeightControl.Value,effortWeightControl.Value, ...
    actuatorControl.Value);
actuatorControl.ValueChangedFcn = @(~,~) ...
    redraw(positionWeightControl.Value,effortWeightControl.Value, ...
    actuatorControl.Value);
resetButton.ButtonPushedFcn = @(~,~) resetBaseline();
redraw(4,1,'Full actuator authority');

    function resetBaseline
        positionWeightControl.Value = 4;
        effortWeightControl.Value = 1;
        actuatorControl.Value = 'Full actuator authority';
        redraw(4,1,'Full actuator authority');
    end

    function redraw(positionWeight,effortWeight,actuatorChoice)
        positionWeight = round(positionWeight*4)/4;
        effortWeight = round(effortWeight*20)/20;
        positionWeightControl.Value = positionWeight;
        effortWeightControl.Value = effortWeight;
        if strcmp(actuatorChoice,'Full actuator authority')
            effectiveness = 1;
        else
            effectiveness = 0;
        end
        result = modelFunction(positionWeight,effortWeight, ...
            effectiveness,1,12,0.02);

        cla(axState);
        plot(axState,result.timeSec,result.positionErrorM,'b-', ...
            'LineWidth',1.8,'DisplayName','Position error (m)');
        hold(axState,'on');
        plot(axState,result.timeSec,result.rateErrorMPerSec, ...
            'Color',[0.1 0.55 0.3],'LineWidth',1.6, ...
            'DisplayName','Rate error (m/s)');
        hold(axState,'off'); grid(axState,'on');
        xlabel(axState,'Time (s)');
        ylabel(axState,'State error (shown in labeled units)');
        title(axState,'State error response');
        legend(axState,'Location','best');

        cla(axEffort);
        plot(axEffort,result.timeSec, ...
            result.commandedAccelerationMPerSec2,'r-', ...
            'LineWidth',1.8,'DisplayName','Commanded');
        hold(axEffort,'on');
        plot(axEffort,result.timeSec,result.appliedAccelerationMPerSec2, ...
            'k--','LineWidth',1.4,'DisplayName','Applied');
        hold(axEffort,'off'); grid(axEffort,'on');
        xlabel(axEffort,'Time (s)');
        ylabel(axEffort,'Acceleration (m/s^2)');
        title(axEffort,'Commanded versus applied effort');
        legend(axEffort,'Location','best');

        if effectiveness == 0
            stateText = 'broken: requested effort has no authority';
        elseif positionWeight == 0
            stateText = 'limit: unpriced position offset persists';
        elseif effortWeight > 4
            stateText = 'expensive control gives a gentler response';
        else
            stateText = 'nominal error-effort tradeoff';
        end
        summary.Text = sprintf([ ...
            'Kp %.2f 1/s^2, Kv %.2f 1/s | settle %.2f s | peak %.2f m/s^2 | ' ...
            'position ISE %.2f m^2 s | effort integral %.2f m^2/s^3 | %s'], ...
            result.feedbackGain(1),result.feedbackGain(2), ...
            result.settlingTimeSec, ...
            result.peakCommandedAccelerationMPerSec2, ...
            result.positionIntegralSquaredM2Sec, ...
            result.commandedEffortIntegralM2PerSec3,stateText);
    end
end
