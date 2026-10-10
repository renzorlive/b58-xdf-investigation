# B58 MG1CS003 — XDF investigation workspace

Forensic reconstruction of calibration map definitions for a BMW B58 / MG1CS003 ECU.
Target: **EPK `R0C2J772B`, EPST `R0C9J772B`, PST `S15A-17-11-490`, HW `10SW002828`**.

> **Exploratory only.** These XDFs are for manual inspection in TunerPro. They are **not**
> validated tuning definitions, and the map *names* they carry are inherited from a
> different software sub-revision. See "Caveats" below.

## Test in TunerPro (Windows)

1. Clone this repo.
2. Open TunerPro → `File ▸ Open BIN` → load **your stock read** (`10SW002828_iRom_ori`).
3. `Tools ▸ Configure / Load XDF` → `out/R0C2J772B_manual_inspection.xdf`.
4. Browse the tree. Load `out/R0C2J772B_timing_candidates.xdf` alongside for the timing block.
5. Close **without saving**, then open `10SW002828_iRom_stage2` with the *same* XDF to compare.
6. **Never** press save/write/burn. Use an XDF-monitor or hex editor for any comparison —
   see `out/MANUAL_TUNERPRO_REVIEW.md`.

Both XDFs declare `REGION size=0x7C0000` (8,126,464) which matches the BINs exactly.
If TunerPro complains about size, stop — something is wrong.

## Validate the XDFs (any OS, Python 3.8+, no dependencies)

```
python tools/validate_xdf.py
python tools/validate_xdf.py --bin path/to/your.bin
```

## What is in here

| Path | What it is |
|---|---|
| `out/R0C2J772B_manual_inspection.xdf` | **78 tables** — 71 byte-verified + 7 raw unidentified-region windows. Start here. |
| `out/R0C2J772B_timing_candidates.xdf` | **7 tables** — the ignition-timing candidate block (see below). |
| `out/*_AUDIT.md`, `out/*_REPORT.md` | The investigation record: what is proven, what is not. |
| `out/*.csv`, `out/*.json` | Per-region diffs, per-table audits, coverage numbers. |
| `*.py`, `tools/` | Reproducible build and validation scripts. |

## The timing candidates — important nuance

`R0C2J772B_timing_candidates.xdf` exposes **7 structures at `0x702F04`–`0x703490`** that sit
inside a **4,505-byte block byte-identical** to an S15A-18 reference image. Four of them
were edited by the tuner (91 bytes each, all at the same internal offset `+0xBB`).

- Address and layout: **strong evidence**
- That they are **ignition timing**: **not established.** The `KF_ZW_*` names are
  transferred hypotheses.
- **Axes are deliberately absent.** Breakpoint arrays were found, but at a relative offset
  that conflicts with the content correspondence by 510 bytes. A wrong axis would be worse
  than none.
- Values display **raw**. An A2L formula of ×0.5 °/LSB exists for the reference image, but
  applying it here would assert an identity that is not proven. Divide by 2 if you want that
  range.

## Caveats that matter

- **Zero** of the named tables are verified for the exact `S15A-17` target. Addresses and
  formulas are evidenced; names are inherited from `S15A-18`.
- 54.7% of the tuner's changed bytes remain unexplained.
- `0x7BFCFC` (4 bytes outside the calibration block) is **not** a checksum — no algorithm
  tested reproduces the stock value.
- No claim is made that the Stage 2 calibration is safe, correct, or understood.

## Not in this repo (deliberately)

The BIN files, `ref/`, `mgflasher-map-packs/` and the large reference zip are excluded via
`.gitignore` — ECU firmware is proprietary, and the reference packs total ~2.5 GB. Re-obtain
the reference packs from their own repositories if you need to re-run the build scripts.
