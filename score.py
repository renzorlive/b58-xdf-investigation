import xdfread, glob, os, sys

u = open('10SW002828_iRom_ori', 'rb').read()
CAL = (0x6C0000, 0x740000)
FFGAP = [(0x600000, 0x6C0000), (0x740000, 0x7C0000)]

paths = []
for root in sys.argv[1:]:
    paths += glob.glob(os.path.join(root, '**/*.xdf'), recursive=True)

res = []
for f in paths:
    try:
        base, tabs = xdfread.parse(f)
    except Exception:
        continue
    tot = inc = 0
    cells = inr = 0
    btot = bmono = 0
    for tb in tabs:
        z = tb.z
        if z is None or z.address is None:
            continue
        n = z.byte_span()
        if z.address < 0 or z.address + n > len(u):
            continue
        tot += n
        if not any(g0 <= z.address < g1 for g0, g1 in FFGAP):
            inc += n
        if z.mn is not None and z.mx is not None:
            try:
                mn, mx = float(z.mn), float(z.mx)
            except ValueError:
                continue
            if mn < mx:
                v = xdfread.read_axis(z, u)
                if v:
                    for q in [z.eq(x) for x in v]:
                        cells += 1
                        if mn - 1e-9 <= q <= mx + 1e-9:
                            inr += 1
    for tb in tabs:
        for ax in (tb.x, tb.y):
            v = xdfread.read_axis(ax, u)
            if v and len(v) > 2:
                btot += 1
                if all(v[i] <= v[i + 1] for i in range(len(v) - 1)):
                    bmono += 1
    if tot == 0:
        continue
    res.append((inc / tot, cells and inr / cells or 0, btot and bmono / btot or 0, len(tabs), f))

res.sort(key=lambda r: (-r[0], -r[1]))
print(f'{"inCal":>6} {"inRange":>8} {"bpMono":>7} {"tabs":>5}  file')
for r in res[:30]:
    print(f'{r[0]*100:6.1f} {r[1]*100:8.1f} {r[2]*100:7.1f} {r[3]:5d}  {os.path.relpath(r[4])}')
print('...')
print(f'total parsed: {len(res)}')