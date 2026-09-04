"""
Process data for the life-cycle model.

Every number here is a per-functional-unit emission factor with a stated basis.
The structure is deliberately not a flat table of footprints: a flat table can
tell you a tomato is 0.4 kg CO2e and nothing else. This is a graph of processes,
each of which knows what it consumes, so the model can be asked *why* — which is
the whole point.

Two ideas carry the weight.

**Direct emissions** are what a process releases itself, per unit of its own
output. A tractor pass emits diesel combustion products. A field emits nitrous
oxide. Nothing upstream is included.

**Allocation** is the fraction of a process that should be charged to our
product. This is the part most footprint numbers hide. A dairy cow produces milk
and, eventually, beef; charging all of her methane to the milk is a choice, not
a measurement. ISO 14044 asks for physical causality first and economic value
second, and where the split is genuinely arbitrary this file says so in the
note. Allocation multiplies down a chain: a fertiliser plant's emissions reach
our tomato multiplied by every allocation factor between them.

Emission factors are drawn from the ranges in Poore & Nemecek (Science, 2018),
IPCC AR6 Chapter 7 and the 2019 Refinement to the IPCC Guidelines, ecoinvent
process descriptions, and DEFRA/BEIS transport factors. They are representative
figures for a class of production, not measurements of any particular farm.
"""

# ---------------------------------------------------------------- regions ---
# Grid intensity in kg CO2e per kWh, and a coordinate for distance.
# Grid figures are operating margin, roughly 2023-2024.
REGIONS = {
    "ES": dict(name="Spain",        lat=40.0, lon=-3.7,   grid=0.17),
    "NL": dict(name="Netherlands",  lat=52.1, lon=5.3,    grid=0.27),
    "MA": dict(name="Morocco",      lat=31.8, lon=-7.1,   grid=0.61),
    "MX": dict(name="Mexico",       lat=23.6, lon=-102.6, grid=0.42),
    "US-TX": dict(name="Texas",     lat=31.0, lon=-99.0,  grid=0.37),
    "US-CA": dict(name="California",lat=36.8, lon=-119.4, grid=0.21),
    "US-NY": dict(name="New York",  lat=42.9, lon=-75.5,  grid=0.21),
    "BR": dict(name="Brazil",       lat=-14.2, lon=-51.9, grid=0.10),
    "CO": dict(name="Colombia",     lat=4.6,  lon=-74.1,  grid=0.16),
    "ET": dict(name="Ethiopia",     lat=9.1,  lon=40.5,   grid=0.03),
    "CN": dict(name="China",        lat=35.9, lon=104.2,  grid=0.55),
    "IN": dict(name="India",        lat=20.6, lon=79.0,   grid=0.63),
    "AU": dict(name="Australia",    lat=-25.3, lon=133.8, grid=0.51),
    "NZ": dict(name="New Zealand",  lat=-41.0, lon=174.9, grid=0.10),
    "KE": dict(name="Kenya",        lat=-0.02, lon=37.9,  grid=0.09),
    "CI": dict(name="Cote d'Ivoire",lat=7.5,  lon=-5.5,   grid=0.44),
    "FR": dict(name="France",       lat=46.6, lon=2.2,    grid=0.06),
    "IT": dict(name="Italy",        lat=41.9, lon=12.6,   grid=0.33),
    "PE": dict(name="Peru",         lat=-9.2, lon=-75.0,  grid=0.25),
    "VN": dict(name="Vietnam",      lat=14.1, lon=108.3,  grid=0.44),
    "DE": dict(name="Germany",      lat=51.2, lon=10.4,   grid=0.38),
    "GB": dict(name="United Kingdom",lat=54.0, lon=-2.0,   grid=0.21),
    "PL": dict(name="Poland",       lat=51.9, lon=19.1,   grid=0.66),
    "NO": dict(name="Norway",       lat=60.5, lon=8.5,    grid=0.02),
    "JP": dict(name="Japan",        lat=36.2, lon=138.3,  grid=0.47),
    "KR": dict(name="South Korea",  lat=35.9, lon=127.8,  grid=0.44),
    "ZA": dict(name="South Africa", lat=-30.6, lon=22.9,  grid=0.87),
    "CA": dict(name="Canada",       lat=56.1, lon=-106.3, grid=0.12),
}

# ------------------------------------------------------------- transport ----
# kg CO2e per tonne-kilometre, well-to-wheel. Air freight is two orders of
# magnitude worse than sea and that single fact decides more food footprints
# than any farming practice.
TRANSPORT = {
    "sea":   dict(name="container ship", ef=0.012, speed_kmh=37,
                  note="DEFRA 2023 bulk container, well-to-wheel"),
    "road":  dict(name="refrigerated truck", ef=0.115, speed_kmh=65,
                  note="DEFRA 2023 articulated HGV, refrigerated uplift"),
    "rail":  dict(name="freight rail", ef=0.028, speed_kmh=45,
                  note="DEFRA 2023 freight rail"),
    "air":   dict(name="air freight", ef=1.05, speed_kmh=800,
                  note="DEFRA 2023 long-haul belly freight, with RFI ~1.9"),
}

