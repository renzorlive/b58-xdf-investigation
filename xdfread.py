"""Minimal XDF (XDFORMAT 1.8x) reader/decoder for Bosch MG1 style calibration files."""
import re
import struct
import math
import xml.etree.ElementTree as ET


def _attrs(s):
    return dict(re.findall(r'(\w+)="([^"]*)"', s))


def _eq(expr):
    """Compile a XDF MATH equation (only uses X) into a python lambda."""
    e = expr.replace(' ', '')
    if re.fullmatch(r'[\d\.\+\-\*/\(\)X]+', e) is None:
        return lambda x: x
    py = e.replace('X', 'x')
    # guard against python-specific constructs sneaking through
    if not re.fullmatch(r'[\d\.\+\-\*/\(\)x]+', py):
        return lambda x: x
    try:
        code = compile(py, '<m>', 'eval')
    except SyntaxError:
        return lambda x: x

    def f(x):
        try:
            v = eval(code, {'__builtins__': {}}, {'x': x})
        except Exception:
            return float('nan')
        return v
    return f


class Axis:
    __slots__ = ('id', 'title', 'address', 'esize_bits', 'rowcount', 'colcount',
                 'major_stride', 'minor_stride', 'indexcount', 'dtype', 'eq',
                 'mn', 'mx', 'labels', 'is_z')

    def shape(self):
        r = self.rowcount if self.rowcount else 1
        c = self.colcount if self.colcount else 1
        return r, c

    def byte_span(self):
        r, c = self.shape()
        r = max(r, self.indexcount or 1)
        c = max(c, self.indexcount or 1)
        eb = self.esize_bits // 8 or 2
        if self.major_stride or self.minor_stride:
            span = (c - 1) * (self.major_stride // 8) + (r - 1) * (self.minor_stride // 8) + eb
            return span
        return r * c * eb


class Table:
    __slots__ = ('title', 'desc', 'categories', 'x', 'y', 'z')

    @property
    def data_axis(self):
        return self.z or self.y or self.x


def parse(path):
    raw = open(path, encoding='utf-8', errors='replace').read()
    root = ET.fromstring(raw)
    hdr = root.find('XDFHEADER')
    cats = {}
    if hdr is not None:
        for c in hdr.findall('CATEGORY'):
            cats[c.get('index')] = c.get('name')
    base = 0
    bo = hdr.find('BASEOFFSET') if hdr is not None else None
    if bo is not None:
        base = int(bo.get('offset', '0'), 0) - int(bo.get('subtract', '0'), 0)

    tables = []
    for t in root.findall('XDFTABLE'):
        title = t.findtext('title', '') or ''
        desc = t.findtext('description', '') or ''
        cl = []
        for cm in t.findall('CATEGORYMEM'):
            cl.append(cats.get(cm.get('category'), cm.get('category')))
        axes = {}
        for a in t.findall('XDFAXIS'):
            ax = Axis()
            ax.id = a.get('id')
            ed = a.find('EMBEDDEDDATA')
            ax.address = int(ed.get('mmedaddress'), 0) if (ed is not None and ed.get('mmedaddress')) else None
            ax.esize_bits = int(ed.get('mmedelementsizebits', '16'), 0) if ed is not None else 16
            ax.rowcount = int(ed.get('mmedrowcount', '0'), 0) if ed is not None else 0
            ax.colcount = int(ed.get('mmedcolcount', '0'), 0) if ed is not None else 0
            ax.major_stride = int(ed.get('mmedmajorstridebits', '0'), 0) if ed is not None else 0
            ax.minor_stride = int(ed.get('mmedminorstridebits', '0'), 0) if ed is not None else 0
            ic = a.findtext('indexcount')
            ax.indexcount = int(ic) if ic and ic.strip() else 0
            dt = a.findtext('datatype')
            ax.dtype = int(dt) if dt and dt.strip() else 0
            m = a.find('MATH')
            ax.eq = _eq(m.get('equation', 'X')) if m is not None else (lambda v: v)
            ax.mn = a.findtext('min')
            ax.mx = a.findtext('max')
            ax.labels = {int(l.get('index')): l.get('value') for l in a.findall('LABEL')}
            axes[ax.id] = ax
        tb = Table()
        tb.title = title
        tb.desc = desc
        tb.categories = cl
        tb.x, tb.y, tb.z = axes.get('x'), axes.get('y'), axes.get('z')
        if tb.z is None and tb.y is not None and tb.x is None:
            tb.z, tb.x = tb.y, None
        tables.append(tb)
    return base, tables


def read_axis(ax, data, base=0):
    """Return a flat list of raw unsigned values, or None if not backed by bin data."""
    if ax is None or ax.address is None:
        return None
    start = ax.address + base
    span = ax.byte_span()
    if start < 0 or start + span > len(data):
        return None
    eb = ax.esize_bits // 8
    r, c = ax.shape()
    out = []
    if ax.major_stride or ax.minor_stride:
        ms = ax.major_stride // 8 or eb
        ns = ax.minor_stride // 8 or eb
        for cc in range(c):
            for rr in range(r):
                off = start + cc * ms + rr * ns
                out.append(_rd(data, off, eb, ax.dtype))
    else:
        n = r * c
        for i in range(n):
            out.append(_rd(data, start + i * eb, eb, ax.dtype))
    return out


def _rd(data, off, eb, dtype):
    try:
        chunk = data[off:off + eb]
    except IndexError:
        return float('nan')
    if dtype == 0:
        return int.from_bytes(chunk, 'big', signed=False)
    if dtype == 1:
        return int.from_bytes(chunk, 'big', signed=True)
    if dtype == 4:
        return struct.unpack('>f', chunk)[0]
    if dtype == 5:
        return struct.unpack('>d', chunk)[0]
    return int.from_bytes(chunk, 'big', signed=False)


def decode_table(tb, data, base=0, scale=True):
    """Return (bp_x, bp_y, values2d) or None. values2d rows=y cols=x like TunerPro."""
    z = tb.z
    if z is None or z.address is None:
        return None
    r, c = z.shape()
    if z.indexcount:
        if z.rowcount and not z.colcount:
            c = z.indexcount
        elif z.colcount and not z.rowcount:
            r = z.indexcount
        elif not z.rowcount and not z.colcount:
            r = c = z.indexcount
    if r * c == 0 or r * c > 100000:
        return None
    bx = read_axis(tb.x, data, base) if tb.x else None
    by = read_axis(tb.y, data, base) if tb.y else None
    bx = bx[:c] if bx else None
    by = by[:r] if by else None
    if scale:
        bx = [tb.x.eq(v) for v in bx] if bx else None
        by = [tb.y.eq(v) for v in by] if by else None
    vals = read_axis(z, data, base)
    if vals is None:
        return None
    vals = [z.eq(v) for v in vals] if scale else vals
    grid = []
    for rr in range(r):
        grid.append(vals[rr * c:(rr + 1) * c])
    return bx, by, grid