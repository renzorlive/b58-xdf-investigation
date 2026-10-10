#!/usr/bin/env python3
"""Build a corrected ignition-timing XDF for R0C2J772B (S15A-17).

Replaces the previous candidate file, whose tables carried address-less axes
(indexcount=1). TunerPro derives table geometry from the X/Y axis indexcount,
so those tables rendered as a single cell. Here every table has real axis
pointers into the target BIN, verified independently by content search.

Evidence chain (see out/IGNITION_TIMING_REINVESTIGATION.md):
  * A2L  : mgflasher-map-packs/A2Ls/B48 B58 Gen 1/Generic/R0C9J8B2B_3081-080_017_002.a2l
           declares KF_ZW_* CHARACTERISTIC/AXIS_PTS records with EPK addresses.
  * REF  : ref/BMW-XDFs-master/B58gen1/00003081501102_original.bin  (S15A-18)
  * TGT  : 10SW002828_iRom_ori                                    (S15A-17)
Axis and map addresses in TGT were located by exact-content search, not by
assuming a single global offset.
"""
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

ROOT = os.path.dirname(os.path.abspath(__file__))
TGT = os.path.join(ROOT, '10SW002828_iRom_ori')
OUT = os.path.join(ROOT, 'out', 'R0C2J772B_ignition_timing.xdf')

# name, target z addr, X(axis=Nkw) addr, Y(addr), nx, ny, conf, note
MAPS = [
    ('KF_ZW_PF1  - Base ignition angle path 1',      0x703350, 0x6EC656, 0x6EC596, 20, 16,
     'HIGH', 'Modified by Stage 2: 91 cells, +11..+51 deg.'),
    ('KF_ZW_PF2  - Base ignition angle path 2',      0x703210, 0x6EC62E, 0x6EC576, 20, 16,
     'HIGH', 'Modified by Stage 2: 91 cells.'),
    ('KF_ZW_S_PF1 - Base ignition angle path 1 safe', 0x7030D0, 0x6EC606, 0x6EC556, 20, 16,
     'HIGH', 'Modified by Stage 2: 91 cells, +11..+48.5 deg.'),
    ('KF_ZW_S_PF2 - Base ignition angle path 2 safe', 0x702F90, 0x6EC5DE, 0x6EC536, 20, 16,
     'HIGH', 'Modified by Stage 2: 91 cells.'),
    ('KF_ZW_UESP_PF1 - Base ignition angle scavenging p1', 0x702F04, 0x6EC5CA, 0x6EC51A, 10, 14,
     'HIGH', 'Unmodified in Stage 2.'),
    ('KF_ZW_UESP_PF2 - Base ignition angle scavenging p2', 0x702E78, 0x6EC5B6, 0x6EC4FE, 10, 14,
     'HIGH', 'Unmodified in Stage 2.'),
    ('KF_ZW_VP_PF1 - Ignition angle with VANOS at stop p1', 0x7072A8, 0x6FA9B2, 0x6FA96A, 20, 16,
     'MEDIUM', 'VANOS map. Axis pair from a differently-laid-out block; content verified.'),
    ('KF_ZW_VP_PF2 - Ignition angle with VANOS at stop p2', 0x707168, 0x6FA98A, 0x6FA94A, 20, 16,
     'MEDIUM', 'VANOS map. Axis pair from a differently-laid-out block; content verified.'),
    ('KF_ZWMIN_WSOT - Min ignition angle, sound tuning warm', 0x706DEC, 0x6F99AE, 0x6F996E, 8, 8,
     'MEDIUM', '8x8 limit map. Unmodified in Stage 2.'),
    ('KF_ZWMIN_KSOT - Min ignition angle, sound tuning cold', 0x706E2C, 0x6F99BE, 0x6F997E, 8, 8,
     'MEDIUM', '8x8 limit map. Unmodified in Stage 2.'),
]

HEADER = """Ignition timing maps for BMW B58 / MG1CS003, EPK R0C2J772B, EPST R0C9J772B,
PST S15A-17-11-490, HW 10SW002828.

Load this file ALONGSIDE R0C2J772B_manual_inspection.xdf. Do not write to the ECU.

IDENTITY EVIDENCE
  Symbol names, dimensions and the x0.5 deg conversion come from the Bosch A2L
  "R0C9J8B2B_3081-080_017_002.a2l" (project R0C2J8B2B, MG1CS003). Addresses were
  located in the TARGET image by exact byte-content search of each map and axis,
  not by transferring reference addresses.
  The A2L describes S15A-18. This target is S15A-17, so dimensions/identity are
  inherited, not proven. Confidence per table is given in each description.

CONFIDENCE
  HIGH   = A2L symbol + byte-identical map content + byte-identical axis content
           + physically correct monotonic behaviour + (for 4 maps) matching tuner edits.
  MEDIUM = as above but located in a differently-laid-out region, so the axis/data
           pairing rests on block-internal ordering rather than a single global offset.

UNITS
  X axis = Nkw  engine speed [1/min]  (breakpoints shown)
  Y axis = NO_INPUT_QUANTITY, air-mass/load [%]
  Z axis = ignition angle, crank degrees, SIGNED int8, phys = X*0.5  (range -64.0..+63.5)

SCOPE / LIMITS
  These maps are the BASE ignition angle, not the final commanded timing. Torque
  limits, knock control, per-cylinder corrections and the air-mass path sit
  upstream/downstream and are NOT described here.
  Nothing here has been validated as a tuning definition. Do not tune from this file.
"""