# --------------------------------------------------------------- processes --
# direct: kg CO2e per unit of this process's own output
# unit:   what one unit of output is
# inputs: (process id, amount of that input per unit of this output, allocation)
#
# The allocation on an edge answers: of this input's burden, what share belongs
# to us? It is 1.0 unless the input process makes something else too.
PROCESSES = {

    # ---- energy and materials, the deep background ----------------------
    "natgas_extraction": dict(
        name="Natural gas extraction", unit="kg gas", direct=0.42,
        note="Includes about 1.5% fugitive methane at 28 kg CO2e per kg "
             "(the AR5 100-year value; AR6 gives 29.8 for fossil methane). "
             "The leak rate is the single most disputed number in the gas "
             "chain and ranges 0.5-3.5%. Until 2026-09-04 this note said "
             "82x, the 20-year value, which the figure does not use.",
        quality="B", inputs=[]),
    "ammonia": dict(
        name="Ammonia synthesis (Haber-Bosch)", unit="kg N", direct=1.9,
        note="Steam methane reforming plus synthesis. About 1.2 kg of the "
             "total is process CO2 from reforming and 0.7 kg is combustion.",
        quality="A", inputs=[("natgas_extraction", 0.62, 1.0)]),
    "nitrate_fert": dict(
        name="Nitric acid and nitrate finishing", unit="kg N", direct=1.4,
        note="Nitrous oxide from nitric acid production. Abated plants emit a "
             "fifth of this; unabated ones several times more.",
        quality="B", inputs=[("ammonia", 1.0, 1.0)]),
    "phosphate_fert": dict(
        name="Phosphate rock and processing", unit="kg P2O5", direct=1.1,
        note="Mining, beneficiation, acidulation.", quality="B", inputs=[]),
    "pesticide": dict(
        name="Pesticide manufacture", unit="kg active", direct=11.0,
        note="Energy-intensive fine chemical synthesis. Small mass, large "
             "factor, usually a minor share of a crop total.",
        quality="C", inputs=[("natgas_extraction", 1.8, 1.0)]),
    "diesel": dict(
        name="Diesel, refined and burned", unit="litre", direct=3.17,
        note="2.68 kg tailpipe plus about 0.49 kg refining and distribution.",
        quality="A", inputs=[]),
    "steel": dict(
        name="Steel, primary", unit="kg", direct=2.1,
        note="Blast furnace route.", quality="A", inputs=[]),
    "plastic_film": dict(
        name="Polyethylene film", unit="kg", direct=2.6,
        note="Resin plus extrusion.", quality="B",
        inputs=[("natgas_extraction", 0.9, 1.0)]),
    "cardboard": dict(
        name="Corrugated board", unit="kg", direct=0.94,
        note="Mixed virgin and recycled fibre, European average.",
        quality="B", inputs=[]),
    "glass_jar": dict(
        name="Glass container", unit="kg", direct=1.25,
        note="Furnace melt dominates. Heavy, which makes transport matter.",
        quality="B", inputs=[]),

    # ---- shared farm operations -----------------------------------------
    "field_n2o": dict(
        name="Soil nitrous oxide", unit="kg N applied", direct=4.4,
        note="IPCC 2019 refinement: about 1% of applied nitrogen leaves as "
             "N2O-N, and nitrous oxide is 273 times carbon dioxide over a "
             "century. This is why nitrogen dominates crop footprints.",
        quality="A", inputs=[]),
    "tillage": dict(
        name="Tillage and field passes", unit="hectare-season", direct=0.0,
        note="Emissions arrive through diesel.", quality="B",
        inputs=[("diesel", 95.0, 1.0)]),
    "irrigation_kwh": dict(
        name="Irrigation pumping", unit="kWh", direct=0.0,
        note="Charged at the producing region's grid intensity.",
        quality="A", inputs=[], grid_scaled=True),
    "process_kwh": dict(
        name="Processing electricity", unit="kWh", direct=0.0,
        note="Electricity used where the thing is made - milking parlours, "
             "slaughter lines, hulling, milling, glasshouse handling - and "
             "therefore charged at the PRODUCING region's grid, not the "
             "consuming one. Getting this backwards is an easy and invisible "
             "error: it makes a French dairy look dirty because someone in "
             "India ate the cheese.",
        quality="A", inputs=[], grid_scaled=True),
    "cold_store_origin": dict(
        name="Cold storage at origin", unit="kWh", direct=0.0,
        note="Chilling before export, charged at the producing grid.",
        quality="A", inputs=[], grid_scaled=True),
    "greenhouse_heat": dict(
        name="Greenhouse heating", unit="kg gas burned", direct=2.75,
        note="Combustion only. Heated winter production in northern Europe "
             "can exceed the entire rest of a tomato's chain.",
        quality="A", inputs=[("natgas_extraction", 1.0, 1.0)]),

    # ---- post-farm -------------------------------------------------------
    "cold_store_kwh": dict(
        name="Cold storage", unit="kWh", direct=0.0,
        note="Charged at the consuming region's grid intensity.",
        quality="A", inputs=[], grid_scaled=True, consumer_grid=True),
    "retail_kwh": dict(
        name="Retail refrigeration and lighting", unit="kWh", direct=0.0,
        note="Includes an allowance for refrigerant leakage, which for older "
             "supermarket systems can rival the electricity itself.",
        quality="B", inputs=[], grid_scaled=True, consumer_grid=True),
    "home_kwh": dict(
        name="Household use", unit="kWh", direct=0.0,
        note="Refrigeration and cooking in the consuming region.",
        quality="B", inputs=[], grid_scaled=True, consumer_grid=True),

    # ---- fuels, vehicles and textiles -----------------------------------
    "petrol": dict(
        name="Petrol, refined and burned", unit="litre", direct=2.92,
        note="2.31 kg leaves the tailpipe as carbon dioxide; the rest is "
             "extraction, refining and distribution. Refining a litre of "
             "petrol costs about a fifth of what burning it costs.",
        quality="A", inputs=[]),
    "jet_fuel": dict(
        name="Jet kerosene, refined and burned", unit="kg", direct=3.67,
        note="3.15 kg of carbon dioxide from combustion plus 0.52 kg "
             "well-to-tank. This is the carbon only; the contrails and the "
             "nitrogen oxides are handled separately because they are not "
             "carbon dioxide and do not behave like it.",
        quality="A", inputs=[]),
    "aviation_nonco2": dict(
        name="Contrails and nitrogen oxides", unit="kg fuel", direct=2.57,
        note="Aviation's non-carbon effects - contrail cirrus, ozone from "
             "nitrogen oxides - are estimated to roughly double the warming "
             "from the carbon dioxide alone. This is the single most disputed "
             "number in aviation accounting, and the range in the literature "
             "is a factor of three. Lee et al. 2021 is the basis here.",
        quality="C", inputs=[]),
    "aluminium": dict(
        name="Aluminium, primary", unit="kg", direct=8.6,
        note="Smelting is electricity almost all the way down, so the figure "
             "swings by a factor of three between a hydro-powered smelter and "
             "a coal-powered one. This is a world average.",
        quality="B", inputs=[]),
    "vehicle_glider": dict(
        name="Vehicle body and drivetrain", unit="kg of vehicle", direct=0.0,
        note="Everything in a car except the battery: steel, aluminium, "
             "plastics, glass, and the energy to press and assemble them.",
        quality="B",
        inputs=[("steel", 0.62, 1.0), ("aluminium", 0.11, 1.0),
                ("plastic_film", 0.14, 1.0), ("process_kwh", 2.1, 1.0)]),
    "li_battery": dict(
        name="Lithium-ion pack", unit="kWh of capacity", direct=42.0,
        note="Cell chemistry, cathode metals and pack assembly. Reported "
             "between 61 and 106 kg CO2e per kWh a few years ago and falling "
             "fast as cell factories move onto cleaner grids; 70 total is a "
             "reasonable current figure, of which this is the non-electric "
             "part.",
        quality="C",
        inputs=[("process_kwh", 55.0, 1.0), ("aluminium", 1.4, 1.0)]),
    "tyres_maint": dict(
        name="Tyres, servicing and fluids", unit="1,000 km", direct=1.9,
        note="Consumables over the life of the vehicle, spread across "
             "distance. Includes tyre and brake wear as materials, not as "
             "particulate pollution, which this model does not track.",
        quality="C", inputs=[]),
    "road_infra": dict(
        name="Road construction and upkeep", unit="1,000 vehicle-km",
        direct=4.2,
        note="Cement and bitumen, amortised over traffic. Almost always left "
             "out of a per-kilometre figure, which is why per-kilometre "
             "figures for cars and for trains are rarely comparable.",
        quality="C", inputs=[]),

    "cotton_fibre": dict(
        name="Cotton, field to bale", unit="kg fibre", direct=0.9,
        note="Ginning and field operations. The nitrogen and the irrigation "
             "are charged separately below, because for cotton they are the "
             "larger half and hiding them inside one number is how a "
             "t-shirt ends up looking cheap.",
        quality="B",
        inputs=[("field_n2o", 0.055, 1.0), ("ammonia", 0.055, 1.0),
                ("irrigation_kwh", 1.9, 1.0), ("pesticide", 0.011, 1.0),
                ("diesel", 0.28, 1.0)]),
    "polyester_fibre": dict(
        name="Polyester fibre", unit="kg fibre", direct=3.1,
        note="Polymerisation and melt spinning from petrochemical feedstock. "
             "Twice the carbon of cotton at the fibre, and less over a "
             "lifetime, because it is washed cooler and dried faster.",
        quality="B", inputs=[("natgas_extraction", 1.5, 1.0)]),
    "yarn_fabric": dict(
        name="Spinning, knitting and weaving", unit="kg fabric", direct=0.0,
        note="Mechanical processing, charged at the producing country's grid. "
             "This is where the location of a garment factory starts to "
             "matter more than the fibre it is working with.",
        quality="B", inputs=[("process_kwh", 5.4, 1.0)]),
    "dyeing": dict(
        name="Dyeing and finishing", unit="kg fabric", direct=2.4,
        note="Wet processing needs steam, and in most textile regions that "
             "steam comes from coal. The direct figure here is the boiler; "
             "the electricity is separate.",
        quality="B", inputs=[("process_kwh", 2.2, 1.0)]),
    "cut_sew": dict(
        name="Cutting and sewing", unit="garment", direct=0.0,
        note="Surprisingly small. Assembly is labour, not energy.",
        quality="B", inputs=[("process_kwh", 1.1, 1.0)]),
    "leather": dict(
        name="Leather, tanned", unit="kg", direct=6.8,
        note="Tanning only. The hide itself arrives from a cow whose burden "
             "is charged at the allocation on the edge above, and that "
             "allocation is the most consequential judgement in this file: by "
             "economic value a hide is worth about 2% of the animal, by mass "
             "about 7%, and published footprints for a leather shoe differ "
             "threefold on exactly this point.",
        quality="C", inputs=[("process_kwh", 3.2, 1.0)]),
    "rubber_sole": dict(
        name="Sole compound, rubber and foam", unit="kg", direct=3.4,
        note="Ethylene-vinyl acetate foam and rubber, moulded.",
        quality="C", inputs=[("natgas_extraction", 0.9, 1.0)]),
    "laundry_kwh": dict(
        name="Washing and drying", unit="kWh", direct=0.0,
        note="Charged at the wearer's grid, because this happens where the "
             "garment is worn rather than where it was made. For a cotton "
             "t-shirt washed weekly for three years, this is the largest "
             "single item in the whole chain.",
        quality="B", inputs=[], grid_scaled=True, consumer_grid=True),
    "landfill": dict(
        name="Food waste to landfill", unit="kg waste", direct=0.55,
        note="Anaerobic decay to methane, partially captured. Composting or "
             "digestion is roughly a fifth of this.",
        quality="B", inputs=[]),
}

