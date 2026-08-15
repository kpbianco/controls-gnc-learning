function interactive
%INTERACTIVE Move sensor sensitivity, observation time, and measurement path.
modelFunction = @model;
fig = uifigure('Name','P14 Test Observability', ...
    'Position',[80 80 1320 780]);
gridLayout = uigridlayout(fig,[2 9]);
gridLayout.RowHeight = {'1x',150};

axStates = uiaxes(gridLayout);
axStates.Layout.Row = 1;
axStates.Layout.Column = [1 4];
axOutput = uiaxes(gridLayout);
axOutput.Layout.Row = 1;
axOutput.Layout.Column = [5 9];

gainLabel = uilabel(gridLayout, ...
    'Text','Sensor sensitivity (normalized output/state)','WordWrap','on');
gainLabel.Layout.Row = 2;
gainLabel.Layout.Column = 1;
gainControl = uislider(gridLayout,'Limits',[0.25 2],'Value',1, ...
    'MajorTicks',[0.25 0.5 1 1.5 2]);
gainControl.Layout.Row = 2;
gainControl.Layout.Column = [2 3];

windowLabel = uilabel(gridLayout, ...
    'Text','Observation window (s)','WordWrap','on');
windowLabel.Layout.Row = 2;
windowLabel.Layout.Column = 4;
windowControl = uispinner(gridLayout,'Limits',[0.1 5], ...
    'Step',0.1,'Value',2);
windowControl.Layout.Row = 2;
windowControl.Layout.Column = 5;

sensorControl = uidropdown(gridLayout, ...
    'Items',{'Position measurement','Rate-only measurement (broken)'}, ...
    'Value','Position measurement');
sensorControl.Layout.Row = 2;
sensorControl.Layout.Column = 6;
resetButton = uibutton(gridLayout,'Text','Reset baseline');
resetButton.Layout.Row = 2;
resetButton.Layout.Column = 7;
summary = uilabel(gridLayout,'WordWrap','on');
summary.Layout.Row = 2;
summary.Layout.Column = [8 9];

gainControl.ValueChangingFcn = @(~,event) ...
    redraw(event.Value,windowControl.Value,sensorControl.Value);
gainControl.ValueChangedFcn = @(~,~) ...
    redraw(gainControl.Value,windowControl.Value,sensorControl.Value);
windowControl.ValueChangedFcn = @(~,~) ...
    redraw(gainControl.Value,windowControl.Value,sensorControl.Value);
sensorControl.ValueChangedFcn = @(~,~) ...
    redraw(gainControl.Value,windowControl.Value,sensorControl.Value);
resetButton.ButtonPushedFcn = @(~,~) resetBaseline();
redraw(gainControl.Value,windowControl.Value,sensorControl.Value);

    function resetBaseline
        gainControl.Value = 1;
        windowControl.Value = 2;
        sensorControl.Value = 'Position measurement';
        redraw(1,2,'Position measurement');
    end

    function redraw(sensorGain,observationWindowSec,sensorMode)
        observationWindowSec = round(observationWindowSec/0.05)*0.05;
        windowControl.Value = observationWindowSec;
        measurePosition = strcmp(sensorMode,'Position measurement');
        result = modelFunction(sensorGain,observationWindowSec,0.05, ...
            measurePosition);

        cla(axStates);
        plot(axStates,result.timeSec,result.stateTrajectory(1,:), ...
            'LineWidth',1.8,'DisplayName','True position / 1 m');
        hold(axStates,'on');
        plot(axStates,result.timeSec, ...
            result.alternativeStateTrajectory(1,:),'--', ...
            'LineWidth',1.6,'DisplayName','Offset position / 1 m');
        plot(axStates,result.timeSec,result.stateTrajectory(2,:),':', ...
            'LineWidth',1.8,'DisplayName','Shared rate / 1 m/s');
        hold(axStates,'off'); grid(axStates,'on');
        xlabel(axStates,'Time (s)');
        ylabel(axStates,'Normalized state');
        title(axStates,'Two candidate initial states');
        legend(axStates,'Location','best');

        cla(axOutput);
        plot(axOutput,result.timeSec,result.measurementHistory, ...
            'LineWidth',1.8,'DisplayName','True-state output');
        hold(axOutput,'on');
        plot(axOutput,result.timeSec, ...
            result.alternativeMeasurementHistory,'--', ...
            'LineWidth',1.6,'DisplayName','Offset-state output');
        hold(axOutput,'off'); grid(axOutput,'on');
        xlabel(axOutput,'Time (s)');
        ylabel(axOutput,'Sensor output (sensor unit)');
        title(axOutput,'Can the output histories distinguish the states?');
        legend(axOutput,'Location','best');

        if ~result.initialStateUnique
            uniquenessText = 'initial position not unique';
            inverseText = 'inverse noise gain N/A';
        elseif result.worstCaseStateErrorGain > 10
            uniquenessText = 'full rank, weakly separated';
            inverseText = sprintf('inverse noise gain %.3g', ...
                result.worstCaseStateErrorGain);
        else
            uniquenessText = 'full rank, states separated';
            inverseText = sprintf('inverse noise gain %.3g', ...
                result.worstCaseStateErrorGain);
        end
        summary.Text = sprintf([ ...
            'rank %d/2 | scaled sigma_min %.3g | separation %.3g sensor unit | %s | %s'], ...
            result.observabilityRank,result.minimumSingularValue, ...
            result.outputDifferenceRmsSensorUnits,inverseText,uniquenessText);
    end
end
