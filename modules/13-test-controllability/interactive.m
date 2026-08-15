function interactive
%INTERACTIVE Move input authority, maneuver time, and state coupling.
modelFunction = @model;
fig = uifigure('Name','P13 Test Controllability', ...
    'Position',[80 80 1320 780]);
gridLayout = uigridlayout(fig,[2 9]);
gridLayout.RowHeight = {'1x',150};

axTransfer = uiaxes(gridLayout);
axTransfer.Layout.Row = 1;
axTransfer.Layout.Column = [1 4];
axProbe = uiaxes(gridLayout);
axProbe.Layout.Row = 1;
axProbe.Layout.Column = [5 9];

gainLabel = uilabel(gridLayout, ...
    'Text','Input gain ((m/s^2)/command)','WordWrap','on');
gainLabel.Layout.Row = 2;
gainLabel.Layout.Column = 1;
gainControl = uislider(gridLayout,'Limits',[0.25 2],'Value',1, ...
    'MajorTicks',[0.25 0.5 1 1.5 2]);
gainControl.Layout.Row = 2;
gainControl.Layout.Column = [2 3];

horizonLabel = uilabel(gridLayout, ...
    'Text','Maneuver time (s)','WordWrap','on');
horizonLabel.Layout.Row = 2;
horizonLabel.Layout.Column = 4;
horizonControl = uispinner(gridLayout,'Limits',[0.5 5], ...
    'Step',0.25,'Value',2);
horizonControl.Layout.Row = 2;
horizonControl.Layout.Column = 5;

couplingControl = uidropdown(gridLayout, ...
    'Items',{'Intact coupling','Disconnected (broken)'}, ...
    'Value','Intact coupling');
couplingControl.Layout.Row = 2;
couplingControl.Layout.Column = 6;
resetButton = uibutton(gridLayout,'Text','Reset baseline');
resetButton.Layout.Row = 2;
resetButton.Layout.Column = 7;
summary = uilabel(gridLayout,'WordWrap','on');
summary.Layout.Row = 2;
summary.Layout.Column = [8 9];

gainControl.ValueChangingFcn = @(~,event) ...
    redraw(event.Value,horizonControl.Value,couplingControl.Value);
gainControl.ValueChangedFcn = @(~,~) ...
    redraw(gainControl.Value,horizonControl.Value,couplingControl.Value);
horizonControl.ValueChangedFcn = @(~,~) ...
    redraw(gainControl.Value,horizonControl.Value,couplingControl.Value);
couplingControl.ValueChangedFcn = @(~,~) ...
    redraw(gainControl.Value,horizonControl.Value,couplingControl.Value);
resetButton.ButtonPushedFcn = @(~,~) resetBaseline();
redraw(gainControl.Value,horizonControl.Value,couplingControl.Value);

    function resetBaseline
        gainControl.Value = 1;
        horizonControl.Value = 2;
        couplingControl.Value = 'Intact coupling';
        redraw(1,2,'Intact coupling');
    end

    function redraw(inputGain,horizonSec,couplingMode)
        horizonSec = round(horizonSec/0.05)*0.05;
        horizonControl.Value = horizonSec;
        if strcmp(couplingMode,'Disconnected (broken)')
            coupling = 0;
        else
            coupling = 1;
        end
        result = modelFunction(inputGain,coupling,horizonSec,0.05);

        cla(axTransfer);
        plot(axTransfer,result.timeSec,result.stateTrajectory(1,:), ...
            'LineWidth',1.8,'DisplayName','Position / 1 m');
        hold(axTransfer,'on');
        plot(axTransfer,result.timeSec,result.stateTrajectory(2,:),'--', ...
            'LineWidth',1.5,'DisplayName','Rate / 1 m/s');
        yline(axTransfer,result.targetPositionM,'k:', ...
            'DisplayName','Position target');
        hold(axTransfer,'off'); grid(axTransfer,'on');
        xlabel(axTransfer,'Time (s)');
        ylabel(axTransfer,'Normalized transfer state');
        title(axTransfer,'Rest-to-rest target transfer');
        legend(axTransfer,'Location','best');

        cla(axProbe);
        plot(axProbe,result.timeSec,result.probeStateTrajectory(1,:), ...
            'LineWidth',1.8,'DisplayName','Probe position / 1 m');
        hold(axProbe,'on');
        plot(axProbe,result.timeSec,result.probeStateTrajectory(2,:),'--', ...
            'LineWidth',1.5,'DisplayName','Probe rate / 1 m/s');
        hold(axProbe,'off'); grid(axProbe,'on');
        xlabel(axProbe,'Time (s)');
        ylabel(axProbe,'Normalized probe state');
        title(axProbe,'Direct rate effect and coupled position effect');
        legend(axProbe,'Location','best');

        if ~result.targetReachable
            conditionText = 'position unreachable';
            effortText = 'energy N/A | peak N/A';
        elseif result.peakCommandMagnitude > 5
            conditionText = 'full rank, demanding command';
            effortText = sprintf('energy %.3g command^2*s | peak %.3g command', ...
                result.commandEnergyCommand2Sec,result.peakCommandMagnitude);
        else
            conditionText = 'full rank, target reconstructed';
            effortText = sprintf('energy %.3g command^2*s | peak %.3g command', ...
                result.commandEnergyCommand2Sec,result.peakCommandMagnitude);
        end
        summary.Text = sprintf([ ...
            'rank %d/2 | scaled sigma_min %.3g | %s | scaled residual %.3g | %s'], ...
            result.controllabilityRank,result.minimumSingularValue, ...
            effortText,result.terminalResidualNorm,conditionText);
    end
end
