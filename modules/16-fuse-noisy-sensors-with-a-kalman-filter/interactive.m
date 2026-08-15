function interactive
%INTERACTIVE Explore covariance-weighted sensor fusion and an outlier.
modelFunction = @model;
fig = uifigure('Name','P16 Fuse Noisy Sensors with a Kalman Filter', ...
    'Position',[80 80 1320 780]);
gridLayout = uigridlayout(fig,[2 10]);
gridLayout.RowHeight = {'1x',170};

axFusion = uiaxes(gridLayout);
axFusion.Layout.Row = 1;
axFusion.Layout.Column = [1 5];
axConsistency = uiaxes(gridLayout);
axConsistency.Layout.Row = 1;
axConsistency.Layout.Column = [6 10];

positionNoiseLabel = uilabel(gridLayout, ...
    'Text','Assumed sensor A noise std (m)','WordWrap','on');
positionNoiseLabel.Layout.Row = 2;
positionNoiseLabel.Layout.Column = 1;
positionNoiseControl = uislider(gridLayout,'Limits',[0.1 0.9], ...
    'Value',0.35,'MajorTicks',[0.1 0.35 0.6 0.9]);
positionNoiseControl.Layout.Row = 2;
positionNoiseControl.Layout.Column = [2 3];

processNoiseLabel = uilabel(gridLayout, ...
    'Text','Assumed acceleration noise std (m/s^2)','WordWrap','on');
processNoiseLabel.Layout.Row = 2;
processNoiseLabel.Layout.Column = 4;
processNoiseControl = uispinner(gridLayout,'Limits',[0.01 0.5], ...
    'Step',0.01,'Value',0.08,'ValueDisplayFormat','%.2f');
processNoiseControl.Layout.Row = 2;
processNoiseControl.Layout.Column = 5;

outlierControl = uidropdown(gridLayout, ...
    'Items',{'No outlier','+4 m sensor A outlier (broken)'}, ...
    'Value','No outlier');
outlierControl.Layout.Row = 2;
outlierControl.Layout.Column = [6 7];
resetButton = uibutton(gridLayout,'Text','Reset baseline');
resetButton.Layout.Row = 2;
resetButton.Layout.Column = 8;
summary = uilabel(gridLayout,'WordWrap','on');
summary.Layout.Row = 2;
summary.Layout.Column = [9 10];

positionNoiseControl.ValueChangingFcn = @(~,event) ...
    redraw(event.Value,processNoiseControl.Value,outlierControl.Value);
positionNoiseControl.ValueChangedFcn = @(~,~) ...
    redraw(positionNoiseControl.Value,processNoiseControl.Value, ...
    outlierControl.Value);
processNoiseControl.ValueChangedFcn = @(~,~) ...
    redraw(positionNoiseControl.Value,processNoiseControl.Value, ...
    outlierControl.Value);
outlierControl.ValueChangedFcn = @(~,~) ...
    redraw(positionNoiseControl.Value,processNoiseControl.Value, ...
    outlierControl.Value);
resetButton.ButtonPushedFcn = @(~,~) resetBaseline();
redraw(0.35,0.08,'No outlier');

    function resetBaseline
        positionNoiseControl.Value = 0.35;
        processNoiseControl.Value = 0.08;
        outlierControl.Value = 'No outlier';
        redraw(0.35,0.08,'No outlier');
    end

    function redraw(positionNoiseStdM,processNoiseStdMPerSec2,outlierChoice)
        positionNoiseStdM = round(positionNoiseStdM*100)/100;
        processNoiseStdMPerSec2 = round(processNoiseStdMPerSec2*100)/100;
        positionNoiseControl.Value = positionNoiseStdM;
        processNoiseControl.Value = processNoiseStdMPerSec2;
        if strcmp(outlierChoice,'No outlier')
            positionOutlierM = 0;
        else
            positionOutlierM = 4;
        end
        result = modelFunction(positionNoiseStdM, ...
            processNoiseStdMPerSec2,positionOutlierM,1601,20,0.05);

        cla(axFusion);
        plot(axFusion,result.timeSec,result.measurement(1,:),'.', ...
            'Color',[0.55 0.72 0.95],'DisplayName','Sensor A');
        hold(axFusion,'on');
        plot(axFusion,result.timeSec,result.measurement(2,:),'.', ...
            'Color',[0.85 0.72 0.55],'DisplayName','Sensor B');
        plot(axFusion,result.timeSec,result.trueState(1,:),'k-', ...
            'LineWidth',1.8,'DisplayName','True position');
        plot(axFusion,result.timeSec,result.posteriorEstimate(1,:),'b--', ...
            'LineWidth',1.6,'DisplayName','Fused position');
        hold(axFusion,'off'); grid(axFusion,'on');
        xlabel(axFusion,'Time (s)');
        ylabel(axFusion,'Position (m)');
        title(axFusion,'Two sensors, prediction, and fused estimate');
        legend(axFusion,'Location','best');

        cla(axConsistency);
        plot(axConsistency,result.timeSec, ...
            result.normalizedInnovationSquared,'LineWidth',1.4);
        hold(axConsistency,'on');
        yline(axConsistency,9.21,'--','Two-sensor 99% reference');
        hold(axConsistency,'off'); grid(axConsistency,'on');
        xlabel(axConsistency,'Time (s)');
        ylabel(axConsistency,'Normalized innovation squared');
        title(axConsistency,'Residual size relative to predicted covariance');

        if positionOutlierM > 0 && ...
                result.normalizedInnovationSquared(result.outlierIndex) > 50
            stateText = 'outlier exceeds the covariance model';
        elseif result.meanNormalizedInnovationSquaredTail > 4
            stateText = 'reported sensor noise is overconfident';
        else
            stateText = 'seeded fusion is covariance-consistent';
        end
        summary.Text = sprintf([ ...
            'Kp A/B %.3f / %.3f | rate gain %.3f 1/s | ' ...
            'tail RMSE %.3f m, %.3f m/s | mean NIS %.2f | %s'], ...
            result.steadyPrimaryPositionGain, ...
            result.steadyBackupPositionGain, ...
            result.steadyRateGainFromPrimaryPerSec, ...
            result.positionErrorRmsTailM,result.rateErrorRmsTailMPerSec, ...
            result.meanNormalizedInnovationSquaredTail,stateText);
    end
end
