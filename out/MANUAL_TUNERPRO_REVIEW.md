# MANUAL_TUNERPRO_REVIEW

A guide to inspecting the stock and Stage 2 BINs side by side. Read-only.

---

## Which file to open

```
out/R0C2J772B_manual_inspection.xdf
```

This is the exploratory inspection definition. Do **not** open or use
`R0C2J772B_verified.xdf` (legacy SP11-based, superseded), `R0C2J772B_CANDIDATE.xdf`
(has 10 known-bad axis references) or `R0C2J772B_CANDIDATE_axesclean.xdf` (identical to
the manual file minus the 7 exploratory tables). All four are retained unchanged.

## Which BIN to load first

1. Load **`10SW002828_iRom_ori`** (stock). The XDF REGION is `0x7C0000` = 8,126,464 bytes,
   which matches both BINs exactly. If TunerPro warns about size, stop — something is wrong.
2. Work through the tables you care about.
3. Only then load **`10SW002828_iRom_stage2`** — the **same XDF**, same addresses.

> I have not run this file in TunerPro. It was validated structurally and numerically, not
> by opening it in the editor. If it fails to load, tell me the error text.

## Comparing stock against Stage 2 without writing anything

TunerPro writes only when you press **Save / Write to flash**. For comparison:

- Load the stock BIN, note values on the tables listed below.
- Close **without saving**.
- Load the Stage 2 BIN into the same XDF. Every address is identical, so the same table now
  shows the tuned values.
- **Do not** use "save", "write", "burn", or any flash button at any point.

If you want a side-by-side instead: open TunerPro twice, or use the two BINs with an
external diff. The machine-readable equivalent already exists —
`out/tuner_delta_regions.csv` has per-region offsets and before/after hex, and
`out/manual_xdf_validation.csv` has a per-table `stock_vs_stage2` column counting how many
cells differ.

---

## Tables to inspect first

**31 of the 78 tables differ between stock and Stage 2.** Highest value first:

| Table | Address | Dims | Cells differing | Note |
|---|---|---|---|---|
| `UNVERIFIED_REGION_7311B4` | `0x7311B4` | 1×434 | 288 | Largest unexplained change |
| `KF_LABAS_1` | `0x6FA45E` | 17×18 | 167 | Axis also rescaled ×0.8 |
| `KF_LABAS_2` | `0x6FA1FA` | 17×18 | 160 | Shares the same axis |
| `UNVERIFIED_REGION_730A8C` | `0x730A8C` | 1×146 | 128 | |
| `UNVERIFIED_REGION_70318B` | `0x70318B` | 1×133 | 91 | **Not identified** |
| `UNVERIFIED_REGION_7032CB` | `0x7032CB` | 1×133 | 91 | **Not identified** |
| `UNVERIFIED_REGION_70340B` | `0x70340B` | 1×133 | 91 | **Not identified** |
| `UNVERIFIED_REGION_6F7F2E` | `0x6F7F2E` | 1×72 | 72 | 30000 → 32767 throughout |
| `BMWtchsp_rat_p_CmprMax_M` | `0x6DE054` | 6×8 | 48 | |
| `BMWchas_lam_InjMpl_M` | `0x6EEE7C` | 10×10 | 45 | |
| `BMWchas_lam_InjMplThr_M` | `0x6EEF44` | 10×10 | 45 | |
| `UNVERIFIED_REGION_6F1BA0` | `0x6F1BA0` | 1×128 | 44 | |

Also look at **`KF_LABAS_1` / `KF_LABAS_2`'s y-axis** at `0x6FA6CE`: 17 points × 16-bit
big-endian, rescaled from `2000…18000` to `1600…14400`. That is **exactly `× 0.8`** on every
point, with no rounding. The 18-point x-axis at `0x6FA6F0` was **not** changed.

---

## What remains uncertain

**Names are inherited, not confirmed.** Tables 1–71 get their Bosch variable names from an
S15A-18 reference image. Your ECU is S15A-17. A name in this XDF is a label someone else
attached to a matching byte pattern — it is **not** proof that the map at that address is
what the name says. Treat every name as a hypothesis.

**Axes.** 59 axis slots are deliberately address-less (no data read, single implicit
breakpoint). Ten axes were removed because they read sentinel values (≥60000) or
non-monotonic sequences — i.e. they were not breakpoint arrays at all. Those addresses were
**not** restored. Tables with no usable axis show raw values with no scale context.

**Formulas.** 27 distinct linear formulas, all corroborated against the DAMOS A2L where a
match existed (59 of 65 checked exactly; 6 are deliberate ×14.7 AFR conversions). None
contains parentheses, offsets or division by `X`.

**Units.** The A2L supplies units only for the `KL_MD_K_MAX_*` family (`Nm`). For most other
tables the pack declares no unit, so none is shown.

**Exploratory tables** (`UNVERIFIED_REGION_*`) have no established identity, dimensions or
units — except `0x6F7F2E`, where 16-bit element width is established (the 144 bytes contain
exactly two distinct uint16 values, 30000 and 32767). They are presented as flat arrays so
no shape is implied.

### Do not label these

The three blocks near `0x70318B`, `0x7032CB`, `0x70340B` are **not** identified as ignition.
Their stock bytes match a reference image (3,579 and 3,259 contiguous identical bytes), but
the match begins where the changed region begins, which does not establish a map boundary,
and the content delta `+0x3F7D0` conflicts with the independently located breakpoint-axis
delta `+0x3F9CE`. They are deliberately **not** named, dimensioned or given units.

Similarly nothing here is established as boost target, injection timing, or torque limit
*function*. `KL_MD_K_MAX_*` are labelled torque setpoints in Nm because the A2L says so —
that is a setpoint, not a prediction of what the engine delivers.

---

## Distinguishing a real change from a display artifact

Because a formula is applied on top of the raw value, the same bytes can look different for
reasons that are not tuning changes. Checklist when a table looks changed:

1. **Is the axis also changed?** If the breakpoints moved, every cell's *meaning* shifts
   even where the raw bytes are untouched. `KF_LABAS_1/2` is exactly this case — the y-axis
   was rescaled ×0.8, so compare raw bytes, not just displayed values.
2. **Is the element width right?** 8-bit vs 16-bit halves or doubles the apparent range.
   Everything here is big-endian; a swapped width produces values that look real but are not.
3. **Is a conversion applied?** `X/4096*14.7` shows AFR; `X*0.00006103516` shows a small
   ratio. Compare the **raw** bytes in a hex editor at the address column before trusting any
   displayed difference.
4. **Address vs value.** A single changed byte near a table start can be a flag; a
   contiguous run of changed cells is more likely data. Region 89 is 4 changed bytes at
   `0x7BFCFC` with **no established meaning** — it is deliberately not in the XDF.

**Reliable rule:** a genuine tuner edit means the underlying bytes differ between the two
BINs. Verify with `out/tuner_delta_regions.csv`, which lists every changed offset with
before/after hex. If the bytes match, any difference you see on screen is display-side.

---

## Safety

This XDF is for **inspection only**. It is not a validated tuning definition, and I make no
claim that the Stage 2 calibration is safe, correct, or understood — 1,439 of 3,821 changed
bytes remain outside any identified definition. Do not flash anything produced with this
file, and do not adjust values on the assumption that a map name is correct.