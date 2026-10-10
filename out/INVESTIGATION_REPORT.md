# Investigation report — B58 MG1CS003, 10SW002828

Target: `10SW002828_iRom_ori` / `10SW002828_iRom.Bin` (8,126,464 B each)
Read-only. No BIN was modified. `out/R0C2J772B_verified.xdf` is unchanged (87 tables).
All candidate definitions are written to separate files under `out/`.

---

## 1. ECU identification — RESOLVED from the BIN itself

No DIATX identifier is stored in the dump, but the two part numbers are. Both strings
appear at identical content in two places (`0x08E50D`, `0x707C85`), so these are
identification blocks, not incidental text.

| Offset | String | Meaning |
|---|---|---|
| `0x000164`, `0x010144` | `10SW002828` | hardware number |
| `0x08E50D` | `53/1/MG1CS003/11/MG1CS003_BX8_R0C2J772B//R0C2J772B///` | ECU + hardware/software ID |
| `0x07FE4B` | `MG1CS003_35UP` | hardware revision |
| `0x018034` | `#Hardware_DME8R0_SP15` | DME8 R0, platform SP15 |
| `0x7BFE3D` | `#DME__860#D1#DST#DME8.6-B58-SP15-M0-B30-G30-ECE-EU6c---_HGAG-LL-RL-AWD-PVL` | engine **B58**, SP**15**, B30/G30, **AWD**, PVL |
| `0x7BFE8C` | **`#EPST:R0C9J772B______#R0C9J772BCDDHX4`** | **calibration software P/N** |

**Key correction to the earlier working assumption.** The number read as "software
version" (`R0C2J772B`) is the *hardware/DME* identifier. The **EPST — the calibration
software family — is `R0C9J772B`**.

This matters because it means:

- The base XDF used, `00003076501103.xdf` = **R0C9J772B_3076-050_011_003**, matches the
  EPST **exactly**. The earlier placement was correct for a reason stronger than
  "closest available".
- `R1C9J772B` (the mgflasher Gen 1 pack) is **not** the same identifier and was never
  treated as interchangeable. Section 4 quantifies exactly how it relates.
- The DIATX serial (`3076-xxx-xxx-xxx` form) is **not present in this dump**. Searches
  for `3076`, `00003076501103`, `011_003`, `_070_`, and the general DIATX pattern all
  returned zero hits. It cannot be recovered without a bench tool or the ECU's own
  diagnostic report.

### Reference pack provenance (from `ref/BMW-XDFs-master/B58gen1`)

| Stock dump | EPST | SP |
|---|---|---|
| `00003076501103_original.bin` | R1C9J8B3B | 11 |
| `00003076501D02_original.bin` | R1C9J8I2B | 11 |
| `000030765A3C06_original.bin` | R1C9JD06B | 11 |
| `00003081501102_original.bin` | R0C9J8B2B | 15 |
| `00003081501D04_original.bin` | R0C9J8I4B | 15 |
| `00007972000705_original.bin` | R1R96015B | – |
| **user** | **R0C9J772B** | **15** |

**No stock dump in the project matches the user's EPST.** The pack's XDF files and
`*_original.bin` files are named by DIATX but the paired dumps carry a *different*
EPST from the XDF filename. This is a defect in the pack, not in our method — and it
is why the offset had to be derived rather than assumed. SP15 dumps are the correct
family; of those, only the R0C9-prefixed ones are close.

---

## 2. Diff report (complete)

`out/diff_report.txt`, `out/diff_report.json` — all 3,821 changed bytes with
before/after values, grouped into **89 contiguous regions** (gap ≤ 64 B).

Summary: 3,821 changed bytes, all inside `0x6C0201`–`0x7BFCFF`; the entire
`0x000000`–`0x6C0200` and `0x7BFD00`–`0x7C0000` is byte-identical. Changes are
confined to the calibration block. One changed region sits outside calibration:
`0x7BFCFC-0x7BFCFF` (4 bytes), immediately after the identifier block — almost
certainly a checksum or signature, not a map.

Largest regions:

