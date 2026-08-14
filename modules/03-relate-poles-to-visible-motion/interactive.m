function interactive
%INTERACTIVE Move stable pole real and imaginary coordinates independently.
fig = uifigure('Name','P03 Poles and Visible Motion', ...
    'Position',[100 100 1100 700]);
gridLayout = uigridlayout(fig,[2 6]);
gridLayout.RowHeight = {'1x',110};

axMotion = uiaxes(gridLayout);
axMotion.Layout.Row = 1;
axMotion.Layout.Column = [1 4];
axPoles = uiaxes(gridLayout);
axPoles.Layout.Row = 1;
axPoles.Layout.Column = [5 6];

realLabel = uilabel(gridLayout,'Text','Pole real part sigma (1/s)', ...
    'WordWrap','on');
realLabel.Layout.Row = 2;
realLabel.Layout.Column = 1;
realControl = uispinner(gridLayout,'Limits',[-1.2 -0.05], ...
    'Step',0.05,'Value',-0.5);
realControl.Layout.Row = 2;
realControl.Layout.Column = 2;

imagLabel = uilabel(gridLayout, ...
    'Text','Pole imaginary magnitude omega (rad/s)','WordWrap','on');
imagLabel.Layout.Row = 2;
imagLabel.Layout.Column = 3;
imagControl = uislider(gridLayout,'Limits',[0.2 4], ...
    'Value',2,'MajorTicks',[0.2 1 2 3 4]);
imagControl.Layout.Row = 2;
imagControl.Layout.Column = 4;

resetButton = uibutton(gridLayout,'Text','Reset baseline', ...
    'ButtonPushedFcn',@resetBaseline);
resetButton.Layout.Row = 2;
resetButton.Layout.Column = 5;
summary = uilabel(gridLayout,'WordWrap','on');
summary.Layout.Row = 2;
summary.Layout.Column = 6;

realControl.ValueChangedFcn = @(~,~) updatePlots();
imagControl.ValueChangingFcn = @previewImaginaryPart;
imagControl.ValueChangedFcn = @(~,~) updatePlots();
updatePlots();

    function previewImaginaryPart(~,event)
        updatePlots(event.Value);
    end

    function resetBaseline(~,~)
        realControl.Value = -0.5;
        imagControl.Value = 2;
        updatePlots();
    end

    function updatePlots(previewValue)
        if nargin < 1
            imagValue = imagControl.Value;
        else
            imagValue = previewValue;
        end
        result = model(realControl.Value,imagValue,1,0,12,0.01);

        cla(axMotion);
        plot(axMotion,result.t,result.position,'LineWidth',1.4, ...
            'DisplayName','Displacement x');
        hold(axMotion,'on');
        plot(axMotion,result.t,result.envelope,'--','LineWidth',1.1, ...
            'DisplayName','Envelope');
        plot(axMotion,result.t,-result.envelope,'--','LineWidth',1.1, ...
            'HandleVisibility','off');
        hold(axMotion,'off'); grid(axMotion,'on');
        xlabel(axMotion,'Time (s)');
        ylabel(axMotion,'Displacement (m)');
        title(axMotion,'Pole coordinates determine visible motion');
        legend(axMotion,'Location','northeast');

        cla(axPoles);
        plot(axPoles,real(result.poles),imag(result.poles),'x', ...
            'MarkerSize',12,'LineWidth',2,'DisplayName','Pole pair');
        hold(axPoles,'on');
        plot(axPoles,[0 0],[-4.5 4.5],'k--','DisplayName','Imaginary axis');
        hold(axPoles,'off'); grid(axPoles,'on');
        axis(axPoles,[-1.5 0.5 -4.5 4.5]);
        xlabel(axPoles,'Real part (1/s)');
        ylabel(axPoles,'Imaginary part (rad/s)');
        title(axPoles,'Pole plane');
        legend(axPoles,'Location','best');

        summary.Text = sprintf(['sigma = %.2f 1/s\nomega = %.2f rad/s\n' ...
            'envelope tau = %.2f s\nperiod = %.2f s'], ...
            realControl.Value,imagValue,result.envelopeTimeConstant, ...
            result.oscillationPeriod);
    end
end
