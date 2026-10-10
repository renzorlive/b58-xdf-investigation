"""Per-table delta search by byte identity against a reference stock dump.

For every table in a reference XDF we search the calibration-shift window for the
delta that maximises byte agreement with the user's stock BIN. A table that is
genuinely transferable to this ECU will hit 100% at a sharp, well-supported delta;
one that is not will score low everywhere.
"""
import sys
import json
import xdfread

WINDOW = (0x3F800, 0x41800, 2)


def popcount_match(a, b):
    if len(a) != len(b):
        return 0
    return len(a) - (int.from_bytes(a, 'big') ^ int.from_bytes(b, 'big')).bit_count()


def search(xdf_path, ref_path, bin_path, window=WINDOW, min_len=4):
    base, tabs = xdfread.parse(xdf_path)
    ref = open(ref_path, 'rb').read()
    user = open(bin_path, 'rb').read()
    lo, hi, step = window
    deltas = list(range(lo, hi + 1, step))

    out = []
    for tb in tabs:
        if not tb.z or not tb.z.address or 'autogen' in (tb.title or ''):
            continue
        n = tb.z.byte_span()
        if n < min_len or tb.z.address + n > len(ref):
            continue
        A = ref[tb.z.address:tb.z.address + n]
        best = (0, None, 0)
        scores = []
        for d in deltas:
            s = tb.z.address + d
            if s < 0 or s + n > len(user):
                continue
            c = popcount_match(A, user[s:s + n])
            scores.append((c, d))
            if c > best[0]:
                best = (c, d, len(scores))
        if best[1] is None:
            continue
        pct = best[0] / n
        # how many other deltas achieve the same score? (uniqueness)
        ties = [d for c, d in scores if c == best[0]]
        out.append(dict(desc=tb.desc, title=tb.title, ref_addr=tb.z.address,
                         delta=hex(best[1]), user_addr=hex(tb.z.address + best[1]),
                         rows=tb.z.rowcount, cols=tb.z.colcount, esize=tb.z.esize_bits,
                         size=n, match=round(pct, 4), n_ties=len(ties),
                         cat=tb.categories))
    return out


if __name__ == '__main__':
    res = search(*sys.argv[1:4])
    res.sort(key=lambda r: -r['match'])
    import collections
    b = collections.Counter()
    for r in res:
        m = r['match']
        b['100%' if m == 1.0 else '>90%' if m > 0.9 else '>50%' if m > 0.5 else '<50%'] += 1
    print('tables searched:', len(res), dict(b))
    print()
    for r in res[:25]:
        print('  %6.1f%% %-28s 0x%06X +%-8s -> 0x%06X %2dx%-3d esz=%-2d ties=%d'
              % (r['match'] * 100, (r['desc'] or '')[:28], r['ref_addr'], r['delta'],
                 int(r['user_addr'],16), r['rows'], r['cols'], r['esize'], r['n_ties']))
    json.dump(res, open(sys.argv[4] if len(sys.argv) > 4 else 'out/sp15_search.json', 'w'), indent=1)