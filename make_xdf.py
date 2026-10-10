"""Generate a re-based XDF for a user binary from a reference XDF.

Per-table offsets come from content-anchored breakpoint axes (high confidence);
tables that cannot be anchored fall back to the global cal-block shift.
"""
import xdfread
import align
import re
import sys
import os


def shift_xdf(xml_text, offsets):
    """offsets: {xdf_table_index: delta}. Rewrite mmedaddress on every axis of that table."""
    # split into XDFTABLE chunks, keep order
    parts = re.split(r'(?=<XDFTABLE[ >])', xml_text)
    head = parts[0]
    out = [head]
    idx = -1
    for p in parts[1:]:
        idx += 1
        d = offsets.get(idx)
        if d:
            def repl(m):
                return '%s%s"' % (m.group(1), hex(int(m.group(2), 0) + d))
            p = re.sub(r'(mmedaddress=")(0x[0-9A-Fa-f]+|[0-9]+)"', repl, p)
        out.append(p)
    return ''.join(out)


def main():
    xdf_path, ref_path, bin_path, out_path = sys.argv[1:5]
    lo, hi = int(sys.argv[5], 0), int(sys.argv[6], 0)
    fallback = int(sys.argv[7], 0)

    res, base = align.main(xdf_path, ref_path, bin_path, lo, hi, require_both=True)
    offsets = {}
    conf = 0
    for i, (tb, off, how) in enumerate(res):
        if off is not None:
            offsets[i] = off
            conf += 1
        else:
            offsets[i] = fallback
    xml = open(xdf_path, encoding='utf-8').read()
    new = shift_xdf(xml, offsets)
    # widen region + record provenance
    new = new.replace('size="0x800000"', 'size="0x7C0000"')
    new = new.replace('<description />', '<description>Re-based from %s for R0C2J772B (%d/%d tables content-anchored, fallback offset 0x%X)</description>'
                      % (os.path.basename(xdf_path), conf, len(res), fallback), 1)
    open(out_path, 'w', encoding='utf-8').write(new)
    print('wrote', out_path)


if __name__ == '__main__':
    main()