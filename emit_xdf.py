"""Emit an XDF containing only the tables whose placement is verified.

Addresses are rewritten with the table's own derived delta. Nothing is emitted
unless verify.run() accepted it.
"""
import re
import os
import sys
import json
import verify

HDR = ('<?xml version="1.0" encoding="utf-8"?>\n'
       '<XDFFORMAT xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
       'xmlns:xsd="http://www.w3.org/2001/XMLSchema" version="1.80">')


def emit(xdf_path, accepted, out_path, region_size, title):
    raw = open(xdf_path, encoding='utf-8').read()
    parts = re.split(r'(?=<XDFTABLE[ >])', raw)
    head = parts[0]
    keep = {}
    for idx, tb, off, how, s in accepted:
        keep[idx] = off

    out = [head]
    uid = 0x1000
    idx = -1
    for p in parts[1:]:
        idx += 1
        if idx not in keep:
            continue
        d = keep[idx]
        p = re.sub(r'(mmedaddress=")(0x[0-9A-Fa-f]+|[0-9]+)"',
                   lambda m: '%s%s"' % (m.group(1), hex(int(m.group(2), 0) + d)), p)
        if 'uniqueid' not in p.split('>', 2)[1]:
            p = p.replace('<XDFTABLE>', '<XDFTABLE uniqueid="0x%x">' % uid, 1)
            uid += 1
        out.append(p)

    doc = ''.join(out)
    if '</XDFFORMAT>' not in doc:
        doc += '</XDFFORMAT>\n'
    doc = doc.replace('size="0x800000"', 'size="%s"' % region_size)
    doc = doc.replace('<description />',
                      '<description>%s</description>' % title, 1)
    open(out_path, 'w', encoding='utf-8').write(doc)
    return len(keep)


if __name__ == '__main__':
    xdf_path = sys.argv[1]
    ref_path = sys.argv[2]
    bin_path = sys.argv[3]
    lo, hi = int(sys.argv[4], 0), int(sys.argv[5], 0)
    out = sys.argv[6]

    acc, tabs, med = verify.run(xdf_path, ref_path, bin_path, lo, hi)
    n = emit(xdf_path, acc, out, '0x7C0000',
             'Verified B58 MG1CS003 map set for R0C2J772B (stock OEM). '
             '%d tables, placement content-anchored to breakpoint arrays. '
             'Offset band 0x40AC2-0x413FE, median 0x%X.' % (len(acc), med))
    print('wrote', out, n, 'tables')

    ori = open(bin_path, 'rb').read()
    mod = None
    for cand in (bin_path.replace('_ori', '.Bin'), bin_path.replace('_ori', '') + '.Bin',
                 _mod()):
        if os.path.exists(cand):
            mod = open(cand, 'rb').read()
            break
    report = []
    for i, tb, off, how, sc in acc:
        z = tb.z
        st = z.address + off
        row = dict(title=tb.title, desc=tb.desc, user_addr=hex(st),
                   rows=z.rowcount or z.indexcount, cols=z.colcount or z.indexcount,
                   esize=z.esize_bits, offset=hex(off), method=how, range_ok=round(sc, 4),
                   cats='; '.join(tb.categories))
        if mod:
            row['tuned_bytes'] = sum(1 for k in range(st, st + z.byte_span()) if ori[k] != mod[k])
        report.append(row)
    json.dump(report, open('out/verified_report.json', 'w'), indent=1)
    print('wrote out/verified_report.json')