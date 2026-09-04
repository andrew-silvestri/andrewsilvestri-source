% Storage arbitrage LP — MATLAB/GNU Octave port of ../model.py
% Uses Octave's built-in glpk() (MATLAB users: swap glpk for linprog with -f).
% Solves a 1-week demo window by default so it runs in seconds; set ndays=365
% for the full year (slow in glpk; the Python/Julia versions chunk monthly).

1;

function p = synthetic_prices(hours)
  rand("seed", 42); randn("seed", 42);
  p = zeros(hours, 1);
  for t = 0:hours-1
    hod = mod(t, 24); doy = mod(floor(t/24), 365);
    seasonal = 30 + 12*exp(-((doy-205)^2)/(2*45^2));
    diurnal = 1.0 + 0.35*exp(-((hod-18)^2)/(2*2.5^2)) + 0.15*exp(-((hod-8)^2)/(2*2^2)) ...
              - 0.25*exp(-((hod-3)^2)/(2*3^2)) - 0.20*exp(-((hod-13)^2)/(2*2^2));
    base = seasonal * diurnal * exp(0.35*randn());
    spike_prob = 0.002 + 0.02*exp(-((doy-205)^2)/(2*30^2))*exp(-((hod-18)^2)/(2*2^2));
    if rand() < spike_prob, base = base * (8 + 52*rand()); end
    base = min(base, 5000);
    if rand() < 0.015 && diurnal < 1.0, base = -(1 + 19*rand()); end
    p(t+1) = base;
  end
end

% ---- parameters
ndays = 7;                  % set 365 for full year
n = ndays * 24;
prices = synthetic_prices(n);
p_max = 1.0; dur = 4.0; E = dur * p_max;
rte = 0.86; eta = sqrt(rte); c_deg = 2.0; soc0 = 0.5 * E;

% ---- LP variables: [ch(1..n); dis(1..n); soc(1..n+1)]
nv = 2*n + (n+1);
c = zeros(nv, 1);
c(1:n) = -prices - c_deg*0.5;          % charging cost (maximize -> use glpk sense=-1... we minimize -obj)
c(n+1:2*n) = prices - c_deg*0.5;       % discharge revenue
% glpk minimizes by default; pass sense = -1 to maximize c'x
A = sparse(n+1, nv); b = zeros(n+1, 1);
% soc(1) = soc0
A(1, 2*n+1) = 1; b(1) = soc0;
% soc(t+1) - soc(t) - eta*ch(t) + dis(t)/eta = 0
for t = 1:n
  A(t+1, 2*n+t+1) = 1; A(t+1, 2*n+t) = -1;
  A(t+1, t) = -eta; A(t+1, n+t) = 1/eta;
end
lb = zeros(nv, 1);
ub = [p_max*ones(2*n,1); E*ones(n+1,1)];
ctype = repmat("S", 1, n+1);           % equality constraints
vartype = repmat("C", 1, nv);
[x, fval] = glpk(c, A, b, lb, ub, ctype, vartype, -1);   % sense=-1 -> maximize

ch = x(1:n); dis = x(n+1:2*n); soc = x(2*n+1:end);
rev = sum(prices .* (dis - ch));
printf("window: %d days | revenue $%.1f | cycles %.2f | rev/kW-yr (extrap) $%.1f\n", ...
       ndays, rev, sum(dis)/E, rev/(p_max*1000)*8760/n);

f = figure("visible", "off");
subplot(2,1,1); plot(prices, "k"); ylabel("$/MWh"); title("Prices and 4h dispatch (Octave)");
subplot(2,1,2); bar(dis, "facecolor", "g"); hold on; bar(-ch, "facecolor", "r");
plot(soc(1:end-1)/E, "b", "linewidth", 1.5);
legend("discharge MW", "charge MW", "SoC frac"); xlabel("hour");
print(f, fullfile(fileparts(mfilename("fullpath")), "fig_dispatch_octave.png"), "-dpng", "-r140");
