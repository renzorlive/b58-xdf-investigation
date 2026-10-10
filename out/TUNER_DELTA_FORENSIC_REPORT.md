# TUNER_DELTA_FORENSIC_REPORT

Read-only forensic comparison of `10SW002828_iRom_ori` (original, bench read) against
`10SW002828_iRom_stage2` (tuner Stage 2 image), same vehicle/ECU workflow.

**Read-only constraint verified.** No BIN or XDF was modified, patched, renamed,
regenerated, flashed, or cleaned up. Two files written by this pass:
`out/TUNER_DELTA_FORENSIC_REPORT.md` and `out/tuner_delta_regions.csv`.
Both BIN hashes are identical to every previously recorded baseline.

---

## 1 — File identity

| File | Size | MD5 | SHA-256 |
|---|---|---|---|
| `10SW002828_iRom_ori` | 8,126,464 | `40c3a007f425858e11cd9b0961dd321b` | `fcc9b8f21127627302a0a96823848f9fb11ecc6385f06adf4957e4c591698356` |
| `10SW002828_iRom_stage2` | 8,126,464 | `251f649b87413ec83d01ef7a53bed2af` | `c544c1fd686e3f4edefd1d8d60b48464d434e02945a545044eac6745f4c8b8f5` |

Sizes equal; MD5s match the recorded baseline from `FINAL_FORENSIC_AUDIT.md`,
`CHANGE_INVENTORY.md` and `R0C2_TARGET_COMPATIBILITY_AUDIT.md`. **Both files unchanged.**

Target identifiers confirmed in the original image: EPK `R0C2J772B` (`0x08E526`,
`0x08E531`, `0x707C9E`, `0x707CA9`), EPST `R0C9J772B` (`0x6BFE36`, `0x7BFEA0`),
PST `S15A-17-11-490` (`0x6BFE3C`).

---

## 2 — Difference mask, recomputed and reconciled

```
changed bytes recomputed directly from the two BINs : 3,821
changed bytes inside out/changed_bytes_inventory.csv spans : 3,821 / 3,821
changed bytes outside inventory spans                        : 0
per-region counts agree with the CSV                         : True
inventory total == recomputed mask                           : True
RECONCILED                                                  : True
```

**No discrepancy.** Every changed byte falls inside exactly one inventory region, and each
region's recorded count equals the count recomputed from the mask. The earlier figures
(3,821 changed bytes in 89 regions) are reproduced exactly.

---

## 3–4 — Per-region classification and definition linkage

`out/tuner_delta_regions.csv` — 89 rows, one per changed region, each with start/end,
span, changed count, per-byte original and Stage-2 hex, changed-only hex, overlapping
definitions, counts inside cells/axes/probable ranges, and an evidence-limitation column.

| Category | Regions | Changed bytes | % |
|---|---:|---:|---:|
| `VERIFIED_DATA_CELL` | 12 | 1,082 | 28.32 % |
| `CELL_AND_AXIS` | 2 | 418 | 10.94 % |
| `PROBABLE_TABLE` | 3 | 216 | 5.65 % |
| `VERIFIED_AXIS` | 2 | 11 | 0.29 % |
| `UNIDENTIFIED_IN_CAL_BLOCK` | 69 | 2,090 | 54.70 % |
| `OUTSIDE_CAL_BLOCK_HIGH` | 1 | 4 | 0.10 % |
| **Total** | **89** | **3,821** | **100 %** |

Regions with demonstrable definition overlap:

| Region | Range | Bytes | Overlapping definitions |
|---|---|---|---|
| 7 | `0x6CD31E-0x6CD3A1` | 132 | `KF_FMS_HFMPL_MN`, `KF_FMS_HFMPL_MX` |
| 12 | `0x6D9DC6-0x6D9DF5` | 48 | `KL_RF_MAX`, `KL_RF_MAX_UESP` |
| 13 | `0x6DA1E6-0x6DA209` | 36 | `KL_LAMX` |
| 14 | `0x6DDBE6-0x6DDC27` | 59 | `BMWtchdiag_pct_WgPHi_M`, `…WgPLo_M` |
| 16 | `0x6DE03A-0x6DE0B3` | 114 | `BMWtchsp_rat_p_CmprMax_M`, `…CmprPmp_T` |
| 19 | `0x6E68DC-0x6E68FF` | 36 | `BMWtqe_tqc_FlApplStgNorm_T` |
| 24 | `0x6EEEE2-0x6EEF43` | 90 | `BMWchas_lam_InjMpl_M` |
| 25 | `0x6EEFAA-0x6EF00B` | 90 | `BMWchas_lam_InjMplThr_M` |
| 33 | `0x6F8CA0-0x6F8D2F` | 96 | `KL_MD_K_MAX_VL/ VL_HS / RST / RST_HS / BST / BST_HS` |
| 34 | `0x6FA260-0x6FA45D` | 301 | `KF_LABAS_2` |
| 36 | `0x6FB116-0x6FB181` | 72 | `KF_FMS_DKPSRPL_MN`, `KF_FMS_DKPSRPL_MX` |
| 38 | `0x6FC899-0x6FC8A1` | 8 | `K_EDA_MD_ANZ_BS_SCAL_CODE`, `K_EDA_P_ANZ_SPORT_BS_SCAL_CODE` |
| 5 | `0x6C9CAE-0x6C9D5B` | 52 | `KF_EDA_ANZ_SPORT_MDK_IST` (+ its x-axis) |
| 35 | `0x6FA4C4-0x6FA6EF` | 366 | `KF_LABAS_1`, `KF_LABAS_2` **and their y-axis** |
| 3 | `0x6C54CD` | 1 | `KL_MDRED_NKW` x-axis |
| 18 | `0x6E2EAC-0x6E2EB5` | 10 | `KF_MDIOP_1_TQE` x-axis |
| 22 | `0x6EED12-0x6EED73` | 90 | `BMWchas_lam_InjSng_M` (PROBABLE) |
| 23 | `0x6EEDDA-0x6EEE3B` | 90 | `BMWchas_lam_InjSngThr_M` (PROBABLE) |
| 39 | `0x6FCA5C-0x6FCA95` | 36 | `BMWchas_st_OpmBasc_M` (PROBABLE) |

**Evidence boundary.** Per `R0C2_TARGET_COMPATIBILITY_AUDIT.md`, **zero** definitions are
verified for the exact `R0C2J772B` / `S15A-17` target. What the linkage above establishes is
**address overlap only**: the changed bytes fall inside address ranges that a candidate
definition occupies, and those ranges are byte-proven against an **S15A-18** reference. The
Bosch names attached to them are inherited, not proven for this image. Data-cell evidence
and map-name confidence are kept in separate columns of the CSV for exactly this reason.

---

## 5 — What kind of regions changed

### 5a. No executable code was modified — proven

```
changed bytes below 0x6C0000 : 0
```

Every one of the 3,821 changed bytes lies at or above `0x6C0000`. The entire code and
data region `0x000000`–`0x5FFFFF` is bit-identical. **The tuner changed calibration only;
no code, no boot blocks, no data outside the calibration area.**

### 5b. One region lies outside the calibration block

Region 89, `0x7BFCFC`–`0x7BFCFF`, 4 bytes:

```
ori    0x7BFCFC: FF AA 0F 5A
stage2 0x7BFCFC: AD 63 60 DD
```

Structural context:

```
0x7BFCF0  ori    ffffffffffffffffffffffffff aa0f5a
         stage2 ffffffffffffffffffffffffff ad6360dd
0x7BFD00  ori    0d0000344846090500000040e00f94bf      <-- identical in both
```

The 4 changed bytes sit in a run of erased `FF` padding, immediately before a fixed
16-byte block that is **identical** in both images. That position and size are
**consistent with a checksum or signature field** stored alongside the calibration, and the
calibration-area byte sum does differ between the two images
(`28,708,465` → `28,820,676`).

**This is a structural hypothesis, not a proven identification.** I have not computed a
CRC over any candidate range and confirmed it reproduces either value, and I am not
claiming the tuner computed a checksum, nor that the field validates. It is recorded as
"changed, 4 bytes, outside the calibration block, in padding, ahead of a fixed block".

### 5c. Axes were modified, not only data cells

Two regions touch axes only, and region 35 touches data cells *and* an axis:

- Region 35 (`0x6FA4C4-0x6FA6EF`, 366 bytes) spans `KF_LABAS_1` / `KF_LABAS_2` data cells
  **and** their shared y-axis at `0x6FA6CE` (17 points, rescaled 2000→1600 … 18000→14400).