| Region | Span | Changed |
|---|---|---|
| `0x7311B4-0x731365` | 434 | 288 |
| `0x6F7F2E-0x6F7FBD` | 144 | 144 |
| `0x6F8CA0-0x6F8D2F` | 144 | 96 |
| `0x70318B-0x70320F` | 133 | 91 |
| `0x7032CB-0x70334F` | 133 | 91 |
| `0x70340B-0x70348F` | 133 | 91 |

---

## 3. Audit of the 87 accepted tables

All checks below are over the tables actually emitted in
`out/R0C2J772B_verified.xdf`.

| Property | Result |
|---|---|
| Tables | 87 |
| Element size | 60 × 16-bit, 27 × 8-bit |
| Datatype | 87 × uint (XDF datatype 0) |
| Byte order | big-endian (validated below) |
| Row/col both declared | 87 / 87 |
| Meaningful declared min/max | 87 / 87 |
| In-range check | 100 % of cells, all 87 |
| Cell bytes covered | 14,136 |
| Axis bytes covered | 2,366 |
| **Cell/axis overlap** | **0 bytes** — no byte is claimed as both data and breakpoint |
| Overlapping cell bytes within the set | 244 (shared arrays / aliased maps) — deduped in coverage accounting |
| Placement method | 87 × content-anchored axes; **0 × band-search** |

### Address convention
`user_address = xdf_address + delta`, with a per-table delta derived from that table's
own breakpoint arrays. No base-offset/region-relative indirection is used, and no
address falls outside the 8,126,464-byte file.

### Endianness — validated, not assumed
For `BMWchas_lam_InjSng_M` at `0x6EECAC`:
- Big-endian raw: `4076` → `3440`
- Little-endian raw would be `60431` → `55210`

Only the big-endian reading yields physically meaningful values. Confirmed.

### Lambda conversion — independently validated
The reference XDF applies `X * 0.0002441406 * 14.7`. Two readings:

| Raw | ÷4096 (lambda) | ÷4095 × 14.7 (AFR) |
|---|---|---|
| 4076 (stock) | **0.9951** | 14.63 |
| 3440 (tuned) | **0.8398** | 12.35 |

The XDF is not wrong — it displays **AFR**, and AFR/14.7 = lambda. But the map is
*named* "Lambda setpoint", so the display convention is misleading. Recommend
switching these maps to `X/4096` so they read as lambda. **This is a display
correction only; the stored bytes and the map's identity are unaffected.**

### Stage 2 changes, checked independently
`BMWchas_lam_InjSng_M`, 10×10, rows 0–4 = λ0.995, rows 5–9 (Y = 175–350 Nm) changed to
λ0.840. That is enrichment at high load and stoichiometric below it — correct Stage 2
behaviour, and the direction of the change is right. 20 of the 87 tables carry tuner
edits; the remaining 67 are stock in this file.

---

## 4. Coverage accounting (no double-counting)

Method: build the union of data-cell and axis spans for every accepted table, then
classify each changed byte exactly once.

```
PROVEN set (87 tables)
  cell-only bytes covered        14,136
  axis-only bytes covered         2,346
  bytes in BOTH cell and axis         0
  changed bytes in >1 table          53   (deduplicated)
  CHANGED EXPLAINED              1,699 / 3,821  =  44.5 %
  CHANGED UNEXPLAINED            2,122

+ ADDITIONAL anchored candidates (3 tables, section 5)
  CHANGED EXPLAINED              1,771 / 3,821  =  46.3 %

COMBINED
  changed bytes explained        1,771   (cell + axis, each counted once)
  changed bytes unexplained      2,050   (53.7 %)
```

Axis changes account for **0** changed bytes — **no breakpoint axis was altered by the
tuner**. That is consistent with a competent tune (breakpoints left alone, only cells
edited) and independently supports the cell/axis separation.

`out/coverage.json` lists every explained and unexplained byte address.

---

## 5. New findings from the second pack

`mgflasher-map-packs/XDFs/B48 B58 Gen 1/Generic/MetricUnits/R1C9J772B_3076-070_009_002.MetricUnits.xdf`
(711 tables). Recovered 79 anchor points from the 87 proven tables, spanning **27
distinct deltas** from `0x410C4` to `0x41724`. Anchored placements are only accepted
where the table's own axes validate at the interpolated delta.

