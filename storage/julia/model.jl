# Storage Revenue Stack Simulator — Julia/JuMP port of ../model.py
# The "real" version of this model in industry tooling: JuMP + HiGHS.
# Run locally:
#   julia> using Pkg; Pkg.activate("."); Pkg.instantiate(); include("model.jl")
# Untested in sandbox (Julia unavailable there); mirrors the verified Python LP.

using JuMP, HiGHS, Random, Printf, Statistics

"Synthetic ERCOT-like hourly DAM prices (same shape as Python; RNG differs slightly)."
function synthetic_prices(hours::Int = 8760; seed = 42)
    rng = MersenneTwister(seed)
    p = zeros(hours)
    for t in 0:hours-1
        hod = t % 24; doy = (t ÷ 24) % 365
        seasonal = 30 + 12 * exp(-((doy - 205)^2) / (2 * 45^2))
        diurnal = 1.0 + 0.35 * exp(-((hod - 18)^2) / (2 * 2.5^2)) +
                  0.15 * exp(-((hod - 8)^2) / (2 * 2.0^2)) -
                  0.25 * exp(-((hod - 3)^2) / (2 * 3.0^2)) -
                  0.20 * exp(-((hod - 13)^2) / (2 * 2.0^2))
        base = seasonal * diurnal * exp(0.35 * randn(rng))
        spike_prob = 0.002 + 0.02 * exp(-((doy - 205)^2) / (2 * 30^2)) *
                             exp(-((hod - 18)^2) / (2 * 2.0^2))
        if rand(rng) < spike_prob
            base *= 8 + 52 * rand(rng)
        end
        base = min(base, 5000.0)
        if rand(rng) < 0.015 && diurnal < 1.0
            base = -(1 + 19 * rand(rng))
        end
        p[t+1] = base
    end
    p
end

"""
Perfect-foresight LP dispatch, monthly chunks with SoC carry-over.
Returns (revenue, cycles, rev_per_kw_yr, dis, ch).
"""
function optimize_battery(prices; duration_h = 4.0, p_max = 1.0, rte = 0.86,
                          c_deg = 2.0, chunk_days = 30)
    eta = sqrt(rte); E = duration_h * p_max
    n = length(prices)
    ch = zeros(n); dis = zeros(n)
    soc0 = 0.5 * E
    chunk = chunk_days * 24
    for s in 1:chunk:n
        e = min(s + chunk - 1, n)
        T = s:e
        m = Model(HiGHS.Optimizer); set_silent(m)
        @variable(m, 0 <= c[T] <= p_max)
        @variable(m, 0 <= d[T] <= p_max)
        @variable(m, 0 <= x[s:e+1] <= E)
        @constraint(m, x[s] == soc0)
        @constraint(m, [t in T], x[t+1] == x[t] + eta * c[t] - d[t] / eta)
        @objective(m, Max, sum(prices[t] * (d[t] - c[t]) -
                               c_deg * 0.5 * (d[t] + c[t]) for t in T))
        optimize!(m)
        for t in T
            ch[t] = value(c[t]); dis[t] = value(d[t])
        end
        soc0 = value(x[e+1])
    end
    revenue = sum(prices .* (dis .- ch))
    cycles = sum(dis) / E
    (revenue = revenue, cycles = cycles,
     rev_per_kw_yr = revenue / (p_max * 1000) * 8760 / n, dis = dis, ch = ch)
end

function main()
    prices = synthetic_prices()
    @printf "price mean %.2f, p99 %.1f, neg hours %d\n" mean(prices) quantile(prices, 0.99) count(<(0), prices)
    for dur in (2.0, 4.0, 8.0)
        r = optimize_battery(prices; duration_h = dur)
        @printf "%2.0fh: %.1f \$/kW-yr, %.0f cycles\n" dur r.rev_per_kw_yr r.cycles
    end
    try
        @eval using Plots
        r = optimize_battery(prices; duration_h = 4.0)
        s, e = 200 * 24, 207 * 24
        plt = plot(s:e, prices[s:e]; color = :gray, lw = 1, label = "price",
                   ylabel = "\$/MWh", title = "4h dispatch, summer week")
        plt2 = bar(s:e, r.dis[s:e]; color = :green, label = "discharge MW")
        bar!(plt2, s:e, -r.ch[s:e]; color = :red, label = "charge MW")
        savefig(plot(plt, plt2; layout = (2, 1), size = (1000, 600)),
                joinpath(@__DIR__, "fig2_dispatch_week_julia.png"))
        println("figure written")
    catch e
        @warn "Plots.jl unavailable — LP results printed above" e
    end
end

abspath(PROGRAM_FILE) == @__FILE__ && main()