- Regions 3 and 18 touch only an x-axis (1 and 10 bytes).

So 11 bytes fall in axes with no cell overlap, and 52 more sit in a region where a
definition's cells and axis both changed. **Breakpoints were not left untouched**, which
corrects an earlier statement in `INVESTIGATION_REPORT.md`.

### 5d. Correction to a previously reported status

**`0x6FB116` is no longer unresolved.** I previously listed it as having no definition in
any local file. That was based on the superseded SP11-era search. Region 36
(`0x6FB116-0x6FB181`, 72 changed bytes) demonstrably overlaps `KF_FMS_DKPSRPL_MN` and
`KF_FMS_DKPSRPL_MX`. It is now classified `VERIFIED_DATA_CELL` on address-overlap evidence.

---

## 6 — Preserved unresolved regions

| Address | Region | Status | Changed |
|---|---|---|---|
| `0x70318B` | 42 | **unidentified** — ignition-scale block, no Bosch name assigned | 91 |
| `0x7032CB` | 43 | **unidentified** — same | 91 |
| `0x70340B` | 44 | **unidentified** — same | 91 |
| `0x7311B4` | 85 | **unresolved** — no definition reaches it | 288 |
| `0x730A8C` | 83 | **unresolved** — no definition reaches it | 128 |
| `0x6F1BA0` | 26 | **unresolved** — no definition reaches it | 44 |
| `0x6F7F2E` | 30 | **unresolved** — 6 × 1×12 structure only | 144 |

Largest unidentified regions: `0x7311B4` (288), `0x6F7F2E` (144), `0x730A8C` (128),
`0x6F6F4E` (117), `0x6F7039` (113), then the four 91-byte blocks at `0x70304B`/`0x70318B`/
`0x7032CB`/`0x70340B` spaced exactly 320 bytes apart.

---

## 7 — What is proven, and what is not

### Tier 1 — Facts proven by direct comparison of the two BINs
- 3,821 bytes differ, in 89 regions, reconciled exactly against the inventory.
- No byte below `0x6C0000` changed → **no code or boot data modified**.
- 4 bytes at `0x7BFCFC` lie outside the calibration block.
- 11 changed bytes fall in breakpoint axes; one 366-byte region spans both cells and an axis.
- Every per-region offset, count, and before/after hex is in `out/tuner_delta_regions.csv`.

### Tier 2 — Structural matches to the S15A-18 reference
- 1,500 changed bytes fall in address ranges occupied by candidate definitions
  (1,082 cell-only, 418 cell+axis, 11 axis, 216 probable-table).
- Those ranges are byte-proven against an `R0C2J8B2B` / `S15A-18-03-510` image, which is a
  **different S15 sub-revision** from the target's `S15A-17-11-490`.
- Map-set membership demonstrably differs between those revisions (the ignition maps).

### Tier 3 — Probable map interpretations
- The six `KL_MD_K_MAX_*` curves are the best-attested: A2L-identified, byte-identical in
  both data and axes, unit `Nm`. Even so, they are torque **setpoints**; no delivered
  torque or boost figure follows from them.
- The `PROBABLE_TABLE` regions (22, 23, 39) rest on byte-verified placement with
  non-corroborating axes and were deliberately withheld from the candidate.

### Tier 4 — Unresolved
- **2,090 bytes (54.7 %) in 69 regions**, including all seven preserved regions above.
- No interpretation is available for any of them.

---

## Statement of limits

**I do not claim this Stage 2 calibration is safe, correct, complete, or understood.**

Nothing in this analysis establishes what any of the 2,090 unidentified bytes do, whether
the identified regions were changed correctly, or whether the combination is coherent.
Byte patterns alone were not used to infer boost targets, ignition advance, fueling,
torque delivery, or any safety property — and where decoded values look plausible, that
plausibility is explicitly *not* evidence. The evidence-linking column in the CSV records
address overlap only; the Bosch names beside it are inherited from a software sibling and
carry no target-specific proof.

The single artifact that would materially change these conclusions is a stock BIN from an
ECU reporting `R0C2J772B` / `S15A-17-*`. Absent that, the residual uncertainty is *which
software this image is*, not how to read the bytes.