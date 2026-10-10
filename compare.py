"""Compare candidate reference XDFs as the base for the verified map set."""
import os
import glob
import re
import verify

ORI = '10SW002828_iRom_ori'

import os as _os
def _mod():
    for c in ('10SW002828_iRom_stage2',_mod()):
        if _os.path.exists(c):
            return c
    raise SystemExit('tuned file not found')
MOD = _mod()
ROOT = 'ref/BMW-XDFs-master/B58gen1'


def bin_ids(path):
    d = open(path, 'rb').read()
    ep = set(x.decode() for x in re.findall(rb'#EPST:([A-Z0-9]{9,10})', d))
    sp = set(x.decode() for x in re.findall(rb'B58-SP(\d+)', d))
    return ','.join(ep) or '-', ','.join(sp) or '-'


def audit(xdf, ref, o, m):
    acc, tabs, med = verify.run(xdf, ref, ORI, 0x6C0000, 0x740000)
    cells = set()
    axes = set()
    overlap = 0
    for i, tb, off, how, sc in acc:
        z = tb.z
        st = z.address + off
        n = z.byte_span()
        s = set(range(st, st + n))
        overlap += len(s & cells)
        cells |= s
        for ax in (tb.x, tb.y):
            if ax and ax.address is not None:
                a = ax.address + off
                axes |= set(range(a, a + max(2, ax.indexcount or 2) * (ax.esize_bits // 8)))
    diff = set(k for k in range(len(o)) if o[k] != m[k])
    return acc, len(cells & axes), overlap, len(diff & cells), len(diff & axes)


if __name__ == '__main__':
    o = open(ORI, 'rb').read()
    m = open(MOD, 'rb').read()
    print('user bin:  EPST=%s  SP=%s\n' % bin_ids(ORI))
    print('%-22s %-11s %-4s %6s %8s %8s %8s %8s' %
          ('xdf', 'refbin EPST', 'SP', 'tables', 'band(KiB)', 'axisOv', 'tblOverlap', 'diffExpl'))
    for x in sorted(glob.glob(ROOT + '/*.xdf')):
        r = x.replace('.xdf', '_original.bin')
        if not os.path.exists(r):
            continue
        ep, sp = bin_ids(r)
        acc, ao, ov, dc, da = audit(x, r, o, m)
        import statistics
        band = len(verify.BAND) // 1024
        print('%-22s %-11s %-4s %6d %8d %8d %8d %7d/%d' %
              (os.path.basename(x)[:22], ep, sp, len(acc), band, ao, ov, dc, 3821))