CAT_IGN = 'Ignition timing'


def build():
    size = os.path.getsize(TGT)
    ET.register_namespace('', '')
    xdf = ET.Element('XDFFORMAT', version='1.80')
    hdr = ET.SubElement(xdf, 'XDFHEADER')
    ET.SubElement(hdr, 'XDFAPPINFO')
    ET.SubElement(hdr, 'BASEOFFSET').text = '0x0'
    d = ET.SubElement(hdr, 'DEFAULTS', datatype='0', unittype='0', decimalpl='0')
    ET.SubElement(d, 'EMBEDDEDDATA', mmedtypeflags='0x00', mmedelementsizebits='16',
                  mmedmajorstridebits='0', mmedminorstridebits='0')
    ET.SubElement(d, 'MAP', mmedtypeflags='0x00', mmedelementsizebits='16',
                  mmedmajorstridebits='0', mmedminorstridebits='0')
    ET.SubElement(hdr, 'REGION', start='0x0', size=hex(size))
    ET.SubElement(hdr, 'CATEGORY', index='0', type='0', name=CAT_IGN)

    uid = 1
    for name, zaddr, xaddr, yaddr, nx, ny, conf, note in MAPS:
        assert zaddr + nx * ny <= size, name
        t = ET.SubElement(xdf, 'XDFTABLE', uniqueid=str(uid), flags='0x0')
        ET.SubElement(t, 'title').text = name
        ET.SubElement(t, 'description').text = (
            '%s  |  confidence: %s\n'
            'Symbol/dimensions/0.5 deg conversion from Bosch A2L R0C9J8B2B_3081-080_017_002.a2l '
            '(project R0C2J8B2B, MG1CS003, S15A-18). This target is S15A-17.\n'
            'Z=%d x %d signed int8 at 0x%06X. X axis (Nkw, 1/min) at 0x%06X. '
            'Y axis (load, %%) at 0x%06X.\n'
            'Address proof: map bytes and both axis arrays were located in the target '
            'by exact-content search of the reference image; all match byte-for-byte. '
            '%s\n'
            'Values are BASE ignition angle in crank degrees; the final commanded '
            'timing includes torque/knock/per-cylinder corrections not described here.'
            % (name, conf, ny, nx, zaddr, xaddr, yaddr, note))
        ET.SubElement(t, 'CATEGORYMEM', index='0', category='0')
        for axis, addr, cnt, unit, fmt in (
                ('x', xaddr, nx, '1/min', 'X'),
                ('y', yaddr, ny, '%', 'X')):
            a = ET.SubElement(t, 'XDFAXIS', id=axis, uniqueid='0x0')
            ET.SubElement(a, 'EMBEDDEDDATA', mmedtypeflags='0x00',
                          mmedaddress=hex(addr), mmedelementsizebits='16',
                          mmedcolcount=str(cnt), mmedmajorstridebits='0',
                          mmedminorstridebits='0')
            ET.SubElement(a, 'units').text = unit
            ET.SubElement(a, 'indexcount').text = str(cnt)
            ET.SubElement(a, 'decimalpl').text = '0'
            ET.SubElement(a, 'datatype').text = '0'
            ET.SubElement(a, 'unittype').text = '0'
            ET.SubElement(a, 'embedinfo', type='1')
            ET.SubElement(a, 'DALINK', index='0')
            ET.SubElement(a, 'MATH', equation=fmt).append(ET.Element('VAR', id='X'))
        z = ET.SubElement(t, 'XDFAXIS', id='z', uniqueid='0x0')
        ET.SubElement(z, 'EMBEDDEDDATA', mmedtypeflags='0x01', mmedaddress=hex(zaddr),
                      mmedelementsizebits='8', mmedrowcount=str(ny), mmedcolcount=str(nx),
                      mmedmajorstridebits='0', mmedminorstridebits='0')
        ET.SubElement(z, 'units').text = 'deg'
        ET.SubElement(z, 'decimalpl').text = '1'
        ET.SubElement(z, 'min').text = '-64.0'
        ET.SubElement(z, 'max').text = '63.5'
        ET.SubElement(z, 'outputtype').text = '1'
        ET.SubElement(z, 'datatype').text = '0'
        ET.SubElement(z, 'unittype').text = '0'
        ET.SubElement(z, 'embedinfo', type='1')
        ET.SubElement(z, 'MATH', equation='X*0.5').append(ET.Element('VAR', id='X'))
        uid += 1

    xml = minidom.parseString(ET.tostring(xdf, encoding='utf-8')).toprettyxml(indent='  ')
    xml = xml.split('\n', 1)[1]
    head = ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE XDFFORMAT [<!ELEMENT XDFFORMAT (XDFHEADER,XDFTABLE*)>\n'
            '<!ELEMENT XDFTABLE (title,description,CATEGORYMEM,XDFAXIS,XDFAXIS,XDFAXIS)>\n'
            '<!ELEMENT XDFAXIS (EMBEDDEDDATA?,units?,indexcount?,decimalpl?,min?,max?,'
            'outputtype?,datatype?,unittype?,embedinfo?,DALINK?,MATH?)>]>\n')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write(head + '<!--\n' + HEADER + '-->\n' + xml)
    return len(MAPS)


if __name__ == '__main__':
    n = build()
    print('wrote %s - %d maps with real axes' % (OUT, n))
    for m in MAPS:
        print('  0x%06X  %2dx%-3d  x=0x%06X y=0x%06X  %s' % (m[1], m[5], m[4], m[2], m[3], m[0][:44]))
