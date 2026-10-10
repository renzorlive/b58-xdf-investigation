"""Cross-version consensus placement of calibration tables into a user binary.

For each reference XDF + its stock dump we locate each table's breakpoint axes by
exact content in the user binary. A table is accepted only when >= MIN_VOTES
independent reference XDFs agree on the *user-space* address of its data block.
Nothing is accepted on plausibility alone.
"""
import xdfread
import align
import os
import glob
import json
from collections import defaultdict

MIN_VOTES = 2


def anchor_file(xdf_path, ref_path, user, lo, hi):
    ref = open(ref_path, 'rb').read()
    base, tabs = xdfread.parse(xdf_path)
    cache = {}

    def find(ax):
        if ax is None or ax.address is None or ax.esize_bits != 16:
            return []
        k = (ax.address, ax.rowcount, ax.colcount, ax.major_stride, ax.minor_stride, ax.indexcount)
        if k not in cache:
            v = align.axis_values(ax, ref)
            h = align.find_seq(v, user, lo, hi) if v else []
            # unique match only: a breakpoint array shared by many tables is
            # still unique as an *address*, but ambiguous only if repeated verbatim
            cache[k] = h[:1] if len(h) == 1 else []
        return cache[k]

    out = []
    for tb in tabs:
        if not tb.z or tb.z.address is None or not tb.desc:
            continue
        if 'autogen' in (tb.title or ''):
            continue
        hx = find(tb.x)
        hy = find(tb.y)
        if not hx or not hy:
            continue
        ux, uy = hx[0], hy[0]
        # axes must be ordered as in the reference, else the match is coincidental
        if tb.x.address < tb.y.address and ux >= uy:
            continue
        if tb.x.address > tb.y.address and ux <= uy:
            continue
        delta = tb.z.address - tb.x.address
        uz = ux + delta
        if uz < 0 or uz + tb.z.byte_span() > len(user):
            continue
        out.append(dict(desc=tb.desc, title=tb.title, ux=ux, uy=uy, uz=uz,
                        rows=tb.z.rowcount or tb.z.indexcount,
                        cols=tb.z.colcount or tb.z.indexcount,
                        esize=tb.z.esize_bits, mn=tb.z.mn, mx=tb.z.mx,
                        cat=tb.categories, src=os.path.basename(xdf_path)))
    return out


def run(bin_path, pairs, lo, hi):
    user = open(bin_path, 'rb').read()
    votes = defaultdict(list)
    for x, r in pairs:
        found = anchor_file(x, r, user, lo, hi)
        print(f'  {os.path.basename(x):24s} anchored {len(found):4d}')
        for f in found:
            votes[f['desc']].append(f)
    return votes, user


if __name__ == '__main__':
    import sys
    root = 'ref/BMW-XDFs-master/B58gen1'
    pairs = []
    for x in sorted(glob.glob(root + '/*.xdf')):
        r = x.replace('.xdf', '_original.bin')
        if os.path.exists(r):
            pairs.append((x, r))
    votes, user = run('10SW002828_iRom_ori', pairs, 0x6C0000, 0x740000)

    consensus = {}
    for desc, fl in votes.items():
        groups = defaultdict(list)
        for f in fl:
            groups[(f['uz'], f['ux'], f['uy'], f['rows'], f['cols'], f['esize'])].append(f)
        for k, g in groups.items():
            if len({f['src'] for f in g}) >= MIN_VOTES:
                consensus[desc] = dict(zip(('uz', 'ux', 'uy', 'rows', 'cols', 'esize'), k),
                                       votes=len({f['src'] for f in g}),
                                       title=g[0]['title'], mn=g[0]['mn'], mx=g[0]['mx'],
                                       cat=g[0]['cat'], srcs=sorted({f['src'] for f in g}))
                break
    print(f'\nconsensus tables (>= {MIN_VOTES} independent votes): {len(consensus)}')
    json.dump({k: {**v, 'srcs': v['srcs']} for k, v in consensus.items()},
              open('out/consensus.json', 'w'), indent=1)