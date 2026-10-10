"""Read-only diff report between the original and tuner-modified BINs."""
import json

ORI = '10SW002828_iRom_ori'

import os as _os
def _mod():
    for c in ('10SW002828_iRom_stage2',_mod()):
        if _os.path.exists(c):
            return c
    raise SystemExit('tuned file not found')
MOD = _mod()


def regions(o, m, gap=64):
    diff = [i for i in range(len(o)) if o[i] != m[i]]
    groups = []
    for i in diff:
        if groups and i - groups[-1][1] <= gap:
            groups[-1][1] = i
        else:
            groups.append([i, i])
    return diff, groups


def main():
    o = open(ORI, 'rb').read()
    m = open(MOD, 'rb').read()
    diff, groups = regions(o, m)

    out = {'file_ori': ORI, 'file_mod': MOD, 'sizes': [len(o), len(m)],
           'total_changed_bytes': len(diff), 'regions': []}

    lines = []
    lines.append('# Diff report  %s  ->  %s' % (ORI, MOD))
    lines.append('sizes %d / %d bytes, %d changed bytes in %d regions (gap<=64)'
                 % (len(o), len(m), len(diff), len(groups)))
    lines.append('')
    hdr = '%-4s %-10s %-10s %-7s %-7s %s' % ('#', 'start', 'end', 'len', 'chg', 'note')
    lines.append(hdr)
    lines.append('-' * len(hdr))

    for n, (a, b) in enumerate(groups, 1):
        cnt = sum(1 for i in range(a, b + 1) if o[i] != m[i])
        rec = {'n': n, 'start': a, 'end': b, 'len': b - a + 1, 'changed': cnt,
               'bytes': [{'addr': i, 'ori': o[i], 'mod': m[i]} for i in range(a, b + 1)
                         if o[i] != m[i]]}
        out['regions'].append(rec)
        lines.append('%-4d 0x%08X 0x%08X %-7d %-7d' % (n, a, b, rec['len'], cnt))

    open('out/diff_report.txt', 'w').write('\n'.join(lines) + '\n')
    json.dump(out, open('out/diff_report.json', 'w'))
    print('\n'.join(lines))
    print('\nwrote out/diff_report.txt and out/diff_report.json')


if __name__ == '__main__':
    main()