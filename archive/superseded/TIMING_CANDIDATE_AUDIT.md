# TIMING CANDIDATE AUDIT

Investigation of the ignition-timing map candidates in `10SW002828_iRom_ori` /
`10SW002828_iRom_stage2` (ECU MG1CS003 / DME8.6, EPK `R0C2J772B`, EPST `R0C9J772B`,
PST `S15A-17-11-490`).

**Read-only.** Neither BIN, nor any existing XDF or report, was modified.
Created: `out/R0C2J772B_timing_candidates.xdf`, this report, and the build/validation
scripts.

---

## 1 — What changed since the last report: the block boundary is now resolved

Earlier work reported a "3,579-byte correspondence" starting at `0x70318B`. That figure was
an artefact of **where my search began**, not a boundary. Extending the match in *both*
directions gives the true extent:

```
target : 0x702DED .. 0x703F85   (4,505 bytes)
reference (C2J8B2B / S15A-18-03-510) : 0x6C361D .. 0x6C47B5
delta  : +0x3F7D0
```

The block is cleanly bounded — the bytes immediately before and after do not continue the
match. **This is the single strongest piece of evidence in the whole investigation**: a
4,505-byte byte-identical correspondence between this image and an S15A-18 reference.

It also settles §4's first question. The three priority blocks are **not three separate
tables**; they are portions of **four consecutive 320-byte structures** inside that block.

---

## 2 — Resolving the offset conflict (not forced)

Two independent, reproducible correspondences exist, and **they disagree**. I have not made
them agree.

### Evidence A — content correspondence, delta `+0x3F7D0`
The 4,505-byte block above. Strong: one continuous run, thousands of bytes.

### Evidence B — breakpoint-array correspondence, delta `+0x3F9CE`
Located in this image at `0x6EC5DE`, `0x6EC606`, `0x6EC62E`, `0x6EC656` (four copies of a
20-point ascending array `[500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500, 2750, 3000,
3250, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 6950]`) plus four 16-point arrays at
`0x6EC536`, `0x6EC556`, `0x6EC576`, `0x6EC596`. All eight match the reference's
`KF_ZW_*` axis block at `0x6ACC10`–`0x6ACBC8` exactly, at a consistent `+0x3F9CE`.
Also strong: eight independent arrays, uniform delta.

### The conflict
`0x3F9CE − 0x3F7D0 = 0x1FE` (510 bytes). Testing the layout the content correspondence
implies: if the 16×20 map at reference `0x6C3900` sits at target `0x7030D0`, its x-axis
(reference `0x6ACC38`, relative offset `−0x16CC8`) should be at target `0x6EC408`. That
address reads `[30, 700, 7000, 7000, 7000, 700, 660, 660]` — **not** the array. The real
array is at `0x6EC5DE`, **470 bytes later** than the content layout predicts.

### Both explanations, unresolved
- **The axis block is laid out differently in S15A-17** — more or fewer shared arrays between
  `0x6AC000` and `0x6C3000`, shifting the axes relative to the data. Plausible: these arrays
  are shared by many maps, so array count is version-sensitive.
- **The eight arrays at `0x6EC5DE`… belong to a different map family** that happens to use
  the same 20-point array, and the `KF_ZW_*` axes for the block at `0x702DED` are elsewhere
  or absent.

**Consequence for the XDF:** the axes cannot be attached to these maps. A 20-point array was
*found* at a uniform offset, but attaching it to these specific maps would require assuming
one of the two unproven explanations above. **No axes are therefore attached.** Every
candidate table below has address-less axes and a single implicit breakpoint. This is
deliberate: a wrong axis is worse than no axis.

---

## 3 — Candidate tables

All seven are byte-identical to the S15A-18 reference at `+0x3F7D0` (verified in §5).
Dimensions and element width are taken from the map declarations occupying the
corresponding reference spans. **The reference labels are hypotheses, not identities.**

| Candidate (neutral name) | Addr | Ref addr | Dims | Bits | Reference label — **hypothesis** | Changed cells | Confidence |
|---|---|---|---|---|---|---|---|
| `UNVERIFIED_TIMING_CANDIDATE_702F18` | `0x702F18` | `0x6C36A8` | 14×10 | 8 | `KF_ZW_UESP_PF2` (spool, path 2) | 0 / 140 | address+layout high |
| `UNVERIFIED_TIMING_CANDIDATE_702F04` | `0x702F04` | `0x6C3734` | 14×10 | 8 | `KF_ZW_UESP_PF1` (spool, path 1) | 0 / 140 | address+layout high |
| `UNVERIFIED_TIMING_CANDIDATE_702F90` | `0x702F90` | `0x6C37C0` | 16×20 | 8 | `KF_ZW_S_PF2` (cold, path 2) | **91 / 320** | address+layout high; identity low |
| `UNVERIFIED_TIMING_CANDIDATE_7030D0` | `0x7030D0` | `0x6C3900` | 16×20 | 8 | `KF_ZW_S_PF1` (cold, path 1) | **91 / 320** | address+layout high; identity low |
| `UNVERIFIED_TIMING_CANDIDATE_703210` | `0x703210` | `0x6C3A40` | 16×20 | 8 | `KF_ZW_PF2` (main, path 2) | **91 / 320** | address+layout high; identity low |
| `UNVERIFIED_TIMING_CANDIDATE_703350` | `0x703350` | `0x6C3B80` | 16×20 | 8 | `KF_ZW_PF1` (main, path 1) | **91 / 320** | address+layout high; identity low |
| `UNVERIFIED_TIMING_CANDIDATE_703490` | `0x703490` | `0x6C3CC0` | 16×20 | 8 | unlabelled successor span | 0 / 320 | address+layout high; identity none |