**Cross-XDF consensus: 42 tables map to byte-identical addresses under both packs**
(e.g. `KF_LABAS_1` → `0x6FA45E`, `BMWchas_lam_InjSng_M` → `0x6EECAC`,
`KL_RF_MAX` → `0x6D9DDE`). Two independent packs, written by different authors,
agreeing exactly, is the strongest corroboration available offline.

### 5.1 Boost target — VERIFIED placement

Found by searching the user BIN directly for well-formed 12-point RPM arrays. Two
distinct arrays sit at `0x6F8D98` and `0x6F8DE0`/`0x6F8DF8`, giving a single consistent
delta **+0x410FA** across three maps simultaneously.

| Map | Bosch var | Data @ | Axis (RPM) @ | Dims | Scaling |
|---|---|---|---|---|---|
| Full-load curve | `KL_MD_K_MAX_VL` | `0x6F8CA0` | `0x6F8D98` | 1×12 | raw = bar |
| Boost curve half-step | `KL_MD_K_MAX_BST_HS` | `0x6F8CE8` | `0x6F8DE0` | 1×12 | raw = bar |
| **Boost curve** | **`KL_MD_K_MAX_BST`** | **`0x6F8D00`** | `0x6F8DF8` | 1×12 | raw = bar |

Axis at `0x6F8DF8`: `[1000, 1250, 1550, 2300, 3800, 4600, 5400, 5500, 5800, 6000, 6500, 7000]`
Axis at `0x6F8D98`: `[1000, 1250, 1300, 2500, 3500, 4500, 4750, 5000, 5500, 6000, 6500, 7000]`

Values:

```
KL_MD_K_MAX_BST  ori  300 300 300 310 320 310 300 295 280 270 230 150
                 mod  650 650 650 650 650 650 650 650 650 650 650 650   12/12 changed

KL_MD_K_MAX_VL   ori  500 500 500 500 500 500 500 500 500 500 500 500
                 mod  650 650 650 650 650 650 650 650 650 650 650 650   12/12 changed
```

**Confidence: address VERIFIED, identity PROBABLE.** The placement is solid — three
independent axes validate at one shared delta. But the *semantics need review before
tuning*: both curves went to a flat 650 across all RPM, which reads as a fixed
constant rather than a shaped boost curve. Two readings are consistent with the bytes
and I cannot separate them offline:
 (a) a flat 650 mbar (0.65 bar) low-boost / bypass curve, or
 (b) the tune tool writing a saturated "limit" value.

Do not adjust these on the strength of the XDF title alone.

### 5.2 Injection timing (not ignition) — PROBABLE

Distinguishing these explicitly, as requested:

| Map | Bosch var | Data @ | Dims | Changed | Function |
|---|---|---|---|---|---|
| Injection start angle, warm | `KF_PHA_H_B1_W` | `0x6CFFD4` | 12×10 | 36 | **injection timing** |
| Injection start angle, preventive (skid) | `KF_PHA_H_B1_SK_PRE` | `0x6D0144` | 12×10 | 36 | **injection timing** |
| Base lambda, bank 1 | `KF_LABAS_1` | `0x6FA45E` | 17×18 | 332 | fuel **quantity** (already verified) |

`Pha` = Phasenwinkel (start angle) and the unit is degrees of **crank angle for the
injector**, not spark advance. These are genuinely injection-timing maps and are
distinct from `KF_ZW_*` (Zündwinkel = ignition).

Confidence PROBABLE, not verified: both sit ~4,700–5,100 bytes from the nearest proven
anchor, i.e. extrapolated rather than interpolated, and neither has an independent
cross-pack address match.

### 5.3 Torque / load limiter saturation — PROBABLE

