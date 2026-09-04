/* The life-cycle engine: a direct port of lca.py, kept in the page so that
   changing the route recomputes rather than looking up a precomputed answer.
   Precomputing would limit the tool to the combinations somebody thought of
   in advance, which is exactly the failure mode the model exists to avoid.

   This file is verified against the Python line by line in test_lca.py; if
   you edit one, edit both, and run the parity check. */
const $ = id => document.getElementById(id);
const CUT = D.cutoff, MAXD = D.max_depth;

/* ---------------------------------------------------------------- engine --
   A direct port of lca.py. Kept in the page so that changing the route
   recomputes rather than looking up a precomputed answer, which would limit
   the tool to the combinations someone thought of in advance. */
const R = 6371.0;
function greatCircle(a, b){
  const r1 = D.regions[a], r2 = D.regions[b], rad = Math.PI/180;
  const p1 = r1.lat*rad, p2 = r2.lat*rad;
  const dl = (r2.lon-r1.lon)*rad, dp = p2-p1;
  const h = Math.sin(dp/2)**2 + Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)**2;
  return 2*R*Math.asin(Math.min(1, Math.sqrt(h)));
}
const DETOUR = {sea:1.35, road:1.25, rail:1.20, air:1.05};

function model(item, origin, dest, mode, life){
  const p = D.products[item];
  const gridO = D.regions[origin].grid, gridD = D.regions[dest].grid;
  const km = greatCircle(origin, dest) * DETOUR[mode];
  let cut = 0;

  /* Capital goods are charged to one unit of use as one part in a lifetime:
     a car's factory divided by the kilometres it will cover, an airframe by
     the passenger-kilometres it will fly. Those lifetimes are assumptions,
     not measurements, so they are exposed rather than buried in a constant.
     Scaling by default/chosen leaves every published figure unchanged when
     the control is left where it started. */
  const lt = p.lifetime;
  const lifeScale = (lt && life && life > 0) ? (lt.default / life) : 1;
  const scalesWithLife = id => !!(lt && lt.stages.indexOf(id) >= 0);

  const factor = pid => {
    const pr = D.processes[pid];
    if (pr.grid_scaled) return pr.consumer_grid ? gridD : gridO;
    return pr.direct;
  };

  function expand(pid, amount, alloc, depth, hint){
    if (D.transport[pid]){
      const tm = D.transport[pid];
      const e = tm.ef * (amount/1000) * alloc;
      return {id:pid, name:tm.name, unit:"km", amount, alloc, direct:e,
              total:e, children:[], quality:"A",
              note:`${Math.round(amount).toLocaleString()} km at ${tm.ef} kg `
                 + `CO2e per tonne-kilometre. ${tm.note}`};
    }
    const pr = D.processes[pid];
    const direct = factor(pid) * amount * alloc;
    const node = {id:pid, name:pr.name, unit:pr.unit, amount, alloc, direct,
                  note:pr.note||"", quality:pr.quality||"B", children:[]};
    if (depth < MAXD){
      for (const [cid, camt, calloc] of (pr.inputs||[])){
        const ca = alloc*calloc;
        const rough = D.transport[cid]
          ? Math.abs(D.transport[cid].ef*camt/1000*amount*ca)
          : Math.abs(factor(cid)*camt*amount*ca);
        if (hint && rough < CUT*hint){ cut += rough; continue; }
        node.children.push(expand(cid, camt*amount, ca, depth+1, hint));
      }
    }
    node.total = direct + node.children.reduce((s,c)=>s+c.total, 0);
    return node;
  }

  function build(hint){
    cut = 0;
    const w = p.waste_frac, over = 1/(1-w);
    const spine = p.stages.map(st => {
      /* Three multipliers, three meanings (see processes.py): a co-product
         share, a capital-good amortisation, and the mass shipped on a
         freight leg. Share and amortisation reach every node in the stage;
         the mass reaches only the freight node. */
      const share = st.share != null ? st.share : 1.0;
      let amort = st.amortise != null ? st.amortise : 1.0;
      if (scalesWithLife(st.id)) amort *= lifeScale;
      const alloc = share * amort;
      const scale = st.waste ? 1.0 : over;
      const kids = [];
      if (st.transport){
        const tm = D.transport[mode];
        const kg = st.freight_kg != null ? st.freight_kg : 1.0;
        const e = tm.ef*(km/1000)*alloc*scale*kg;
        kids.push({id:"freight_"+mode, name:tm.name, unit:"tonne-km",
                   amount:km/1000*kg*scale, alloc:alloc, direct:e, total:e,
                   children:[], quality:"A",
                   note:`${Math.round(km).toLocaleString()} km by ${tm.name} `
                      + `at ${tm.ef} kg CO2e per tonne-kilometre. ${tm.note}`});
      }
      for (const [cid, camt, calloc] of st.inputs)
        kids.push(expand(cid, camt*scale, alloc*calloc, 1, hint));
      let direct = (st.direct||0)*alloc*scale;
      let note = st.note||"";
      if (st.waste){
        direct = D.processes.landfill.direct*(over-1)*alloc;
        /* The unit is the product's own, not "kilogram eaten": this engine
           carries cars and flights as well as food. */
        note += ` Losses run about ${Math.round(w*100)}% for this product, so `
             + `${over.toFixed(2)} units leave the line for every one that `
             + `reaches the buyer, and every stage above is scaled `
             + `accordingly.`;
      }
      const total = direct + kids.reduce((s,c)=>s+c.total, 0);
      return {id:st.id, name:st.name, alloc, direct, note, children:kids,
              total, land_use:!!st.land_use, basis:st.basis||""};
    });
    return {spine, total:spine.reduce((s,x)=>s+x.total,0), km, cut,
            over, waste:w};
  }
  const first = build(0);            // learn the scale
  return build(first.total);         // then apply a proportional cutoff
}
