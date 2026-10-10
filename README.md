# B58 MG1CS003 — XDF investigation workspace

Forensic reconstruction of calibration map definitions for a BMW B58 / MG1CS003 ECU.
Target: **EPK `R0C2J772B`, EPST `R0C9J772B`, PST `S15A-17-11-490`, HW `10SW002828`**.

> **Exploratory only.** These XDFs are for manual inspection in TunerPro. They are **not**
> validated tuning definitions, and the map *names* they carry are inherited from a
> different software sub-revision. See "Caveats" below.

## Test in TunerPro (Windows)

1. Clone this repo.
2. Open TunerPro → `File ▸ Open BIN` → load **your stock read** (`10SW002828_iRom_ori`).
3. `Tools ▸ Configure / Load XDF` → **`out/R0C2J772B_display.xdf`** (the one you need).
4. Close **without saving**, then open `10SW002828_iRom_stage2` with the *same* XDF to compare.
5. **Never** press save/write/burn. Use an XDF-monitor or hex editor for any comparison —
   see `out/MANUAL_TUNERPRO_REVIEW.md`.

The XDF declares `REGION size=0x7C0000` (8,126,464), matching the BINs exactly.
If TunerPro complains about size, stop — something is wrong.

## Validate the XDFs (any OS, Python 3.8+, no dependencies)

```
python tools/validate_xdf.py
python tools/validate_xdf.py --bin path/to/your.bin
```

## What is in here

### Use these

| Path | What it is |
|---|---|
| **`out/R0C2J772B_display.xdf`** | **The file to load.** 85 tables: 75 inspection + 10 ignition timing, in one tree. |
| `out/R0C2J772B_ignition_timing.xdf` | The 10 ignition-timing tables alone, if you prefer them separate. |
| `out/R0C2J772B_manual_inspection.xdf` | The 78 inspection tables alone. |
| `out/IGNITION_TIMING_FINAL_VALIDATION.md` | Read this for what is proven and what is not. |
| `out/*.md` | The investigation record. |
| `out/*.csv`, `out/*.json` | Per-region diffs, per-table audits, coverage numbers. |
| `*.py`, `tools/` | Reproducible build and validation scripts. |

### Do not use

`archive/superseded/` holds artifacts that are **wrong** — see `archive/superseded/README.md`
for why each one failed. They are kept only for the audit trail.

## The ignition timing maps

10 maps in the "Ignition timing" category, all with real axes:

| Map | Address | Size | Stock → tuned |
|---|---|---|---|
| `KF_ZW_PF1` | `0x703350` | 16×20 | **91 cells, +1.0…+2.0°** |
| `KF_ZW_PF2` | `0x703210` | 16×20 | 91 cells, +1.0…+2.0° |
| `KF_ZW_S_PF1` | `0x7030D0` | 16×20 | 91 cells, +1.0…+2.0° |
| `KF_ZW_S_PF2` | `0x702F90` | 16×20 | 91 cells, +1.0…+2.0° |
| `KF_ZW_UESP_PF1` | `0x702F04` | 14×10 | unchanged |
| `KF_ZW_UESP_PF2` | `0x702E78` | 14×10 | unchanged |
| `KF_ZW_VP_PF1` | `0x7072A8` | 16×20 | unchanged |
| `KF_ZW_VP_PF2` | `0x707168` | 16×20 | unchanged |
| `KF_ZWMIN_WSOT` | `0x706DEC` | 8×8 | unchanged |
| `KF_ZWMIN_KSOT` | `0x706E2C` | 8×8 | unchanged |

- X axis = **engine speed (1/min)**, Y axis = **load (%)**, Z = **ignition angle, signed
  int8, ×0.5 → crank degrees**, range −64.0…+63.5.
- The tuner raised advance by **1–2°**, on an identical 91-cell rectangle in all four main
  maps: load 9000–18000, 2250–6950 rpm. Light-load and low-rpm cells untouched.
- These are **base** ignition angle maps. Final commanded timing also depends on torque
  limits, knock control and per-cylinder corrections, which are **not** described here.

## Caveats that matter

- Map **names, dimensions, signedness, scaling and axis semantics are inherited from a
  Bosch A2L describing S15A-18.** This target is S15A-17, and no S15A-17 A2L exists
  locally, so none of that is proven for this image. What *was* verified against the
  target itself: addresses, byte spans, element width, axis array contents, and the
  tuned deltas.
- The **+1…+2° figures are a derived interpretation** — the raw, formula-independent fact
  is 91 changed cells per map with a byte delta of +2 or +4.
- 54.7% of the tuner's changed bytes remain unexplained.
- No claim is made that the Stage 2 calibration is safe, correct, or understood.

## ECU firmware — read this first

This repo **contains two ECU firmware images** in the repository root:

| File | Size | MD5 | SHA-256 |
|---|---|---|---|
| `10SW002828_iRom_ori` | 8,126,464 | `40c3a007f425858e11cd9b0961dd321b` | `fcc9b8f21127627302a0a96823848f9fb11ecc6385f06adf4957e4c591698356` |
| `10SW002828_iRom_stage2` | 8,126,464 | `251f649b87413ec83d01ef7a53bed2af` | `c544c1fd686e3f4edefd1d8d60b48464d434e02945a545044eac6745f4c8b8f5` |

These are **proprietary BMW/Bosch firmware** (EPK `R0C2J772B`, EPST `R0C9J772B`,
PST `S15A-17-11-490`, HW `10SW002828`), plus a third-party tune. They are published
here at the repository owner's decision so the analysis can be reproduced and the XDFs
tested. Check the licensing terms that apply to you before redistributing them. Anyone
forking this repo redistributes them too.

Verify the hashes before using them. Never flash these to an ECU.

## Not in this repo

`ref/`, `mgflasher-map-packs/` and the large reference zip remain excluded via
`.gitignore` — the reference packs total ~2.5 GB. Re-obtain them from their own
repositories if you need to re-run the build scripts.
