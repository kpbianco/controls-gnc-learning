function interactive
%INTERACTIVE Move reference and actuator limit while preserving the P11 model.
modelFunction = @model;
fig = uifigure('Name','P11 Drive an Actuator into Saturation', ...
    'Position',[80 80 1280 760]);
gridLayout = uigridlayout(fig,[2 7]);
gridLayout.RowHeight = {'1x',135};

axOutput = uiaxes(gridLayout);
axOutput.Layout.Row = 1;
axOutput.Layout.Column = [1 3];
axControl = uiaxes(gridLayout);
axControl.Layout.Row = 1;
axControl.Layout.Column = [4 7];

referenceLabel = uilabel(gridLayout,'Text','Reference r (output)', ...
    'WordWrap','on');
referenceLabel.Layout.Row = 2;
referenceLabel.Layout.Column = 1;
referenceControl = uislider(gridLayout,'Limits',[-2 2],'Value',1, ...
    'MajorTicks',[-2 -1 0 1 2]);
referenceControl.Layout.Row = 2;
referenceControl.Layout.Column = 2;

limitLabel = uilabel(gridLayout,'Text','Actuator limit uLimit (actuator)', ...
    'WordWrap','on');
limitLabel.Layout.Row = 2;
limitLabel.Layout.Column = 3;
limitControl = uislider(gridLayout,'Limits',[0.25 3],'Value',2, ...
    'MajorTicks',[0.25 0.5 1 2 3]);
limitControl.Layout.Row = 2;
limitControl.Layout.Column = 4;

resetButton = uibutton(gridLayout,'Text','Reset baseline');
resetButton.Layout.Row = 2;
resetButton.Layout.Column = 5;
summary = uilabel(gridLayout,'WordWrap','on');
summary.Layout.Row = 2;
summary.Layout.Column = [6 7];

referenceControl.ValueChangingFcn = @(~,event) ...
    redraw(event.Value,limitControl.Value);
referenceControl.ValueChangedFcn = @(~,~) ...
    redraw(referenceControl.Value,limitControl.Value);
limitControl.ValueChangingFcn = @(~,event) ...
    redraw(referenceControl.Value,event.Value);
limitControl.ValueChangedFcn = @(~,~) ...
    redraw(referenceControl.Value,limitControl.Value);
resetButton.ButtonPushedFcn = @(~,~) resetBaseline();
redraw(referenceControl.Value,limitControl.Value);

    function resetBaseline
        referenceControl.Value = 1;
        limitControl.Value = 2;
        redraw(1,2);
    end

    function redraw(reference,controlLimit)
        result = modelFunction(reference,controlLimit,5,0.01);

        cla(axOutput);
        plot(axOutput,result.t,result.reference,'k:', ...
            'LineWidth',1.2,'DisplayName','Reference');
        hold(axOutput,'on');
        plot(axOutput,result.t,result.unlimitedOutput,'--', ...
            'LineWidth',1.3,'DisplayName','Unlimited actuator');
        plot(axOutput,result.t,result.plantOutput,'LineWidth',1.8, ...
            'DisplayName','Limited actuator');
        hold(axOutput,'off'); grid(axOutput,'on');
        xlabel(axOutput,'Time (s)');
        ylabel(axOutput,'Plant output y (output)');
        title(axOutput,'Saturation changes the trajectory, not the requested target');
        legend(axOutput,'Location','best');

        cla(axControl);
        stairs(axControl,result.t,result.requestedControl,'--', ...
            'LineWidth',1.3,'DisplayName','Requested control');
        hold(axControl,'on');
        stairs(axControl,result.t,result.appliedControl,'LineWidth',1.8, ...
            'DisplayName','Applied control');
        plot(axControl,result.t,result.controlUpperLimit,'r:', ...
            'DisplayName','Positive actuator limit');
        plot(axControl,result.t,result.controlLowerLimit,'r:', ...
            'HandleVisibility','off');
        hold(axControl,'off'); grid(axControl,'on');
        xlabel(axControl,'Time (s)');
        ylabel(axControl,'Control command u (actuator)');
        title(axControl,'The actuator clips amplitude at its physical limit');
        legend(axControl,'Location','best');

        if result.persistentSaturation
            saturationText = 'persistent saturation';
        elseif result.saturatedThroughHorizon
            saturationText = 'still clipped at 5 s; eventual release';
        elseif result.saturationFraction > 0
            saturationText = sprintf('released at %.2f s', ...
                result.releaseTimeSec);
        else
            saturationText = 'not saturated';
        end
        summary.Text = sprintf([ ...
            'r %.2f output | limit %.2f actuator | clipped %.1f%% | ' ...
            'max request %.2f actuator | final error %.3f output | %s'], ...
            result.referenceValue,result.controlLimit, ...
            100*result.saturationFraction, ...
            result.maximumAbsRequestedControl,result.finalTrackingError, ...
            saturationText);
    end
end
