function interactive
fig = uifigure('Name','P01 Mass-Spring-Damper','Position',[100 100 1100 700]);
g = uigridlayout(fig,[3 5]);
g.RowHeight = {'1x','1x',95};

axTime = uiaxes(g); axTime.Layout.Row = 1; axTime.Layout.Column = [1 3];
axPhase = uiaxes(g); axPhase.Layout.Row = 1; axPhase.Layout.Column = [4 5];
axEnergy = uiaxes(g); axEnergy.Layout.Row = 2; axEnergy.Layout.Column = [1 5];

mS = uislider(g,'Limits',[0.2 5],'Value',1,'MajorTicks',[0.2 1 2 3 4 5]);
mS.Layout.Row=3; mS.Layout.Column=1;
cS = uislider(g,'Limits',[0 8],'Value',0.8,'MajorTicks',[0 1 2 4 8]);
cS.Layout.Row=3; cS.Layout.Column=2;
kS = uislider(g,'Limits',[0.5 15],'Value',4,'MajorTicks',[0.5 4 8 12 15]);
kS.Layout.Row=3; kS.Layout.Column=3;
fS = uislider(g,'Limits',[0.2 5],'Value',1,'MajorTicks',[0.2 1 2 3 4 5]);
fS.Layout.Row=3; fS.Layout.Column=4;
summary = uilabel(g,'WordWrap','on'); summary.Layout.Row=3; summary.Layout.Column=5;

sliders = [mS cS kS fS];
for q = 1:numel(sliders)
    sliders(q).ValueChangingFcn = @(~,~) updatePlots();
    sliders(q).ValueChangedFcn = @(~,~) updatePlots();
end
updatePlots();

    function updatePlots
        out = model(mS.Value,cS.Value,kS.Value,fS.Value,12);
        cla(axTime); plot(axTime,out.t,out.position,'LineWidth',1.3);
        hold(axTime,'on'); yline(axTime,out.steady,'--'); hold(axTime,'off');
        grid(axTime,'on'); xlabel(axTime,'Time (s)'); ylabel(axTime,'Position');
        title(axTime,'Step response');

        cla(axPhase); plot(axPhase,out.position,out.velocity,'LineWidth',1.2);
        grid(axPhase,'on'); xlabel(axPhase,'Position'); ylabel(axPhase,'Velocity');
        title(axPhase,'Phase plane');

        energy = 0.5*mS.Value*out.velocity.^2 + 0.5*kS.Value*(out.position-out.steady).^2;
        cla(axEnergy); plot(axEnergy,out.t,energy,'LineWidth',1.2);
        grid(axEnergy,'on'); xlabel(axEnergy,'Time (s)'); ylabel(axEnergy,'Stored energy');
        title(axEnergy,'Damping removes mechanical energy');

        summary.Text = sprintf(['m = %.2f\nc = %.2f\nk = %.2f\nzeta = %.2f\n' ...
            'omega_n = %.2f rad/s\novershoot = %.1f%%'], ...
            mS.Value,cS.Value,kS.Value,out.zeta,out.wn,out.overshoot_percent);
    end
end