`0x6F7F2E-0x6F7FBD` — 144 contiguous bytes, **all 144 changed**, stock `30000` repeated
→ tuned `32767`. `0x7FFF` is the maximum of a 15-bit field. A uniform saturation of a
limiter map to its maximum is the signature of a limiter being disabled. Six identical
12-point RPM axes (`[1000, 1250, 1550, 2300, 3800, 4600, 5400, 5500, 5800, 6000, 6500, 7000]`)
sit at `0x6F8022`–`0x6F809A`, 24 B apart, immediately after — consistent with six maps
sharing one axis. Candidate identity: the `KF_MDIMAX_*` / `KL_MDIMAX_*` inner-torque
limitation family. **Unresolved** — not in any pack at the implied delta.

---

## 6. Ignition timing — UNRESOLVED (explicitly not claimed)

The main ignition map is **not identified**, and I am not going to force it.

What is known:
- `KF_ZW_PF1` / `KF_ZW_PF2` (base ignition angle path 1/2) exist in the mgflasher pack
  at `0x6C12F8` / `0x6C11B8`, **16×20, 8-bit, 640 B**, axes at `0x6AB33C` / `0x6AB27C`.
- `0x40E93` (= `0x70318B − 0x6C12F8`) sits inside the derived band.
- Three unexplained regions `0x70318B`, `0x7032CB`, `0x70340B` are spaced exactly
  **0x140 = 320 B** apart — the same spacing as `KF_ZW_PF2 → S_PF2 → S_PF1 → PF1` in
  the pack. Each has 91 changed bytes.
- Read as 8-bit values, the tuner added **+2 to +4** to the low-index rows of all three,
  in all 13 leading columns — consistent with adding ignition advance at part load.

Why it is not claimed:
- **No 16- or 20-point breakpoint array exists anywhere in `0x702C00-0x703700`.** The
  ignition map's axes must be present; they are not at the implied delta.
- The data shows an exact byte-repetition at offset +20, which is inconsistent with a
  16×20 row-major map. The row/column layout is therefore unresolved.

The +2…+4 pattern is suggestive but "looks like ignition" is precisely the plausibility
reasoning to avoid. Status: **UNRESOLVED — hypothesis only, deliberately excluded from
the verified XDF.**

---

## 7. What is proven, unknown, and next

**Proven**
- Hardware `10SW002828`, ECU `MG1CS003`, engine B58, SP15, B30/G30 AWD PVL, DME8.6.
- EPST `R0C9J772B` — matches the base XDF's identifier exactly.
- Calibration block layout is shared with R0C9J772B_3076-050_011_003 under a delta of
  `0x40AC2`–`0x413FE` (414 independently located breakpoint arrays; 2,364 B spread).
- 87 tables verified; 46.3 % of the tuner's changed bytes explained, no double counting.
- No breakpoint axis was modified by the tuner.

**Unknown**
- DIATX serial — not present in this dump, cannot be recovered offline.
- Main ignition timing map.
- What `650` in the boost curves means in the tuner's intent.
- Identity of the 0x6F7F2E saturation map.
- 2,050 changed bytes (53.7 %) remain unattributed.

**Highest-value next steps, in order**
1. **A stock dump with EPST R0C9J772B**, or the DIATX P/N from the bench tool. This would
   let content-anchoring run directly and collapse the ±1.1 KB sub-block drift, which is
   the single biggest source of ambiguity.
2. **Ask the tuner** which map files/labels were used. Even just the XDF filename pins
   the whole address space.
3. **Damos/A2L route**: the repo ships A2Ls for the same P/Ns; an A2L for R0C9J772B
   would give address + layout independently of XDF conventions.
4. Re-run `candidates3.py` against any new pack — it reuses the 87 proven anchors, so
   each new pack is placed automatically and cross-checked.

**Artefacts** (all read-only, nothing written back to the BINs)
```
out/R0C2J772B_verified.xdf      unchanged, 87 verified tables
out/diff_report.txt/.json       full 3,821-byte diff
out/verified_report.json        per-table evidence for the 87
out/coverage.json               explained / unexplained byte lists
out/candidates_anchored.json    anchored placements from the second pack
out/candidates_disambiguated.json  candidates rejected as ambiguous (156)
```

Candidate definitions were **not** merged into `out/R0C2J772B_verified.xdf`.