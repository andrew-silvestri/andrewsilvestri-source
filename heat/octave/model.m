% Industrial Heat Electrification Break-Even Model (Texas) — GNU Octave port
% Mirrors ../model.py (reference implementation). Run:  octave model.m
% Headless-safe: uses gnuplot toolkit and prints PNGs next to this script.

1;  % script file

function out = crf(r, n)
  if r == 0, out = 1/n; else, out = r*(1+r)^n / ((1+r)^n - 1); end
end

function res = lcoh(p)
  KWH = 293.07;
  fuel_g = p.P_g / p.eta_g;
  fuel_e = KWH * p.P_e / p.eta_e;
  q = p.hours;
  res.gas.fuel  = fuel_g;
  res.gas.capex = p.capex_g * crf(p.r, p.life) / q;
  res.gas.fom   = p.capex_g * p.fom_g / q;
  res.gas.total = res.gas.fuel + res.gas.capex + res.gas.fom;
  res.elec.fuel  = fuel_e;
  res.elec.capex = p.capex_e * crf(p.r, p.life) / q;
  res.elec.fom   = p.capex_e * p.fom_e / q;
  res.elec.total = res.elec.fuel + res.elec.capex + res.elec.fom;
end

function pe = breakeven_Pe(p, full)
  KWH = 293.07;
  if nargin < 2, full = true; end
  if ~full
    pe = p.eta_e * p.P_g / (KWH * p.eta_g);
  else
    r = lcoh(p);
    pe = (r.gas.total - (r.elec.capex + r.elec.fom)) * p.eta_e / KWH;
  end
end

% ---------------- baseline parameters (traceable to source docs; see README)
p = struct('eta_e',0.98,'eta_g',0.85,'P_e',0.065,'P_g',3.50, ...
           'capex_g',50000,'capex_e',30000,'fom_e',0.01,'fom_g',0.02, ...
           'r',0.08,'life',20,'hours',6000,'ef_gas',53.06,'grid_ci',0.333);

KWH = 293.07;
r = lcoh(p);
printf("LCOH gas  = %.3f $/MMBtu\n", r.gas.total);
printf("LCOH elec = %.3f $/MMBtu\n", r.elec.total);
printf("break-even Pe (full)      = %.3f c/kWh\n", 100*breakeven_Pe(p, true));
printf("break-even Pe (fuel-only) = %.3f c/kWh\n", 100*breakeven_Pe(p, false));
e_gas = p.ef_gas / p.eta_g;
parity = e_gas * p.eta_e / KWH;
printf("emissions gas = %.2f kg/MMBtu; grid-CI parity = %.4f t/MWh\n", e_gas, parity);

% ---------------- figures
graphics_toolkit("gnuplot");
d = fileparts(mfilename("fullpath"));

Pg = linspace(1.5, 8, 200);
be = zeros(size(Pg)); bf = zeros(size(Pg));
for i = 1:numel(Pg)
  q = p; q.P_g = Pg(i);
  be(i) = 100*breakeven_Pe(q, true);
  bf(i) = 100*breakeven_Pe(q, false);
end
f = figure("visible","off");
plot(Pg, be, "linewidth", 2, Pg, bf, "--", "linewidth", 2);
hold on; plot(xlim, [p.P_e p.P_e]*100, "r-");
xlabel("Gas price [$/MMBtu]"); ylabel("Break-even Pe [cents/kWh]");
title("Spark-gap threshold (Octave)");
legend("full LCOH", "fuel-only", "TX industrial retail", "location", "northwest");
grid on;
print(f, fullfile(d, "fig1_breakeven_price_octave.png"), "-dpng", "-r140");

Pe = linspace(0.02, 0.12, 100); Pgv = linspace(1.5, 8, 100);
gap = zeros(numel(Pgv), numel(Pe));
for i = 1:numel(Pgv)
  for j = 1:numel(Pe)
    q = p; q.P_g = Pgv(i); q.P_e = Pe(j);
    rr = lcoh(q);
    gap(i,j) = rr.elec.total - rr.gas.total;
  end
end
f2 = figure("visible","off");
contourf(Pe*100, Pgv, gap, 21); colorbar;
hold on; contour(Pe*100, Pgv, gap, [0 0], "k", "linewidth", 2);
xlabel("Electricity price [cents/kWh]"); ylabel("Gas price [$/MMBtu]");
title("LCOH(elec) - LCOH(gas) [$/MMBtu] — black line = parity");
print(f2, fullfile(d, "fig3_costgap_contour_octave.png"), "-dpng", "-r140");
printf("figures written to %s\n", d);
