function interactive
%INTERACTIVE Explore P18 feedforward, feedback, and mixer polarity.
modelFunction = @model;
window = uifigure('Name','P18 feedforward plus feedback', ...
    'Position',[80 80 1240 700]);
gridLayout = uigridlayout(window,[2 12]);
gridLayout.RowHeight = {'1x',115};
gridLayout.ColumnWidth = repmat({'1x'},1,12);

axTracking = uiaxes(gridLayout);
axTracking.Layout.Row = 1;
axTracking.Layout.Column = [1 6];
axCommands = uiaxes(gridLayout);
axCommands.Layout.Row = 1;
axCommands.Layout.Column = [7 12];

feedforwardLabel = uilabel(gridLayout, ...
    'Text','Feedforward scale alpha','WordWrap','on');
feedforwardLabel.Layout.Row = 2;
feedforwardLabel.Layout.Column = 1;
feedforwardControl = uislider(gridLayout,'Limits',[0 1.5], ...
    'Value',1,'MajorTicks',[0 0.5 1 1.5]);
feedforwardControl.Layout.Row = 2;
feedforwardControl.Layout.Column = [2 3];

feedbackLabel = uilabel(gridLayout, ...
    'Text','Feedback scale beta','WordWrap','on');
feedbackLabel.Layout.Row = 2;
feedbackLabel.Layout.Column = 4;
feedbackControl = uislider(gridLayout,'Limits',[0 2], ...
    'Value',1,'MajorTicks',[0 0.5 1 1.5 2]);
feedbackControl.Layout.Row = 2;
feedbackControl.Layout.Column = [5 6];

disturbanceLabel = uilabel(gridLayout, ...
    'Text','Disturbance magnitude (m/s^2)','WordWrap','on');
disturbanceLabel.Layout.Row = 2;
disturbanceLabel.Layout.Column = 7;
disturbanceControl = uispinner(gridLayout,'Limits',[0 0.8], ...
    'Step',0.05,'Value',0.4,'ValueDisplayFormat','%.2f');
disturbanceControl.Layout.Row = 2;
disturbanceControl.Layout.Column = 8;

signControl = uidropdown(gridLayout, ...
    'Items',{'Correct feedforward sign','Reversed feedforward sign (broken)'}, ...
    'Value','Correct feedforward sign');
signControl.Layout.Row = 2;
signControl.Layout.Column = [9 10];
resetButton = uibutton(gridLayout,'Text','Reset baseline');
resetButton.Layout.Row = 2;
resetButton.Layout.Column = 11;
summary = uilabel(gridLayout,'WordWrap','on');
summary.Layout.Row = 2;
summary.Layout.Column = 12;

feedforwardControl.ValueChangingFcn = @(~,event) ...
    redraw(event.Value,feedbackControl.Value,disturbanceControl.Value, ...
    signControl.Value);
feedforwardControl.ValueChangedFcn = @(~,~) ...
    redraw(feedforwardControl.Value,feedbackControl.Value, ...
    disturbanceControl.Value,signControl.Value);
feedbackControl.ValueChangingFcn = @(~,event) ...
    redraw(feedforwardControl.Value,event.Value,disturbanceControl.Value, ...
    signControl.Value);
feedbackControl.ValueChangedFcn = @(~,~) ...
    redraw(feedforwardControl.Value,feedbackControl.Value, ...
    disturbanceControl.Value,signControl.Value);
disturbanceControl.ValueChangedFcn = @(~,~) ...
    redraw(feedforwardControl.Value,feedbackControl.Value, ...
    disturbanceControl.Value,signControl.Value);
signControl.ValueChangedFcn = @(~,~) ...
    redraw(feedforwardControl.Value,feedbackControl.Value, ...
    disturbanceControl.Value,signControl.Value);
resetButton.ButtonPushedFcn = @(~,~) resetBaseline();
redraw(1,1,0.4,'Correct feedforward sign');

    function resetBaseline
        feedforwardControl.Value = 1;
        feedbackControl.Value = 1;
        disturbanceControl.Value = 0.4;
        signControl.Value = 'Correct feedforward sign';
        redraw(1,1,0.4,'Correct feedforward sign');
    end

    function redraw(feedforwardScale,feedbackScale,disturbanceMagnitude, ...
            signChoice)
        feedforwardScale = round(feedforwardScale*20)/20;
        feedbackScale = round(feedbackScale*20)/20;
        disturbanceMagnitude = round(disturbanceMagnitude*20)/20;
        feedforwardControl.Value = feedforwardScale;
        feedbackControl.Value = feedbackScale;
        disturbanceControl.Value = disturbanceMagnitude;
        if strcmp(signChoice,'Correct feedforward sign')
            feedforwardSign = 1;
        else
            feedforwardSign = -1;
        end
        result = modelFunction(feedforwardScale,feedbackScale, ...
            feedforwardSign,0.6,disturbanceMagnitude,12,0.02);

        cla(axTracking);
        plot(axTracking,result.timeSec,result.referencePositionM,'k--', ...
            'LineWidth',1.4,'DisplayName','Reference position');
        hold(axTracking,'on');
        plot(axTracking,result.timeSec,result.actualPositionM,'b-', ...
            'LineWidth',1.8,'DisplayName','Actual position');
        plot(axTracking,result.timeSec,result.positionErrorM,'m:', ...
            'LineWidth',1.5,'DisplayName','Position error');
        hold(axTracking,'off'); grid(axTracking,'on');
        xlabel(axTracking,'Time (s)'); ylabel(axTracking,'Position (m)');
        title(axTracking,'Reference, actual position, and tracking error');
        legend(axTracking,'Location','best');

        cla(axCommands);
        plot(axCommands,result.timeSec,result.feedforwardCommandMPerSec2, ...
            'b-','LineWidth',1.5,'DisplayName','Feedforward');
        hold(axCommands,'on');
        plot(axCommands,result.timeSec,result.feedbackCommandMPerSec2, ...
            'm-','LineWidth',1.5,'DisplayName','Feedback');
        plot(axCommands,result.timeSec,result.totalCommandMPerSec2, ...
            'k--','LineWidth',1.7,'DisplayName','Total command');
        plot(axCommands,result.timeSec, ...
            result.disturbanceAccelerationMPerSec2,'r:', ...
            'LineWidth',1.4,'DisplayName','Disturbance');
        hold(axCommands,'off'); grid(axCommands,'on');
        xlabel(axCommands,'Time (s)');
        ylabel(axCommands,'Plant-input acceleration (m/s^2)');
        title(axCommands,'Command mixer and external disturbance');
        legend(axCommands,'Location','best');

        if feedforwardSign < 0
            stateText = 'broken: feedforward polarity is reversed';
        elseif feedbackScale == 0 && disturbanceMagnitude > 0
            stateText = 'limit: feedforward cannot remove disturbance error';
        elseif feedforwardScale == 1 && disturbanceMagnitude == 0
            stateText = 'matched plan: feedback correction is zero';
        else
            stateText = 'combined anticipatory and reactive control';
        end
        summary.Text = sprintf([ ...
            'RMSE %.3f m | peak error %.3f m | recovery %.2f s | ' ...
            'feedback effort %.3f m^2/s^3 | %s'], ...
            result.positionRmseM,result.maximumAbsolutePositionErrorM, ...
            result.recoveryTimeSec,result.feedbackEffortIntegralM2PerSec3, ...
            stateText);
    end
end