**Raw stock vs Stage 2 comparison.** The four 16×20 maps that the tuner edited each show
**exactly 91 changed bytes, each beginning at map offset `+0xBB` (187)** — the same
relative offset in all four, in the same order as the reference declares them
(S_PF2 → S_PF1 → PF2 → PF1). That consistency across four independent structures is
reproducible evidence that the tuner's edits map onto these four structures.

**Axes:** none attached (§2).
**Conversion:** identity `X` for all. The A2L declares `×0.5 °/LSB` for `KF_ZW_S_PF2` in the
S15A-18 image, but that formula belongs to the *named map in that image*. Since identity is
not established for this image, **no scaling is applied** — values display raw. Divide by 2
if you want the reference's displayed range.
**Units:** none shown, because none is established for this target.

---

## 4 — Are the three priority blocks separate tables, portions of larger ones, or unrelated?

**Portions of four larger structures.** Evidence:

1. All three sit inside one 4,505-byte byte-identical correspondence (§1).
2. They are spaced exactly 320 bytes apart (`0x70318B`, `0x7032CB`, `0x70340B`).
3. A fourth, `0x70304B`, continues the same 320-byte series — and at delta `+0x3F7D0` the
   series maps onto four consecutive 320-byte maps declared in the reference, in the same
   order.
4. Each changed block begins at `+0xBB` into its 320-byte structure, consistently across all
   four.

They are **not** unrelated structures: they are four equally sized tables inside one
correspondence block, three of which the tuner edited at the same internal offset.

---

## 5 — Validation results

```
XML parses                                 OK   XDFFORMAT 1.80
REGION start=0x0 size=0x7C0000             OK   8,126,464 = BIN size
tables                                     7
structural errors                          0
all data spans within BIN                  yes  (max end 0x7035D0)
axis length vs table geometry              consistent (all address-less, indexcount 1)
conversion formulas                        1  ("X") - no unsafe expressions
address-less axis slots                    14
bytes mapped                               1,880
bytes differing stock vs stage2            364
all 7 maps byte-identical to reference
  at delta +0x3F7D0                        TRUE  (verified programmatically)
```

Raw values were decoded from `10SW002828_iRom_ori` at each address and compared to the
reference at the implied offset; all seven match exactly.

**Element width / byte order.** 8-bit, big-endian-agnostic (byte elements). Big-endian was
established for the surrounding calibration maps and is consistent here; a byte element has
no byte order to get wrong.

**Not tested in TunerPro.** TunerPro is not available here. Structure and values were
validated programmatically. Format conventions were copied from the packs already in use.

---

## 6 — What this does and does not establish

**Established:**
- A 4,505-byte region of this image is byte-identical to an S15A-18 reference at `+0x3F7D0`.
- Seven structures at the addresses listed, with the dimensions and element widths shown.
- Four of them were edited by the tuner, 91 bytes each, all at the same internal offset.

**Not established:**
- That any of them is ignition timing. The `KF_ZW_*` labels are transferred hypotheses from
  a different software sub-revision.
- Their breakpoints, axis locations, scaling, units, or physical function.
- Why the content and axis deltas differ by 510 bytes.
- Whether the eight arrays at `0x6EC5DE`… belong to these maps at all.

**Deliberately not claimed:** I am not asserting these are ignition maps, that the
Stage 2 changes to them are correct, or that the calibration is safe. The value range
(roughly 8–80 raw) resembles an advance table and the A2L for the reference image declares
`×0.5 °/LSB` — but **that is plausibility plus a borrowed formula, not proof**, and it is
the exact reasoning this investigation has avoided throughout.

---

## 7 — What would resolve it

1. **A stock BIN reporting `R0C2J772B` / `S15A-17-*`.** Content-anchoring the 20-point array
   against the correct image would fix the axis placement and settle §2 immediately.
2. **A Damos/A2L or XDF for EPST `R0C9J772B`** — would give authoritative axis addresses,
   dimensions and conversion for this exact software.
3. **The tuner's own definition file** — pins the whole address space.

---

## 8 — Preserved

Both BINs, all existing XDFs and all existing reports are unchanged. No ECU data was
written, patched or flashed. The general inspection XDF
`out/R0C2J772B_manual_inspection.xdf` is untouched; this timing set is a **separate** file
for use alongside it.