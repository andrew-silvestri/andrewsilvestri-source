"""Extract Lost City rows (pH, T, H2, CH4, Mg) from MARHYS DB 3.0.
usage: python -I marhys_lostcity.py <xlsx> <out.csv>"""
import sys, csv, openpyxl
sys.stdout.reconfigure(encoding="utf-8")
xlsx, out = sys.argv[1], sys.argv[2]
ws = openpyxl.load_workbook(xlsx, read_only=True).worksheets[0]
rows = list(ws.iter_rows(min_row=12, values_only=True))
hdr, units, data = rows[0], rows[1], rows[3:]
name = {j: (h or '').strip() for j, h in enumerate(hdr)}
unit = {j: (u or '') for j, u in enumerate(units)}
want_names = ['Sample-ID','Vent-ID','Vent site (small scale)','Vent area (large scale)','Date of sample collection',
  'Author (primary)','Year of publication (primary)','Source ID (primary)','Sample type','Depth',
  'Tsample','Tmax','Tcalc','T','pHmeas','pHmin','pHcalc','pH','Mg','H2','CH4']
cols = []
for w in want_names:
    js = [j for j, n in name.items() if n == w]
    if not js: print('MISSING column', w); continue
    cols.append(js[0])
print('gas/carbon headers:', [(j, name[j], unit[j]) for j in range(105, 135) if name.get(j)])
lc = [r for r in data if r and any('lost city' in str(r[j] or '').lower() for j in (1,2,3,4,5))]
print('Lost City rows:', len(lc), 'of', len(data))
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow([f"{name[j]} [{unit[j]}]" if unit[j] else name[j] for j in cols])
    for r in lc:
        w.writerow(['' if r[j] is None else r[j] for j in cols])
def nums(colname):
    j = [k for k, n in name.items() if n == colname][0]
    v = []
    for r in lc:
        try: v.append(float(r[j]))
        except (TypeError, ValueError): pass
    return v
for c in ['pHmeas','pHcalc','pH','Tmax','Tsample','T','H2','CH4','Mg']:
    v = nums(c)
    print(c, unit[[k for k,n in name.items() if n==c][0]], 'n=%d' % len(v), ('min=%g max=%g' % (min(v), max(v))) if v else '')