# ---------------------------------------------------------------- products --
# Each product is a spine of life-cycle stages. A stage lists its inputs the
# same way a process does. Amounts are per kilogram of product as eaten, so
# losses along the chain are already folded into the amounts.
#
# Three multipliers can sit on a stage, and they are three different things.
# Until 2026-09-04 all three lived in one field called `allocation`, which is
# how a mass in kilograms came to be displayed as "allocation 160%".
#
#   share       Co-product allocation: the fraction of this stage's burden
#               that belongs to this product because the stage also makes
#               something else (hide, whey, bran, pulp). Always 0 < share <= 1.
#   basis       Required beside every share: the allocation basis and its
#               source ("physical, IDF feed-energy (Flysjo et al. 2011,
#               Sweden)"), or "unstated (assumed)" when there is none. A
#               number whose basis lives only in a comment is one refactor
#               from being wrong again; test_lca.py fails if it is missing.
#   amortise    Capital-good amortisation: the fraction of a vehicle charged
#               to one functional unit, = functional unit / lifetime. This is
#               the field the lifetime slider rescales.
#   freight_kg  Mass shipped on a transport stage, in kilograms per functional
#               unit. Food products ship one kilogram and omit it; a garment
#               ships its own weight plus packaging.
#
# The engine multiplies share x amortise onto everything in the stage, and
# freight_kg onto the freight leg only. Renaming changed no total.
PRODUCTS = {

    "tomato_field": dict(
        name="Tomato, field grown", unit="1 kg as eaten", category="Vegetable", group="Food",
        note="Open-field production. The comparison with the heated-greenhouse "
             "entry is the clearest demonstration in this model that how a "
             "thing is grown matters more than how far it travelled.",
        default_origin="ES", default_dest="US-TX",
        waste_frac=0.19, transport_mode="sea",
        stages=[
            dict(id="cultivation", name="Cultivation", inputs=[
                ("field_n2o", 0.0035, 1.0),
                ("ammonia", 0.0035, 1.0),
                ("nitrate_fert", 0.0012, 1.0),
                ("phosphate_fert", 0.0009, 1.0),
                ("pesticide", 0.00012, 1.0),
                ("irrigation_kwh", 0.075, 1.0),
                ("tillage", 0.00002, 1.0),
            ], direct=0.0,
               note="Nitrogen enters three ways: as the ammonia that made the "
                    "fertiliser, as the nitric acid that finished it, and as "
                    "the nitrous oxide the soil releases afterwards. The third "
                    "is usually the largest and is invisible at the farm gate."),
            dict(id="harvest", name="Harvest and grading", inputs=[
                ("diesel", 0.010, 1.0)], direct=0.0,
                note="Mechanical harvest and on-farm handling."),
            dict(id="packing", name="Packing", inputs=[
                ("cardboard", 0.055, 1.0),
                ("plastic_film", 0.008, 1.0),
                ("cold_store_origin", 0.045, 1.0)], direct=0.0,
                note="Packaging is small for produce sold loose and grows "
                     "quickly for anything sold in a tray."),
            dict(id="freight", name="Freight to market", inputs=[],
                 direct=0.0, transport=True,
                 note="Computed from the great-circle distance between origin "
                      "and destination and the chosen mode."),
            dict(id="distribution", name="Distribution and retail", inputs=[
                ("road", 240, 1.0),
                ("cold_store_kwh", 0.10, 1.0),
                ("retail_kwh", 0.14, 1.0)], direct=0.0,
                note="Regional haul plus time on a chilled shelf."),
            dict(id="consumer", name="Consumer", inputs=[
                ("home_kwh", 0.06, 1.0),
                ("road", 7, 1.0)], direct=0.0,
                note="Fridge time and a share of the drive home."),
            dict(id="waste", name="End of life", inputs=[], direct=0.0,
                 waste=True,
                 note="Household and retail losses, sent to landfill."),
        ]),

    "tomato_greenhouse": dict(
        name="Tomato, heated greenhouse", unit="1 kg as eaten",
        category="Vegetable", group="Food",
        note="Northern European winter production under glass. Same plant, "
             "same distance, different heating.",
        default_origin="NL", default_dest="US-NY",
        waste_frac=0.19, transport_mode="sea",
        stages=[
            dict(id="cultivation", name="Cultivation under glass", inputs=[
                ("greenhouse_heat", 0.62, 1.0),
                ("field_n2o", 0.0030, 1.0),
                ("ammonia", 0.0030, 1.0),
                ("nitrate_fert", 0.0010, 1.0),
                ("irrigation_kwh", 0.11, 1.0),
                ("plastic_film", 0.004, 1.0),
            ], direct=0.0,
               note="The heating term is the entire story. Everything else in "
                    "this product is within noise of the field-grown version."),
            dict(id="harvest", name="Harvest and grading", inputs=[
                ("process_kwh", 0.012, 1.0)], direct=0.0,
                note="Glasshouse handling is largely electric."),
            dict(id="packing", name="Packing", inputs=[
                ("cardboard", 0.060, 1.0),
                ("plastic_film", 0.012, 1.0),
                ("cold_store_origin", 0.045, 1.0)], direct=0.0,
                note="Glasshouse fruit is usually sold in trays."),
            dict(id="freight", name="Freight to market", inputs=[],
                 direct=0.0, transport=True, note="As chosen."),
            dict(id="distribution", name="Distribution and retail", inputs=[
                ("road", 240, 1.0),
                ("cold_store_kwh", 0.10, 1.0),
                ("retail_kwh", 0.14, 1.0)], direct=0.0, note="As above."),
            dict(id="consumer", name="Consumer", inputs=[
                ("home_kwh", 0.06, 1.0),
                ("road", 7, 1.0)], direct=0.0, note="As above."),
            dict(id="waste", name="End of life", inputs=[], direct=0.0,
                 waste=True, note="As above."),
        ]),

    "beef": dict(
        name="Beef, from a dedicated herd", unit="1 kg as eaten",
        category="Meat", group="Food",
        note="A beef herd raised for meat, not a dairy cow at the end of her "
             "milking life. That distinction is worth more than a factor of "
             "two and is the most common sleight of hand in beef footprints.",
        default_origin="BR", default_dest="US-TX",
        waste_frac=0.12, transport_mode="sea",
        stages=[
            dict(id="enteric", name="Enteric fermentation", inputs=[],
                 direct=38.0,
                 note="Methane from rumen microbes, at 27 times carbon dioxide "
                      "over a century. No feed change removes this; it is what "
                      "a ruminant is."),
            dict(id="feed", name="Feed production", inputs=[
                ("field_n2o", 0.42, 1.0),
                ("ammonia", 0.42, 1.0),
                ("nitrate_fert", 0.15, 1.0),
                ("tillage", 0.0018, 1.0),
                ("diesel", 0.55, 1.0),
            ], direct=0.0,
               note="Roughly 25 kg of feed per kg of carcass, most of it "
                    "pasture or forage, with the nitrogen following it."),
            dict(id="manure", name="Manure management", inputs=[], direct=6.2,
                 note="Methane and nitrous oxide from stored manure. Highly "
                      "sensitive to whether storage is anaerobic."),
            dict(id="landuse", name="Land use change", inputs=[], direct=16.0,
                 note="Amortised pasture expansion into forest. This is the "
                      "term that separates a Brazilian figure from a European "
                      "one, and the amortisation window - twenty years by "
                      "convention - is an accounting choice, not a fact.",
                 land_use=True),
            dict(id="slaughter", name="Slaughter and processing", inputs=[
                ("process_kwh", 0.55, 1.0),
                ("cold_store_origin", 0.35, 1.0)], direct=0.0,
                share=0.72, basis="economic (assumed)",
                note="Allocation: hide, tallow, offal and bone meal leave the "
                     "plant as saleable products, so not all of the plant's "
                     "burden belongs to the meat. 0.72 is an economic split; a "
                     "mass split would give roughly 0.55 and a different total. "
                     "Neither figure is from a named source."),
            dict(id="freight", name="Freight to market", inputs=[],
                 direct=0.0, transport=True, note="Frozen or chilled."),
            dict(id="distribution", name="Distribution and retail", inputs=[
                ("road", 380, 1.0),
                ("cold_store_kwh", 0.30, 1.0),
                ("retail_kwh", 0.25, 1.0)], direct=0.0,
                note="Meat sits in colder cabinets than produce."),
            dict(id="consumer", name="Consumer", inputs=[
                ("home_kwh", 0.55, 1.0),
                ("road", 9, 1.0)], direct=0.0,
                note="Freezer time and cooking, which for beef is significant."),
            dict(id="waste", name="End of life", inputs=[], direct=0.0,
                 waste=True, note="Trim, bone and plate waste."),
        ]),

    "chicken": dict(
        name="Chicken", unit="1 kg as eaten", category="Meat", group="Food",
        note="A monogastric animal with no rumen, which is most of why it "
             "sits an order of magnitude below beef.",
        default_origin="BR", default_dest="US-TX",
        waste_frac=0.12, transport_mode="sea",
        stages=[
            dict(id="feed", name="Feed production", inputs=[
                ("field_n2o", 0.055, 1.0),
                ("ammonia", 0.055, 1.0),
                ("nitrate_fert", 0.020, 1.0),
                ("tillage", 0.0004, 1.0),
                ("diesel", 0.12, 1.0),
            ], direct=2.10,
               note="About 2.9 kg of feed per kg of carcass, mostly maize and "
                    "soy. The direct term carries soy land-use change and the "
                    "crop emissions the nitrogen lines do not reach, and it is "
                    "the largest single item in a chicken - roughly half. Feed "
                    "is where poultry's footprint lives, which is why feed "
                    "conversion ratio is the number the industry optimises."),
            dict(id="housing", name="Housing and manure", inputs=[
                ("process_kwh", 0.35, 1.0)], direct=0.75,
                note="Heated sheds, ventilation and litter management."),
            dict(id="slaughter", name="Slaughter and processing", inputs=[
                ("process_kwh", 0.30, 1.0),
                ("cold_store_origin", 0.25, 1.0)], direct=0.0,
                share=0.78, basis="unstated (assumed)",
                note="Allocation: feathers, offal and meal are co-products. "
                     "The 0.78 is an assumption, not a published factor."),
            dict(id="freight", name="Freight to market", inputs=[],
                 direct=0.0, transport=True, note="Usually frozen."),
            dict(id="distribution", name="Distribution and retail", inputs=[
                ("road", 380, 1.0),
                ("cold_store_kwh", 0.28, 1.0),
                ("retail_kwh", 0.22, 1.0)], direct=0.0, note="Chilled chain."),
            dict(id="consumer", name="Consumer", inputs=[
                ("home_kwh", 0.40, 1.0),
                ("road", 9, 1.0)], direct=0.0, note="Fridge and oven."),
            dict(id="waste", name="End of life", inputs=[], direct=0.0,
                 waste=True, note="Bone and plate waste."),
        ]),

    "coffee": dict(
        name="Coffee, roasted beans", unit="1 kg roasted", category="Beverage", group="Food",
        note="Per kilogram of beans this looks large; per cup it is small, and "
             "what happens in the kitchen afterwards can exceed everything "
             "that happened on the farm.",
        default_origin="CO", default_dest="US-TX",
        waste_frac=0.05, transport_mode="sea",
        stages=[
            dict(id="cultivation", name="Cultivation", inputs=[
                ("field_n2o", 0.038, 1.0),
                ("ammonia", 0.038, 1.0),
                ("nitrate_fert", 0.014, 1.0),
                ("pesticide", 0.0025, 1.0),
                ("diesel", 0.18, 1.0),
            ], direct=0.35,
               note="Shade-grown systems sequester carbon and can come in far "
                    "lower; full-sun intensive systems higher. The direct term "
                    "here is an average land-use figure."),
            dict(id="wet_mill", name="Wet milling", inputs=[
                ("process_kwh", 0.35, 1.0)], direct=0.62,
                share=0.55, basis="unstated (assumed)",
                note="Allocation: pulp and mucilage are separated here and are "
                     "increasingly sold rather than dumped. The direct term is "
                     "methane from wastewater lagoons, which is the whole "
                     "reason wet processing is worse than dry."),
            dict(id="drying", name="Drying and hulling", inputs=[
                ("diesel", 0.08, 1.0)], direct=0.0,
                note="Sun drying where climate allows, mechanical where not."),
            dict(id="freight", name="Freight to roaster", inputs=[],
                 direct=0.0, transport=True,
                 note="Green beans ship dry and unrefrigerated, which makes "
                      "sea freight almost free in emissions terms."),
            dict(id="roasting", name="Roasting", inputs=[
                ("natgas_extraction", 0.075, 1.0)], direct=0.21,
                note="Roasting drives off about 16% of the mass as water, so "
                     "a kilogram of roasted beans started as more."),
            dict(id="packing", name="Packing", inputs=[
                ("plastic_film", 0.035, 1.0),
                ("cardboard", 0.020, 1.0)], direct=0.0,
                note="Valved foil-laminate bags, hard to recycle."),
            dict(id="distribution", name="Distribution and retail", inputs=[
                ("road", 520, 1.0),
                ("retail_kwh", 0.08, 1.0)], direct=0.0,
                note="Ambient, so no refrigeration."),
            dict(id="consumer", name="Brewing", inputs=[
                ("home_kwh", 1.30, 1.0)], direct=0.0,
                note="Heating water, and keeping it hot. A drip machine left "
                     "on a hotplate can use more energy than the roast."),
            dict(id="waste", name="End of life", inputs=[], direct=0.0,
                 waste=True, note="Spent grounds."),
        ]),

    "almond": dict(
        name="Almonds", unit="1 kg as eaten", category="Nut", group="Food",
        note="The interesting number here is not carbon but water, which this "
             "model does not track - a caveat worth stating rather than "
             "burying, since almonds are usually criticised on grounds this "
             "model is silent about.",
        default_origin="US-CA", default_dest="US-NY",
        waste_frac=0.04, transport_mode="rail",
        stages=[
            dict(id="cultivation", name="Orchard", inputs=[
                ("field_n2o", 0.070, 1.0),
                ("ammonia", 0.070, 1.0),
                ("nitrate_fert", 0.025, 1.0),
                ("pesticide", 0.0018, 1.0),
                ("irrigation_kwh", 1.90, 1.0),
                ("diesel", 0.22, 1.0),
            ], direct=-0.35,
               note="The negative direct term is carbon held in orchard "
                    "biomass over a 25-year rotation. It is real, it is "
                    "temporary, and whether it belongs in an annual footprint "
                    "is a live argument. Irrigation pumping is the largest "
                    "single line and scales with the Californian grid."),
            dict(id="hulling", name="Hulling and shelling", inputs=[
                ("process_kwh", 0.28, 1.0)], direct=0.0, share=0.62,
                basis="unstated (assumed)",
                note="Allocation: hulls and shells go to cattle feed and "
                     "bedding, and are genuinely sold. The 0.62 is an "
                     "assumption, not a published factor."),
            dict(id="freight", name="Freight to market", inputs=[],
                 direct=0.0, transport=True, note="Ambient, shelf-stable."),
            dict(id="packing", name="Packing", inputs=[
                ("plastic_film", 0.030, 1.0),
                ("cardboard", 0.025, 1.0)], direct=0.0, note="Bagged."),
            dict(id="distribution", name="Distribution and retail", inputs=[
                ("road", 380, 1.0),
                ("retail_kwh", 0.06, 1.0)], direct=0.0, note="Ambient."),
            dict(id="consumer", name="Consumer", inputs=[], direct=0.0,
                 note="Eaten as they are; no cooking energy."),
            dict(id="waste", name="End of life", inputs=[], direct=0.0,
                 waste=True, note="Minimal."),
        ]),

    "banana": dict(
        name="Banana", unit="1 kg as eaten", category="Fruit", group="Food",
        note="The standard counter-example to food miles: a fruit that travels "
             "eight thousand kilometres and still comes in low, because it "
             "travels by sea and needs no heating.",
        default_origin="PE", default_dest="US-NY",
        waste_frac=0.20, transport_mode="sea",
        stages=[
            dict(id="cultivation", name="Cultivation", inputs=[
                ("field_n2o", 0.011, 1.0),
                ("ammonia", 0.011, 1.0),
                ("nitrate_fert", 0.004, 1.0),
                ("pesticide", 0.0009, 1.0),
                ("diesel", 0.045, 1.0),
            ], direct=0.10,
               note="Plantation systems with heavy fungicide use."),
            dict(id="packing", name="Packing", inputs=[
                ("cardboard", 0.075, 1.0),
                ("plastic_film", 0.006, 1.0)], direct=0.0,
                note="Boxed at origin. Cardboard is a real share of a banana."),
            dict(id="freight", name="Freight to market", inputs=[],
                 direct=0.0, transport=True,
                 note="Reefer containers at 13 degrees."),
            dict(id="ripening", name="Ripening rooms", inputs=[
                ("cold_store_kwh", 0.14, 1.0)], direct=0.0,
                note="Ethylene-controlled ripening on arrival."),
            dict(id="distribution", name="Distribution and retail", inputs=[
                ("road", 300, 1.0),
                ("retail_kwh", 0.07, 1.0)], direct=0.0,
                note="Displayed at ambient temperature."),
            dict(id="consumer", name="Consumer", inputs=[
                ("road", 7, 1.0)], direct=0.0, note="No cooking."),
            dict(id="waste", name="End of life", inputs=[], direct=0.0,
                 waste=True,
                 note="High household waste; bananas are thrown away often."),
        ]),

    "cheese": dict(
        name="Cheese, hard", unit="1 kg as eaten", category="Dairy", group="Food",
        note="Ten kilograms of milk make one of cheese, so every burden in the "
             "milk chain arrives multiplied by ten.",
        default_origin="FR", default_dest="US-NY",
        waste_frac=0.08, transport_mode="sea",
        stages=[
            dict(id="enteric", name="Enteric fermentation", inputs=[],
                 direct=8.4, share=0.85, basis="physical, IDF feed-energy (Flysjo et al. 2011, Sweden)",
                 note="Allocation: a dairy cow yields milk and, at the end, "
                      "meat. 0.85 to milk is the International Dairy "
                      "Federation's physical (feed-energy) split as computed "
                      "for Swedish milk by Flysjo et al. 2011, Int J LCA "
                      "16:420. It is not an economic split: the same paper "
                      "gives 0.88 (Sweden) and 0.92 (New Zealand) by economic "
                      "value, 0.93-0.94 by protein, 0.98 by mass, and "
                      "0.63-0.76 by system expansion. Charging her whole "
                      "methane output to milk would raise this figure by "
                      "nearly a fifth."),
            dict(id="feed", name="Feed production", inputs=[
                ("field_n2o", 0.20, 1.0),
                ("ammonia", 0.20, 1.0),
                ("nitrate_fert", 0.07, 1.0),
                ("tillage", 0.0009, 1.0),
                ("diesel", 0.30, 1.0),
            ], direct=0.0, share=0.85, basis="physical, IDF feed-energy (Flysjo et al. 2011, Sweden)",
               note="Concentrate and forage, carried at the same milk split."),
            dict(id="manure", name="Manure management", inputs=[], direct=2.1,
                 share=0.85, basis="physical, IDF feed-energy (Flysjo et al. 2011, Sweden)", note="Slurry storage."),
            dict(id="dairy", name="Milking and cooling", inputs=[
                ("process_kwh", 0.65, 1.0),
                ("cold_store_origin", 0.40, 1.0)], direct=0.0, share=0.85,
                basis="physical, IDF feed-energy (Flysjo et al. 2011, Sweden)",
                note="On-farm chilling is continuous."),
            dict(id="cheesemaking", name="Cheesemaking", inputs=[
                ("natgas_extraction", 0.12, 1.0),
                ("process_kwh", 0.55, 1.0)], direct=0.0, share=0.90,
                basis="unstated (assumed)",
                note="Allocation: whey leaves as a saleable protein stream, so "
                     "a tenth of the burden goes with it. IDF 2015 recommends "
                     "dry-matter allocation at the dairy plant; the 0.90 here "
                     "is an assumption, not that calculation."),
            dict(id="ageing", name="Ageing", inputs=[
                ("cold_store_origin", 1.10, 1.0)], direct=0.0,
                note="Months in a temperature-controlled store. Time itself "
                     "costs energy, which few footprints show."),
            dict(id="freight", name="Freight to market", inputs=[],
                 direct=0.0, transport=True, note="Chilled."),
            dict(id="distribution", name="Distribution and retail", inputs=[
                ("road", 380, 1.0),
                ("cold_store_kwh", 0.30, 1.0),
                ("retail_kwh", 0.24, 1.0)], direct=0.0, note="Chilled cabinet."),
            dict(id="consumer", name="Consumer", inputs=[
                ("home_kwh", 0.30, 1.0)], direct=0.0, note="Fridge time."),
            dict(id="waste", name="End of life", inputs=[], direct=0.0,
                 waste=True, note="Rind and spoilage."),
        ]),

    "rice": dict(
        name="Rice", unit="1 kg as eaten", category="Staple", group="Food",
        note="The only major staple whose emissions are dominated by methane "
             "from the field itself, because flooding a paddy creates exactly "
             "the anaerobic conditions methanogens want.",
        default_origin="IN", default_dest="US-CA",
        waste_frac=0.10, transport_mode="sea",
        stages=[
            dict(id="paddy", name="Paddy methane", inputs=[], direct=1.85,
                 note="Continuous flooding. Alternate wetting and drying cuts "
                      "this by roughly half and is the single largest "
                      "mitigation available in rice."),
            dict(id="cultivation", name="Cultivation", inputs=[
                ("field_n2o", 0.014, 1.0),
                ("ammonia", 0.014, 1.0),
                ("nitrate_fert", 0.005, 1.0),
                ("irrigation_kwh", 0.42, 1.0),
                ("diesel", 0.10, 1.0),
            ], direct=0.0, note="Nitrogen and pumping."),
            dict(id="milling", name="Milling", inputs=[
                ("process_kwh", 0.09, 1.0)], direct=0.0, share=0.80,
                basis="unstated (assumed)",
                note="Allocation: bran and husk are sold for oil and fuel. The "
                     "0.80 is an assumption, not a published factor."),
            dict(id="freight", name="Freight to market", inputs=[],
                 direct=0.0, transport=True, note="Bagged, ambient."),
            dict(id="packing", name="Packing", inputs=[
                ("plastic_film", 0.012, 1.0)], direct=0.0, note="Bagged."),
            dict(id="distribution", name="Distribution and retail", inputs=[
                ("road", 380, 1.0),
                ("retail_kwh", 0.04, 1.0)], direct=0.0, note="Ambient."),
            dict(id="consumer", name="Cooking", inputs=[
                ("home_kwh", 0.55, 1.0)], direct=0.0,
                note="Twenty minutes of boiling, every time."),
            dict(id="waste", name="End of life", inputs=[], direct=0.0,
                 waste=True, note="Plate waste."),
        ]),

# =========================================================================
# TRANSPORT
# =========================================================================
# The functional unit is 100 kilometres carrying one person. That choice is
# doing a lot of work and it should be said out loud: a car carrying four
# people is four times better per person than the number below, and a bus at
# nine in the evening is far worse than the number below. Occupancy is the
# lever nobody adjusts and it moves these figures more than the drivetrain
# does.
#
# "Produced in" is where the vehicle was built, "consumed in" where it is
# driven. That is not decoration. An electric car is a machine for converting
# a grid into motion, so the same car is a different object in France and in
# India, and the model already knows the difference.

    "car_petrol": dict(
        name="Car, petrol", unit="100 km, one occupant", category="Road",
        group="Transport",
        note="A mid-size petrol car at 7.0 litres per 100 km, one person "
             "aboard, over a 200,000 km life. Manufacture is real but it is "
             "not the story: burning the fuel is about three quarters of it.",
        default_origin="DE", default_dest="US-TX", waste_frac=0.0,
        transport_mode="sea",
        lifetime=dict(label="Vehicle life", unit="km", default=200000,
                      min=80000, max=500000, stages=["manufacture", "delivery"],
                      note="Manufacture is charged to each 100 km as one part in the lifetime. Scrapping a car early does not undo the factory; it re-divides it over fewer kilometres."),
        stages=[
            dict(id="manufacture", name="Building the vehicle",
                 inputs=[("vehicle_glider", 1400.0, 1.0)],
                 direct=0.0, amortise=0.0005,
                 note="1,400 kg of car spread over 200,000 km, so 0.7 kg of "
                      "vehicle is charged to each 100 km. The allocation on "
                      "this edge is one divided by the lifetime, and shortening "
                      "the life is the most effective way to make any car "
                      "worse."),
            dict(id="delivery", name="Delivery to the buyer",
                 inputs=[], direct=0.0, transport=True, amortise=0.0005,
                 freight_kg=1400.0,
                 note="1,400 kg of vehicle moved from the factory to the "
                      "market it is sold into, charged to each 100 km as one "
                      "part in the lifetime. Until 2026-09-04 this field held "
                      "1.4: the mass typed in tonnes into a field the engine "
                      "reads in kilograms, so the delivery leg was a "
                      "thousandth of its size (0.0001 kg instead of 0.097)."),
            dict(id="fuel", name="Fuel, burned",
                 inputs=[("petrol", 7.0, 1.0)], direct=0.0,
                 note="Well-to-wheel, so extraction and refining are in here "
                      "with the combustion."),
            dict(id="upkeep", name="Tyres and servicing",
                 inputs=[("tyres_maint", 0.1, 1.0)], direct=0.0, note=""),
            dict(id="roads", name="The road itself",
                 inputs=[("road_infra", 0.1, 1.0)], direct=0.0,
                 note="Almost every published per-kilometre figure leaves "
                      "this out. It is included here so that the car and the "
                      "train are being asked the same question."),
        ]),

    "car_ev": dict(
        name="Car, battery electric", unit="100 km, one occupant",
        category="Road", group="Transport",
        note="The same car with a 60 kWh battery, drawing 18 kWh per 100 km "
             "from the grid where it is driven. Change the destination and "
             "watch this one move more than anything else in the catalogue.",
        default_origin="CN", default_dest="US-TX", waste_frac=0.0,
        transport_mode="sea",
        lifetime=dict(label="Vehicle life", unit="km", default=200000,
                      min=80000, max=500000, stages=["manufacture", "delivery"],
                      note="An electric car carries more manufacturing burden and less fuel burden, so its answer moves further with lifetime than a petrol car's does."),
        stages=[
            dict(id="manufacture", name="Building the vehicle",
                 inputs=[("vehicle_glider", 1500.0, 1.0),
                         ("li_battery", 60.0, 1.0)],
                 direct=0.0, amortise=0.0005,
                 note="The battery is built where the car is built, so its "
                      "carbon belongs to the producing country's grid. This "
                      "is why a battery made in Sichuan and a battery made in "
                      "Shanxi are not the same battery."),
            dict(id="delivery", name="Delivery to the buyer",
                 inputs=[], direct=0.0, transport=True, amortise=0.0005,
                 freight_kg=1500.0,
                 note="1,500 kg of vehicle moved to market, charged to each "
                      "100 km as one part in the lifetime. Carried the same "
                      "tonnes-for-kilograms slip as the petrol car until "
                      "2026-09-04 (0.0002 kg instead of 0.148)."),
            dict(id="charging", name="Charging",
                 inputs=[("home_kwh", 18.0, 1.0)], direct=0.0,
                 note="18 kWh at the wall, including charging losses, "
                      "charged at the grid where the car is driven."),
            dict(id="upkeep", name="Tyres and servicing",
                 inputs=[("tyres_maint", 0.1, 1.0)], direct=0.0,
                 note="Fewer fluids, heavier car, so tyre wear is worse and "
                      "servicing is lighter. They roughly cancel."),
            dict(id="roads", name="The road itself",
                 inputs=[("road_infra", 0.1, 1.0)], direct=0.0, note=""),
        ]),

    "bus_city": dict(
        name="Bus, city diesel", unit="100 passenger-km", category="Road",
        group="Transport",
        note="A diesel city bus at an average twelve passengers. The vehicle "
             "burden per person is small because it is shared; the fuel "
             "burden per person is small for the same reason.",
        default_origin="DE", default_dest="US-TX", waste_frac=0.0,
        transport_mode="sea",
        lifetime=dict(label="Vehicle life", unit="passenger-km", default=15873016,
                      min=4000000, max=40000000, stages=["manufacture"],
                      note="Bus-kilometres multiplied by the average number of people aboard."),
        stages=[
            dict(id="manufacture", name="Building the vehicle",
                 inputs=[("vehicle_glider", 12000.0, 1.0)],
                 direct=0.0, amortise=0.0000063,
                 note="12 tonnes of bus spread over its lifetime "
                      "passenger-kilometres, which is what makes shared "
                      "vehicles cheap per person however heavy they are. The "
                      "amortisation implies 15.9 million passenger-km, which "
                      "is 1.3 million bus-km at the twelve aboard the fuel "
                      "line assumes; the figure is assumed, not measured."),
            dict(id="fuel", name="Fuel, burned",
                 inputs=[("diesel", 2.9, 1.0)], direct=0.0,
                 note="35 litres per 100 km divided among twelve people."),
            dict(id="upkeep", name="Tyres and servicing",
                 inputs=[("tyres_maint", 0.02, 1.0)], direct=0.0, note=""),
            dict(id="roads", name="The road itself",
                 inputs=[("road_infra", 0.008, 1.0)], direct=0.0, note=""),
        ]),

    "rail_intercity": dict(
        name="Train, electric intercity", unit="100 passenger-km",
        category="Rail", group="Transport",
        note="Electric intercity rail at typical European occupancy. Like the "
             "electric car, this is a grid in disguise, and its footprint is "
             "mostly a statement about the country it runs through.",
        default_origin="FR", default_dest="FR", waste_frac=0.0,
        transport_mode="rail",
        lifetime=dict(label="Trainset life", unit="passenger-km", default=1250000000,
                      min=300000000, max=4000000000, stages=["manufacture"],
                      note="A trainset runs for decades and carries hundreds at a time, which is why its manufacturing share per passenger-kilometre is small."),
        stages=[
            dict(id="manufacture", name="Building the train",
                 inputs=[("vehicle_glider", 400000.0, 1.0)],
                 direct=0.0, amortise=0.00000008,
                 note="400 tonnes of train over 40 years, spread across every "
                      "passenger it will ever carry."),
            dict(id="traction", name="Traction power",
                 inputs=[("home_kwh", 4.4, 1.0)], direct=0.0,
                 note="4.4 kWh per 100 passenger-km at the pantograph, "
                      "including distribution losses."),
            dict(id="track", name="Track and signalling",
                 inputs=[("road_infra", 0.05, 1.0)], direct=0.0,
                 note="Rail infrastructure is heavier per kilometre than road "
                      "and carries far more traffic, so per passenger it is "
                      "smaller. Included for the same reason it is included "
                      "for the car: so the comparison is honest."),
        ]),

    "flight_short": dict(
        name="Flight, short haul", unit="100 passenger-km", category="Air",
        group="Transport",
        note="Under 1,500 km. Take-off and climb are a fixed cost paid over a "
             "short distance, so short flights are worse per kilometre than "
             "long ones - and they are the ones most easily replaced by a "
             "train.",
        default_origin="FR", default_dest="IT", waste_frac=0.0,
        transport_mode="air",
        lifetime=dict(label="Airframe life", unit="passenger-km", default=500000000,
                      min=150000000, max=2000000000, stages=["manufacture"],
                      note="Seats multiplied by load factor multiplied by lifetime distance. A narrowbody flies about 25 years."),
        stages=[
            dict(id="manufacture", name="Building the aircraft",
                 inputs=[("aluminium", 42000.0, 1.0)],
                 direct=0.0, amortise=0.0000002,
                 note="Airframes fly for decades and carry a great many "
                      "people, so manufacture is a rounding error against the "
                      "fuel. This is the opposite of the car."),
            dict(id="fuel", name="Fuel, burned",
                 inputs=[("jet_fuel", 3.4, 1.0)], direct=0.0,
                 note="3.4 kg of kerosene per 100 passenger-km, at typical "
                      "load factors."),
            dict(id="nonco2", name="Contrails and nitrogen oxides",
                 inputs=[("aviation_nonco2", 3.4, 1.0)], direct=0.0,
                 note="Not carbon dioxide, and not optional. Leaving this out "
                      "halves aviation, which is why so many airline figures "
                      "leave it out."),
            dict(id="airport", name="Airport operations",
                 inputs=[("retail_kwh", 0.35, 1.0)], direct=0.0, note=""),
        ]),

    "flight_long": dict(
        name="Flight, long haul", unit="100 passenger-km", category="Air",
        group="Transport",
        note="Over 4,000 km. More efficient per kilometre than a short hop, "
             "and far worse per journey, because the journey is ten times "
             "longer. Per-kilometre efficiency is the wrong unit for a "
             "decision nobody makes per kilometre.",
        default_origin="US-NY", default_dest="CN", waste_frac=0.0,
        transport_mode="air",
        lifetime=dict(label="Airframe life", unit="passenger-km", default=1111111111,
                      min=300000000, max=4000000000, stages=["manufacture"],
                      note="Seats multiplied by load factor multiplied by lifetime distance. This is your share of building the aircraft, divided the same way the fuel is."),
        stages=[
            dict(id="manufacture", name="Building the aircraft",
                 inputs=[("aluminium", 180000.0, 1.0)],
                 direct=0.0, amortise=0.00000009, note=""),
            dict(id="fuel", name="Fuel, burned",
                 inputs=[("jet_fuel", 2.5, 1.0)], direct=0.0,
                 note="2.5 kg per 100 passenger-km, in economy. A business "
                      "seat occupies about three times the floor area and "
                      "carries about three times the fuel."),
            dict(id="nonco2", name="Contrails and nitrogen oxides",
                 inputs=[("aviation_nonco2", 2.5, 1.0)], direct=0.0,
                 note="Worse at cruise altitude, where contrails persist."),
            dict(id="airport", name="Airport operations",
                 inputs=[("retail_kwh", 0.12, 1.0)], direct=0.0, note=""),
        ]),

# =========================================================================
# CLOTHING
# =========================================================================
# The functional unit is one garment through its whole life, including being
# washed. That last part is the reason clothing is here: for a cotton t-shirt
# the laundry is larger than the cotton, and it is charged at the grid where
# the wearer lives rather than where the shirt was sewn. Almost no published
# garment footprint includes it, and the ones that do stop looking like
# arguments about fibre.

    "tshirt_cotton": dict(
        name="T-shirt, cotton", unit="1 shirt, whole life", category="Cotton",
        group="Clothing",
        note="A 180 g cotton t-shirt, worn and washed weekly for three years. "
             "Published figures run from 2 to 7 kg CO2e and the spread is "
             "almost entirely about whether the washing was counted.",
        default_origin="IN", default_dest="US-TX", waste_frac=0.0,
        transport_mode="sea",
        stages=[
            dict(id="fibre", name="Growing the cotton",
                 inputs=[("cotton_fibre", 0.26, 1.0)], direct=0.0,
                 note="260 g of fibre for a 180 g shirt; the rest is lost in "
                      "spinning and cutting."),
            dict(id="fabric", name="Spinning and knitting",
                 inputs=[("yarn_fabric", 0.22, 1.0)], direct=0.0, note=""),
            dict(id="finish", name="Dyeing and finishing",
                 inputs=[("dyeing", 0.20, 1.0)], direct=0.0, note=""),
            dict(id="make", name="Cutting and sewing",
                 inputs=[("cut_sew", 1.0, 1.0)], direct=0.0, note=""),
            dict(id="freight", name="Freight to market",
                 inputs=[], direct=0.0, transport=True, freight_kg=0.22,
                 note="220 g including its share of the carton."),
            dict(id="retail", name="Retail",
                 inputs=[("retail_kwh", 0.9, 1.0)], direct=0.0,
                 note="Floor space, lighting and heating, per garment sold."),
            dict(id="care", name="Washing and drying",
                 inputs=[("laundry_kwh", 9.5, 1.0)], direct=0.0,
                 note="150 washes over three years. A machine load costs about "
                      "0.6 kWh to wash and 2.5 to tumble dry and holds "
                      "thirty-odd garments, so one shirt's share of a "
                      "cycle is small and the number of cycles is what "
                      "makes it large. This is usually "
                      "the largest single item and it is the one entirely "
                      "under the wearer's control."),
            dict(id="waste", name="Disposal",
                 inputs=[("landfill", 0.18, 1.0)], direct=0.0, waste=True,
                 note=""),
        ]),

    "tshirt_poly": dict(
        name="T-shirt, polyester", unit="1 shirt, whole life",
        category="Synthetic", group="Clothing",
        note="The same shirt in polyester. Worse at the fibre, better in the "
             "laundry - it washes cool and dries without a machine - and the "
             "two effects are close enough that the answer depends on how the "
             "wearer behaves rather than on what the shirt is made of.",
        default_origin="CN", default_dest="US-TX", waste_frac=0.0,
        transport_mode="sea",
        stages=[
            dict(id="fibre", name="Making the fibre",
                 inputs=[("polyester_fibre", 0.20, 1.0)], direct=0.0,
                 note=""),
            dict(id="fabric", name="Spinning and knitting",
                 inputs=[("yarn_fabric", 0.19, 1.0)], direct=0.0, note=""),
            dict(id="finish", name="Dyeing and finishing",
                 inputs=[("dyeing", 0.18, 1.0)], direct=0.0,
                 note="Polyester takes disperse dyes at higher temperature, "
                      "so the wet processing is slightly worse than cotton's."),
            dict(id="make", name="Cutting and sewing",
                 inputs=[("cut_sew", 1.0, 1.0)], direct=0.0, note=""),
            dict(id="freight", name="Freight to market",
                 inputs=[], direct=0.0, transport=True, freight_kg=0.20,
                 note=""),
            dict(id="retail", name="Retail",
                 inputs=[("retail_kwh", 0.9, 1.0)], direct=0.0, note=""),
            dict(id="care", name="Washing and drying",
                 inputs=[("laundry_kwh", 4.5, 1.0)], direct=0.0,
                 note="Washed cooler and rarely tumble dried, which is where "
                      "synthetics win back what they lost at the fibre."),
            dict(id="waste", name="Disposal",
                 inputs=[("landfill", 0.15, 1.0)], direct=0.0, waste=True,
                 note=""),
        ]),

    "jeans": dict(
        name="Jeans, denim", unit="1 pair, whole life", category="Cotton",
        group="Clothing",
        note="800 g of denim, worn for four years. The published anchor is "
             "Levi Strauss's own life-cycle assessment of a pair of 501s, "
             "which came to 33.4 kg CO2e over the garment's life and put more "
             "than a third of it in the consumer's laundry basket.",
        default_origin="CN", default_dest="US-CA", waste_frac=0.0,
        transport_mode="sea",
        stages=[
            dict(id="fibre", name="Growing the cotton",
                 inputs=[("cotton_fibre", 1.05, 1.0)], direct=0.0, note=""),
            dict(id="fabric", name="Spinning and weaving",
                 inputs=[("yarn_fabric", 0.95, 1.0)], direct=0.0,
                 note="Denim is woven rather than knitted, which is heavier "
                      "work."),
            dict(id="finish", name="Dyeing and finishing",
                 inputs=[("dyeing", 0.90, 1.0)], direct=0.0,
                 note="Indigo dyeing plus whatever distressing the style "
                      "calls for. Stonewashing and laser finishing are not "
                      "free and vary enormously between products."),
            dict(id="make", name="Cutting and sewing",
                 inputs=[("cut_sew", 2.4, 1.0)], direct=0.0,
                 note="More pieces, more seams, heavier machines."),
            dict(id="freight", name="Freight to market",
                 inputs=[], direct=0.0, transport=True, freight_kg=0.85,
                 note=""),
            dict(id="retail", name="Retail",
                 inputs=[("retail_kwh", 1.6, 1.0)], direct=0.0, note=""),
            dict(id="care", name="Washing and drying",
                 inputs=[("laundry_kwh", 14.0, 1.0)], direct=0.0,
                 note="Washed after every ten wears over four years, mostly "
                      "tumble dried. Washing jeans less is the single largest "
                      "lever a wearer has over this number, and it is the one "
                      "the manufacturer's own study recommends."),
            dict(id="waste", name="Disposal",
                 inputs=[("landfill", 0.80, 1.0)], direct=0.0, waste=True,
                 note=""),
        ]),

    "sneakers": dict(
        name="Trainers, synthetic", unit="1 pair, whole life",
        category="Footwear", group="Clothing",
        note="A running shoe is about sixty separate pieces in a dozen "
             "materials, and the assembly is so fragmented that manufacture, "
             "not materials, is most of the footprint. The MIT teardown study "
             "put a pair at roughly 14 kg CO2e.",
        default_origin="VN", default_dest="US-NY", waste_frac=0.0,
        transport_mode="sea",
        stages=[
            dict(id="materials", name="Materials",
                 inputs=[("polyester_fibre", 0.22, 1.0),
                         ("rubber_sole", 0.42, 1.0),
                         ("plastic_film", 0.09, 1.0)],
                 direct=0.0, note=""),
            dict(id="make", name="Moulding and assembly",
                 inputs=[("cut_sew", 5.5, 1.0), ("process_kwh", 8.0, 1.0)],
                 direct=0.0,
                 note="Sixty-odd components, each moulded or cut and then "
                      "joined by hand. This is where a shoe differs from a "
                      "shirt: the making costs more than the stuff."),
            dict(id="freight", name="Freight to market",
                 inputs=[], direct=0.0, transport=True, freight_kg=1.6,
                 note="Shoes are bulky, so they are usually charged by volume "
                      "rather than by weight; this uses weight and therefore "
                      "understates the freight a little."),
            dict(id="retail", name="Retail",
                 inputs=[("retail_kwh", 2.2, 1.0)], direct=0.0, note=""),
            dict(id="waste", name="Disposal",
                 inputs=[("landfill", 0.75, 1.0)], direct=0.0, waste=True,
                 note="Almost nothing about a trainer is separable, so almost "
                      "none of it is recycled."),
        ]),

    "leather_shoes": dict(
        name="Shoes, leather", unit="1 pair, whole life", category="Footwear",
        group="Clothing",
        note="The interesting one. A hide is a co-product of a beef animal, "
             "so how much of that animal's methane belongs to a shoe is a "
             "choice, not a measurement - and it is the choice that decides "
             "the answer. Set by economic value here, which is the smaller "
             "of the defensible options.",
        default_origin="IT", default_dest="US-NY", waste_frac=0.0,
        transport_mode="sea",
        stages=[
            dict(id="hide", name="The hide, from a beef animal",
                 inputs=[("leather", 0.9, 1.0)], direct=8.4, share=0.022,
                 basis="economic (assumed; cf. Lunesu et al. 2025, 2.7%)",
                 note="The direct figure is the animal: enteric methane, "
                      "feed and land, for the share of a carcass that becomes "
                      "one pair of shoes. The 2.2% allocation is by economic "
                      "value, following ISO 14044's preference order; Lunesu "
                      "et al. 2025 (Animals 15:3546) put the economic mean at "
                      "2.7% and the physical, live-weight mean at 5.9% (range "
                      "4.2-6.9%). The hide stage is about 9% of this shoe, so "
                      "moving from the economic to the physical mean raises "
                      "the pair by about a sixth, from 3.7 to 4.2 kg. Until "
                      "2026-09-04 this note said the shoe would triple at 7%; "
                      "that scaled the whole shoe by the ratio of the two "
                      "factors, as if every gram of it were hide."),
            dict(id="make", name="Lasting and assembly",
                 inputs=[("cut_sew", 4.0, 1.0), ("rubber_sole", 0.25, 1.0)],
                 direct=0.0, note=""),
            dict(id="freight", name="Freight to market",
                 inputs=[], direct=0.0, transport=True, freight_kg=1.2,
                 note=""),
            dict(id="retail", name="Retail",
                 inputs=[("retail_kwh", 2.2, 1.0)], direct=0.0, note=""),
            dict(id="waste", name="Disposal",
                 inputs=[("landfill", 0.60, 1.0)], direct=0.0, waste=True,
                 note="Leather shoes are resoled and worn for years, which is "
                      "the one thing that reliably beats every material "
                      "choice: use it longer."),
        ]),
}
