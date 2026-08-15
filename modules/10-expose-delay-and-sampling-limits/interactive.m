function interactive
%INTERACTIVE Move sample period and computation-delay fraction safely.
% Retain the P10 model even after launch_lesson removes this folder from the
% MATLAB path or another lesson clears the global name-resolution cache.
modelFunction = @model;
fig = uifigure('Name','P10 Expose Delay and Sampling Limits', ...
    'Position',[80 80 1280 760]);
gridLayout = uigridlayout(fig,[2 7]);
gridLayout.RowHeight = {'1x',130};

axOutput = uiaxes(gridLayout);
axOutput.Layout.Row = 1;
axOutput.Layout.Column = [1 3];
axCommand = uiaxes(gridLayout);
axCommand.Layout.Row = 1;
axCommand.Layout.Column = [4 7];

periodLabel = uilabel(gridLayout,'Text','Sample period Ts (s)', ...
    'WordWrap','on');
periodLabel.Layout.Row = 2;
periodLabel.Layout.Column = 1;
periodControl = uislider(gridLayout,'Limits',[0.02 0.2],'Value',0.05, ...
    'MajorTicks',[0.02 0.05 0.1 0.15 0.2]);
periodControl.Layout.Row = 2;
periodControl.Layout.Column = 2;

delayLabel = uilabel(gridLayout, ...
    'Text','Computation delay Td / Ts (fraction)', ...
    'WordWrap','on');
delayLabel.Layout.Row = 2;
delayLabel.Layout.Column = 3;
delayControl = uislider(gridLayout,'Limits',[0 0.95],'Value',0.2, ...
    'MajorTicks',[0 0.2 0.4 0.6 0.8 0.95]);
delayControl.Layout.Row = 2;
delayControl.Layout.Column = 4;

resetButton = uibutton(gridLayout,'Text','Reset baseline');
resetButton.Layout.Row = 2;
resetButton.Layout.Column = 5;
summary = uilabel(gridLayout,'WordWrap','on');
summary.Layout.Row = 2;
summary.Layout.Column = [6 7];

periodControl.ValueChangingFcn = @(~,event) ...
    redraw(event.Value,delayControl.Value);
periodControl.ValueChangedFcn = @(~,~) ...
    redraw(periodControl.Value,delayControl.Value);
delayControl.ValueChangingFcn = @(~,event) ...
    redraw(periodControl.Value,event.Value);
delayControl.ValueChangedFcn = @(~,~) ...
    redraw(periodControl.Value,delayControl.Value);
resetButton.ButtonPushedFcn = @(~,~) resetBaseline();
redraw(periodControl.Value,delayControl.Value);

    function resetBaseline
        periodControl.Value = 0.05;
        delayControl.Value = 0.2;
        redraw(0.05,0.2);
    end

    function redraw(samplePeriodSec,delayFraction)
        computationDelaySec = samplePeriodSec*delayFraction;
        result = modelFunction(samplePeriodSec,computationDelaySec,4,0.005);

        cla(axOutput);
        plot(axOutput,result.t,result.continuousOutput,'k--', ...
            'LineWidth',1.3,'DisplayName','Immediate continuous P target');
        hold(axOutput,'on');
        plot(axOutput,result.t,result.sampledOutput,'LineWidth',1.7, ...
            'DisplayName','Sampled and delayed output');
        plot(axOutput,result.sampleTimes,result.outputSamples,'o', ...
            'MarkerSize',3,'DisplayName','Controller samples');
        hold(axOutput,'off'); grid(axOutput,'on');
        xlabel(axOutput,'Time (s)');
        ylabel(axOutput,'Plant output y (output)');
        title(axOutput,'Output: continuous target versus timed feedback');
        legend(axOutput,'Location','best');

        cla(axCommand);
        stairs(axCommand,result.t,result.computedCommand,'--', ...
            'LineWidth',1.3,'DisplayName','Newly computed command');
        hold(axCommand,'on');
        stairs(axCommand,result.t,result.appliedCommand, ...
            'LineWidth',1.7,'DisplayName','Actually applied command');
        hold(axCommand,'off'); grid(axCommand,'on');
        xlabel(axCommand,'Time (s)');
        ylabel(axCommand,'Control effort u (output)');
        title(axCommand,'Latency keeps the previous command active');
        legend(axCommand,'Location','best');

        if result.isStable
            stabilityText = 'inside unit circle';
        else
            stabilityText = 'not strictly inside unit circle';
        end
        summary.Text = sprintf([ ...
            'Ts %.3f s | Td %.3f s (%.0f%%) | Nyquist ratio %.2f | ' ...
            'delay phase %.1f deg | gap %.3f output | |p|max %.3f (%s)'], ...
            result.samplePeriodSec,result.computationDelaySec, ...
            100*result.delayFraction,result.nyquistRatio, ...
            result.delayPhaseAtBandwidthDeg,result.maximumAbsTrackingGap, ...
            result.spectralRadius,stabilityText);
    end
end
