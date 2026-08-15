function interactive
%INTERACTIVE Move PID gains while observing position and each force term.
% Retain the P06 model even after launch_lesson removes this folder from the
% MATLAB path or another lesson clears the global name-resolution cache.
modelFunction = @model;
fig = uifigure('Name','P06 Observe Each PID Term', ...
    'Position',[80 80 1280 760]);
gridLayout = uigridlayout(fig,[2 8]);
gridLayout.RowHeight = {'1x',125};

axPosition = uiaxes(gridLayout);
axPosition.Layout.Row = 1;
axPosition.Layout.Column = [1 4];
axTerms = uiaxes(gridLayout);
axTerms.Layout.Row = 1;
axTerms.Layout.Column = [5 8];

proportionalLabel = uilabel(gridLayout,'Text','Kp proportional (N/m)', ...
    'WordWrap','on');
proportionalLabel.Layout.Row = 2;
proportionalLabel.Layout.Column = 1;
proportionalControl = uislider(gridLayout,'Limits',[4 8], ...
    'Value',4,'MajorTicks',[4 5 6 7 8]);
proportionalControl.Layout.Row = 2;
proportionalControl.Layout.Column = 2;

integralLabel = uilabel(gridLayout,'Text','Ki integral (N/(m*s))', ...
    'WordWrap','on');
integralLabel.Layout.Row = 2;
integralLabel.Layout.Column = 3;
integralControl = uislider(gridLayout,'Limits',[0 2], ...
    'Value',1,'MajorTicks',[0 0.5 1 1.5 2]);
integralControl.Layout.Row = 2;
integralControl.Layout.Column = 4;

derivativeLabel = uilabel(gridLayout,'Text','Kd derivative (N*s/m)', ...
    'WordWrap','on');
derivativeLabel.Layout.Row = 2;
derivativeLabel.Layout.Column = 5;
derivativeControl = uislider(gridLayout,'Limits',[0 5], ...
    'Value',3,'MajorTicks',[0 1 2 3 4 5]);
derivativeControl.Layout.Row = 2;
derivativeControl.Layout.Column = 6;

resetButton = uibutton(gridLayout,'Text','Reset baseline', ...
    'ButtonPushedFcn',@resetBaseline);
resetButton.Layout.Row = 2;
resetButton.Layout.Column = 7;
summary = uilabel(gridLayout,'WordWrap','on');
summary.Layout.Row = 2;
summary.Layout.Column = 8;

proportionalControl.ValueChangingFcn = @previewProportional;
proportionalControl.ValueChangedFcn = @(~,~) updatePlots([],[],[]);
integralControl.ValueChangingFcn = @previewIntegral;
integralControl.ValueChangedFcn = @(~,~) updatePlots([],[],[]);
derivativeControl.ValueChangingFcn = @previewDerivative;
derivativeControl.ValueChangedFcn = @(~,~) updatePlots([],[],[]);
updatePlots([],[],[]);

    function previewProportional(~,event)
        updatePlots(event.Value,[],[]);
    end

    function previewIntegral(~,event)
        updatePlots([],event.Value,[]);
    end

    function previewDerivative(~,event)
        updatePlots([],[],event.Value);
    end

    function resetBaseline(~,~)
        proportionalControl.Value = 4;
        integralControl.Value = 1;
        derivativeControl.Value = 3;
        updatePlots([],[],[]);
    end

    function updatePlots(proportionalPreview,integralPreview,derivativePreview)
        if isempty(proportionalPreview)
            proportionalGain = proportionalControl.Value;
        else
            proportionalGain = proportionalPreview;
        end
        if isempty(integralPreview)
            integralGain = integralControl.Value;
        else
            integralGain = integralPreview;
        end
        if isempty(derivativePreview)
            derivativeGain = derivativeControl.Value;
        else
            derivativeGain = derivativePreview;
        end
        result = modelFunction( ...
            proportionalGain,integralGain,derivativeGain,-1,-1,20,0.01);

        cla(axPosition);
        plot(axPosition,result.t,result.referenceM*ones(size(result.t)), ...
            'k:','LineWidth',1.2,'DisplayName','Reference r');
        hold(axPosition,'on');
        plot(axPosition,result.t,result.positionM,'LineWidth',1.5, ...
            'DisplayName','Position x');
        hold(axPosition,'off'); grid(axPosition,'on');
        xlabel(axPosition,'Time (s)');
        ylabel(axPosition,'Position x (m)');
        title(axPosition,'Tracking under a constant -1 N load');
        legend(axPosition,'Location','southeast');

        cla(axTerms);
        plot(axTerms,result.t,result.proportionalControlN,'LineWidth',1.2, ...
            'DisplayName','P');
        hold(axTerms,'on');
        plot(axTerms,result.t,result.integralControlN,'LineWidth',1.2, ...
            'DisplayName','I');
        plot(axTerms,result.t,result.derivativeControlN,'LineWidth',1.2, ...
            'DisplayName','D');
        plot(axTerms,result.t,result.totalControlN,'k','LineWidth',1.5, ...
            'DisplayName','Total u');
        hold(axTerms,'off'); grid(axTerms,'on');
        xlabel(axTerms,'Time (s)');
        ylabel(axTerms,'Controller force (N)');
        title(axTerms,'Visible PID contributions');
        legend(axTerms,'Location','best');

        summary.Text = sprintf(['Kp %.2f N/m\nKi %.2f N/(m*s)\n' ...
            'Kd %.2f N*s/m\nfinal e %.3f m\novershoot %.3f m\nmax |u| %.2f N'], ...
            proportionalGain,integralGain,derivativeGain, ...
            result.finalTrackingErrorM,result.overshootM,result.maxAbsControlN);
    end
end
