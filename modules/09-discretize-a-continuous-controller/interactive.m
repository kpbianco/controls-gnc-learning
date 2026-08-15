function interactive
%INTERACTIVE Move sample period and discretization rule independently.
% Retain the P09 model even after launch_lesson removes this folder from the
% MATLAB path or another lesson clears the global name-resolution cache.
modelFunction = @model;
fig = uifigure('Name','P09 Discretize a Continuous Controller', ...
    'Position',[80 80 1280 760]);
gridLayout = uigridlayout(fig,[2 6]);
gridLayout.RowHeight = {'1x',130};

axOutput = uiaxes(gridLayout);
axOutput.Layout.Row = 1;
axOutput.Layout.Column = [1 3];
axControl = uiaxes(gridLayout);
axControl.Layout.Row = 1;
axControl.Layout.Column = [4 6];

periodLabel = uilabel(gridLayout,'Text','Sample period Ts (s)', ...
    'WordWrap','on');
periodLabel.Layout.Row = 2;
periodLabel.Layout.Column = 1;
periodControl = uislider(gridLayout,'Limits',[0.02 0.6],'Value',0.05, ...
    'MajorTicks',[0.02 0.05 0.1 0.2 0.4 0.6]);
periodControl.Layout.Row = 2;
periodControl.Layout.Column = 2;

methodLabel = uilabel(gridLayout,'Text','Integral discretization rule', ...
    'WordWrap','on');
methodLabel.Layout.Row = 2;
methodLabel.Layout.Column = 3;
methodControl = uidropdown(gridLayout, ...
    'Items',{'backward-euler','forward-euler'}, ...
    'Value','backward-euler');
methodControl.Layout.Row = 2;
methodControl.Layout.Column = 4;

resetButton = uibutton(gridLayout,'Text','Reset baseline');
resetButton.Layout.Row = 2;
resetButton.Layout.Column = 5;
summary = uilabel(gridLayout,'WordWrap','on');
summary.Layout.Row = 2;
summary.Layout.Column = 6;

periodControl.ValueChangingFcn = @(~,event) ...
    redraw(event.Value,methodControl.Value);
periodControl.ValueChangedFcn = @(~,~) ...
    redraw(periodControl.Value,methodControl.Value);
methodControl.ValueChangedFcn = @(~,~) ...
    redraw(periodControl.Value,methodControl.Value);
resetButton.ButtonPushedFcn = @(~,~) resetBaseline();
redraw(periodControl.Value,methodControl.Value);

    function resetBaseline
        periodControl.Value = 0.05;
        methodControl.Value = 'backward-euler';
        redraw(0.05,'backward-euler');
    end

    function redraw(samplePeriodSec,discretizationMethod)
        result = modelFunction(samplePeriodSec,discretizationMethod,12,0.01);

        cla(axOutput);
        plot(axOutput,result.t,result.continuousOutput,'k--', ...
            'LineWidth',1.3,'DisplayName','Continuous PI target');
        hold(axOutput,'on');
        plot(axOutput,result.t,result.digitalOutput,'LineWidth',1.7, ...
            'DisplayName','Digital PI output');
        plot(axOutput,result.sampleTimes,result.digitalOutputSamples,'o', ...
            'MarkerSize',3,'DisplayName','Controller samples');
        hold(axOutput,'off'); grid(axOutput,'on');
        xlabel(axOutput,'Time (s)');
        ylabel(axOutput,'Plant output y (output)');
        title(axOutput,'Output: continuous target versus sampled controller');
        legend(axOutput,'Location','best');

        cla(axControl);
        plot(axControl,result.t,result.continuousControl,'k--', ...
            'LineWidth',1.3,'DisplayName','Continuous PI command');
        hold(axControl,'on');
        stairs(axControl,result.t,result.heldControl, ...
            'LineWidth',1.6,'DisplayName','Held digital command');
        hold(axControl,'off'); grid(axControl,'on');
        xlabel(axControl,'Time (s)');
        ylabel(axControl,'Control effort u (output)');
        title(axControl,'Zero-order hold makes update timing visible');
        legend(axControl,'Location','best');

        if result.isStable
            stabilityText = 'inside unit circle';
        else
            stabilityText = 'not strictly inside unit circle';
        end
        summary.Text = sprintf([ ...
            '%s | Ts %.3f s | %.1f samples/period | gap %.3f output | ' ...
            '|p|max %.3f (%s)'],discretizationMethod,samplePeriodSec, ...
            result.samplesPerNaturalPeriod,result.maximumAbsTrackingGap, ...
            result.spectralRadius,stabilityText);
    end
end
