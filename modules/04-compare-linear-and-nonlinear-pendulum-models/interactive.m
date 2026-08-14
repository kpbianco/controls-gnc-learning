function interactive
%INTERACTIVE Compare release angle and length effects one lever at a time.
fig = uifigure('Name','P04 Linear and Nonlinear Pendulums', ...
    'Position',[100 100 1150 720]);
gridLayout = uigridlayout(fig,[2 6]);
gridLayout.RowHeight = {'1x',120};

axMotion = uiaxes(gridLayout);
axMotion.Layout.Row = 1;
axMotion.Layout.Column = [1 4];
axRestoring = uiaxes(gridLayout);
axRestoring.Layout.Row = 1;
axRestoring.Layout.Column = [5 6];

angleLabel = uilabel(gridLayout,'Text','Release angle theta_0 (deg)', ...
    'WordWrap','on');
angleLabel.Layout.Row = 2;
angleLabel.Layout.Column = 1;
angleControl = uislider(gridLayout,'Limits',[1 120], ...
    'Value',20,'MajorTicks',[1 5 20 60 90 120]);
angleControl.Layout.Row = 2;
angleControl.Layout.Column = 2;

lengthLabel = uilabel(gridLayout,'Text','Pendulum length L (m)', ...
    'WordWrap','on');
lengthLabel.Layout.Row = 2;
lengthLabel.Layout.Column = 3;
lengthControl = uislider(gridLayout,'Limits',[0.3 2.5], ...
    'Value',1,'MajorTicks',[0.3 0.5 1 1.5 2 2.5]);
lengthControl.Layout.Row = 2;
lengthControl.Layout.Column = 4;

resetButton = uibutton(gridLayout,'Text','Reset baseline', ...
    'ButtonPushedFcn',@resetBaseline);
resetButton.Layout.Row = 2;
resetButton.Layout.Column = 5;
summary = uilabel(gridLayout,'WordWrap','on');
summary.Layout.Row = 2;
summary.Layout.Column = 6;

angleControl.ValueChangingFcn = @previewAngle;
angleControl.ValueChangedFcn = @(~,~) updatePlots([],[]);
lengthControl.ValueChangingFcn = @previewLength;
lengthControl.ValueChangedFcn = @(~,~) updatePlots([],[]);
updatePlots([],[]);

    function previewAngle(~,event)
        updatePlots(event.Value,[]);
    end

    function previewLength(~,event)
        updatePlots([],event.Value);
    end

    function resetBaseline(~,~)
        angleControl.Value = 20;
        lengthControl.Value = 1;
        updatePlots([],[]);
    end

    function updatePlots(anglePreview,lengthPreview)
        if isempty(anglePreview)
            angleDeg = angleControl.Value;
        else
            angleDeg = anglePreview;
        end
        if isempty(lengthPreview)
            lengthM = lengthControl.Value;
        else
            lengthM = lengthPreview;
        end
        result = model(angleDeg,0,lengthM,0.02,12,0.01);

        cla(axMotion);
        plot(axMotion,result.t,result.linearAngleDeg,'--','LineWidth',1.3, ...
            'DisplayName','Linear: sin(theta) replaced by theta');
        hold(axMotion,'on');
        plot(axMotion,result.t,result.nonlinearAngleDeg,'LineWidth',1.5, ...
            'DisplayName','Nonlinear: sin(theta) retained');
        hold(axMotion,'off'); grid(axMotion,'on');
        xlabel(axMotion,'Time (s)');
        ylabel(axMotion,'Angle theta (deg)');
        title(axMotion,'Same release state, different restoring models');
        legend(axMotion,'Location','northeast');

        cla(axRestoring);
        plot(axRestoring,result.restoringAngleRad*180/pi, ...
            result.linearRestoringAccelerationRadPerSec2,'--','LineWidth',1.3, ...
            'DisplayName','-g theta/L');
        hold(axRestoring,'on');
        plot(axRestoring,result.restoringAngleRad*180/pi, ...
            result.nonlinearRestoringAccelerationRadPerSec2,'LineWidth',1.5, ...
            'DisplayName','-g sin(theta)/L');
        hold(axRestoring,'off'); grid(axRestoring,'on');
        xlabel(axRestoring,'Angle theta (deg)');
        ylabel(axRestoring,'Restoring acceleration (rad/s^2)');
        title(axRestoring,'Why the predictions separate');
        legend(axRestoring,'Location','best');

        summary.Text = sprintf(['theta_0 = %.1f deg\nL = %.2f m\n' ...
            'T_small = %.2f s\nmax |delta theta| = %.2f deg'], ...
            angleDeg,lengthM,result.smallAnglePeriodSec,result.maxAbsErrorDeg);
    end
end
