# Industrial Heat Electrification Break-Even Model (Texas) — Julia port
# Faithful port of ../model.py. Computation uses only Base; plotting needs Plots.jl.
#
# Setup (local machine):
#   julia> using Pkg; Pkg.activate("."); Pkg.instantiate()   # installs Plots
#   julia> include("model.jl")
#
# NOTE: written/verified against the Python reference in a sandbox where Julia
# could not be installed (network allowlist). Logic matches model.py exactly;
# expect identical numbers.

using Printf

const KWH_PER_MMBTU = 293.07

Base.@kwdef struct Params
    eta_e::Float64  = 0.98      # electric boiler efficiency (0.95–0.99)
    eta_g::Float64  = 0.85      # gas boiler efficiency (0.80–0.90)
    P_e::Float64    = 0.065     # $/kWh TX industrial retail electricity (update w/ EIA)
    P_g::Float64    = 3.50      # $/MMBtu TX industrial gas (update w/ EIA)
    capex_g::Float64 = 50_000.0 # $ per MMBtu/hr installed
    capex_e::Float64 = 30_000.0 # $ per MMBtu/hr installed
    fom_e::Float64  = 0.01      # fraction of capex per year
    fom_g::Float64  = 0.02
    r::Float64      = 0.08      # real discount rate
    life::Int       = 20        # years
    hours::Float64  = 6000.0    # operating hours/yr at rated output
    ef_gas::Float64 = 53.06     # kgCO2/MMBtu fuel (EPA)
    grid_ci::Float64 = 0.333    # tCO2/MWh, ERCOT average (eGRID2023, 733.862 lb/MWh)
end

crf(r, n) = r == 0 ? 1 / n : r * (1 + r)^n / ((1 + r)^n - 1)

"LCOH components in \$/MMBtu delivered. Returns (gas=..., elec=...) named tuples."
function lcoh(p::Params)
    fuel_g = p.P_g / p.eta_g
    fuel_e = KWH_PER_MMBTU * p.P_e / p.eta_e
    q = p.hours                                   # MMBtu/yr per MMBtu/hr rated
    capg = p.capex_g * crf(p.r, p.life) / q
    cape = p.capex_e * crf(p.r, p.life) / q
    fomg = p.capex_g * p.fom_g / q
    fome = p.capex_e * p.fom_e / q
    (gas  = (fuel = fuel_g, capex = capg, fom = fomg, total = fuel_g + capg + fomg),
     elec = (fuel = fuel_e, capex = cape, fom = fome, total = fuel_e + cape + fome))
end

"Break-even electricity price [\$/kWh]; full=false gives the fuel-only spark-gap threshold."
function breakeven_Pe(p::Params; full::Bool = true)
    full || return p.eta_e * p.P_g / (KWH_PER_MMBTU * p.eta_g)
    r = lcoh(p)
    nonfuel_gap = r.gas.total - (r.elec.capex + r.elec.fom)
    return nonfuel_gap * p.eta_e / KWH_PER_MMBTU
end

"Emissions per MMBtu delivered [kgCO2] and grid-CI parity point [tCO2/MWh]."
function emissions(p::Params)
    e_gas  = p.ef_gas / p.eta_g
    e_elec = p.grid_ci * KWH_PER_MMBTU / p.eta_e   # tCO2/MWh ≡ kg/kWh
    parity = p.ef_gas / p.eta_g * p.eta_e / KWH_PER_MMBTU
    (gas = e_gas, elec = e_elec, parity_grid_ci = parity)
end

with(p::Params; kw...) = Params(; merge(ntfromstruct(p), values(kw))...)
ntfromstruct(p::Params) = NamedTuple{fieldnames(Params)}(ntuple(i -> getfield(p, i), fieldcount(Params)))

function main()
    p = Params()
    r = lcoh(p); em = emissions(p)
    @printf "LCOH gas   = %.3f \$/MMBtu\n" r.gas.total
    @printf "LCOH elec  = %.3f \$/MMBtu\n" r.elec.total
    @printf "gap        = %.3f \$/MMBtu\n" r.elec.total - r.gas.total
    @printf "break-even Pe (full LCOH) = %.3f ¢/kWh\n" breakeven_Pe(p) * 100
    @printf "break-even Pe (fuel only) = %.3f ¢/kWh\n" breakeven_Pe(p; full = false) * 100
    @printf "emissions gas/elec = %.2f / %.2f kg/MMBtu; parity CI = %.4f t/MWh\n" em.gas em.elec em.parity_grid_ci

    # ---- figures (requires Plots; comment out if running computation-only)
    try
        @eval using Plots
        Pg = range(1.5, 8.0; length = 200)
        be = [breakeven_Pe(with(p; P_g = pg)) * 100 for pg in Pg]
        bf = [breakeven_Pe(with(p; P_g = pg); full = false) * 100 for pg in Pg]
        plt = plot(Pg, be; lw = 2.5, label = "break-even Pe (full LCOH)",
                   xlabel = "Gas price [\$/MMBtu]", ylabel = "Break-even Pe [¢/kWh]",
                   title = "Spark-gap threshold", legend = :topleft)
        plot!(plt, Pg, bf; lw = 2, ls = :dash, label = "fuel-only")
        hline!(plt, [p.P_e * 100]; color = :red, label = "TX industrial retail")
        savefig(plt, joinpath(@__DIR__, "fig1_breakeven_price_julia.png"))

        Pe = range(0.02, 0.12; length = 120); Pgv = range(1.5, 8.0; length = 120)
        gap = [lcoh(with(p; P_e = pe, P_g = pg)).elec.total -
               lcoh(with(p; P_e = pe, P_g = pg)).gas.total for pg in Pgv, pe in Pe]
        plt2 = contourf(collect(Pe) .* 100, collect(Pgv), gap; c = :RdBu, levels = 21,
                        xlabel = "Electricity price [¢/kWh]", ylabel = "Gas price [\$/MMBtu]",
                        title = "LCOH(elec) − LCOH(gas) [\$/MMBtu]")
        contour!(plt2, collect(Pe) .* 100, collect(Pgv), gap; levels = [0.0], lc = :black, lw = 2)
        savefig(plt2, joinpath(@__DIR__, "fig3_costgap_contour_julia.png"))
        println("figures written next to model.jl")
    catch e
        @warn "Plots.jl not available — computation ran fine, skipping figures" e
    end
end

abspath(PROGRAM_FILE) == @__FILE__ && main()
