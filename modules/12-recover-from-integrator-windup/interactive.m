function interactive
%INTERACTIVE Move anti-windup gain and demand duration in the P12 model.
modelFunction = @model;
fig = uifigure('Name','P12 Recover from Integrator Windup', ...
    'Position',[80 80 1320 780]);
gridLayout = uigridlayout(fig,[2 8]);
gridLayout.RowHeight = {'1x',140};

axOutput = uiaxes(gridLayout);
axOutput.Layout.Row = 1;
axOutput.Layout.Column = [1 4];
axState = uiaxes(gridLayout);
axState.Layout.Row = 1;
axState.Layout.Column = [5 8];

gainLabel = uilabel(gridLayout, ...
    'Text','Anti-windup gain Kaw (1/s)','WordWrap','on');
gainLabel.Layout.Row = 2;
gainLabel.Layout.Column = 1;
gainControl = uislider(gridLayout,'Limits',[0 8],'Value',1, ...
    'MajorTicks',[0 0.5 1 2 4 8]);
gainControl.Layout.Row = 2;
gainControl.Layout.Column = [2 3];

durationLabel = uilabel(gridLayout, ...
    'Text','High-demand duration (s)','WordWrap','on');
durationLabel.Layout.Row = 2;
durationLabel.Layout.Column = 4;
durationControl = uislider(gridLayout,'Limits',[1 5],'Value',3, ...
    'MajorTicks',[1 2 3 4 5]);
durationControl.Layout.Row = 2;
durationControl.Layout.Column = [5 6];

resetButton = uibutton(gridLayout,'Text','Reset baseline');
resetButton.Layout.Row = 2;
resetButton.Layout.Column = 7;
summary = uilabel(gridLayout,'WordWrap','on');
summary.Layout.Row = 2;
summary.Layout.Column = 8;

gainControl.ValueChangingFcn = @(~,event) ...
    redraw(event.Value,durationControl.Value);
gainControl.ValueChangedFcn = @(~,~) ...
    redraw(gainControl.Value,durationControl.Value);
durationControl.ValueChangingFcn = @(~,event) ...
    redraw(gainControl.Value,event.Value);
durationControl.ValueChangedFcn = @(~,~) ...
    redraw(gainControl.Value,durationControl.Value);
resetButton.ButtonPushedFcn = @(~,~) resetBaseline();
redraw(gainControl.Value,durationControl.Value);

    function resetBaseline
        gainControl.Value = 1;
        durationControl.Value = 3;
        redraw(1,3);
    end

    function redraw(antiWindupGain,demandDurationSec)
        recoveryViewSec = 9;
        result = modelFunction(antiWindupGain,demandDurationSec, ...
            demandDurationSec+recoveryViewSec,0.01);

        cla(axOutput);
        stairs(axOutput,result.t,result.reference,'k:', ...
            'LineWidth',1.2,'DisplayName','Reference');
        hold(axOutput,'on');
        plot(axOutput,result.t,result.unprotected.plantOutput,'--', ...
            'LineWidth',1.4,'DisplayName','No anti-windup');
        plot(axOutput,result.t,result.protected.plantOutput, ...
            'LineWidth',1.8,'DisplayName','Back-calculation');
        xline(axOutput,result.demandDurationSec,':', ...
            'HandleVisibility','off');
        hold(axOutput,'off'); grid(axOutput,'on');
        xlabel(axOutput,'Time (s)');
        ylabel(axOutput,'Plant output y (output)');
        title(axOutput,'Same actuator, different integral-state recovery');
        legend(axOutput,'Location','best');

        cla(axState);
        plot(axState,result.t,result.unprotected.integralState,'--', ...
            'LineWidth',1.4,'DisplayName','Unprotected integral state');
        hold(axState,'on');
        plot(axState,result.t,result.protected.integralState, ...
            'LineWidth',1.8,'DisplayName','Protected integral state');
        stairs(axState,result.t,result.protected.appliedControl,':', ...
            'LineWidth',1.3,'DisplayName','Protected applied control');
        xline(axState,result.demandDurationSec,':', ...
            'HandleVisibility','off');
        hold(axState,'off'); grid(axState,'on');
        xlabel(axState,'Time (s)');
        ylabel(axState,'State or command (actuator)');
        title(axState,'Command-gap feedback drains unavailable effort');
        legend(axState,'Location','best');

        if antiWindupGain == 0
            protectionText = 'Kaw=0: paths coincide';
        elseif result.protected.integralStateAtRelease < 0
            protectionText = 'integral state over-unwinds before reversal';
        else
            protectionText = 'stored positive effort is reduced';
        end
        summary.Text = sprintf([ ...
            'Kaw %.2f 1/s | demand %.1f s | release I %.2f vs %.2f ' ...
            'actuator | recovery IAE %.2f vs %.2f output*s | %s'], ...
            result.antiWindupGainPerSec,result.demandDurationSec, ...
            result.unprotected.integralStateAtRelease, ...
            result.protected.integralStateAtRelease, ...
            result.unprotected.postReleaseIntegralAbsoluteError, ...
            result.protected.postReleaseIntegralAbsoluteError, ...
            protectionText);
    end
end
