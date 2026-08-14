function interactive
%INTERACTIVE Explore input amplitude and time constant one at a time.
fig = uifigure('Name','P02 Integrator and First-Order Intuition', ...
    'Position',[100 100 1100 700]);
gridLayout = uigridlayout(fig,[3 6]);
gridLayout.RowHeight = {'1x','1x',105};

axOutput = uiaxes(gridLayout);
axOutput.Layout.Row = 1;
axOutput.Layout.Column = [1 6];
axRate = uiaxes(gridLayout);
axRate.Layout.Row = 2;
axRate.Layout.Column = [1 6];

amplitudeLabel = uilabel(gridLayout,'Text','Input amplitude A (normalized)', ...
    'WordWrap','on');
amplitudeLabel.Layout.Row = 3;
amplitudeLabel.Layout.Column = 1;
amplitudeControl = uispinner(gridLayout,'Limits',[-2 2],'Step',0.1,'Value',1);
amplitudeControl.Layout.Row = 3;
amplitudeControl.Layout.Column = 2;

tauLabel = uilabel(gridLayout,'Text','Time constant tau (s)','WordWrap','on');
tauLabel.Layout.Row = 3;
tauLabel.Layout.Column = 3;
tauControl = uislider(gridLayout,'Limits',[0.2 5],'Value',2, ...
    'MajorTicks',[0.2 1 2 3 4 5]);
tauControl.Layout.Row = 3;
tauControl.Layout.Column = 4;

resetButton = uibutton(gridLayout,'Text','Reset baseline', ...
    'ButtonPushedFcn',@resetBaseline);
resetButton.Layout.Row = 3;
resetButton.Layout.Column = 5;
summary = uilabel(gridLayout,'WordWrap','on');
summary.Layout.Row = 3;
summary.Layout.Column = 6;

amplitudeControl.ValueChangedFcn = @(~,~) updatePlots();
tauControl.ValueChangingFcn = @previewTau;
tauControl.ValueChangedFcn = @(~,~) updatePlots();
updatePlots();

    function previewTau(~,event)
        updatePlots(event.Value);
    end

    function resetBaseline(~,~)
        amplitudeControl.Value = 1;
        tauControl.Value = 2;
        updatePlots();
    end

    function updatePlots(previewValue)
        if nargin < 1
            tauValue = tauControl.Value;
        else
            tauValue = previewValue;
        end
        result = model(amplitudeControl.Value,tauValue,1,10,0.02);

        cla(axOutput);
        plot(axOutput,result.t,result.integrator,'LineWidth',1.4, ...
            'DisplayName','Integrator x_I');
        hold(axOutput,'on');
        plot(axOutput,result.t,result.firstOrder,'LineWidth',1.4, ...
            'DisplayName','First-order y');
        yline(axOutput,result.firstOrderSteady,'--','K A');
        hold(axOutput,'off'); grid(axOutput,'on');
        xlabel(axOutput,'Time (s)');
        ylabel(axOutput,'Output (command for y; command s for x_I)');
        title(axOutput,'Accumulation versus bounded settling');
        legend(axOutput,'Location','best');

        cla(axRate);
        plot(axRate,result.t,result.integratorRate,'LineWidth',1.4, ...
            'DisplayName','dx_I/dt');
        hold(axRate,'on');
        plot(axRate,result.t,result.firstOrderRate,'LineWidth',1.4, ...
            'DisplayName','dy/dt');
        hold(axRate,'off'); grid(axRate,'on');
        xlabel(axRate,'Time (s)');
        ylabel(axRate,'Rate (command for dx_I/dt; command/s for dy/dt)');
        title(axRate,'The first-order rate shrinks with its remaining gap');
        legend(axRate,'Location','best');

        summary.Text = sprintf(['A = %.1f\ntau = %.2f s\n' ...
            'integrator slope = %.1f\nfirst-order equilibrium = %.1f'], ...
            amplitudeControl.Value,tauValue,result.integratorSlope, ...
            result.firstOrderSteady);
    end
end
