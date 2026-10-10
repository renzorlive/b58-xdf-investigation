# Ignition-timing XDF — final delivery report

**Artifact:** `out/R0C2J772B_ignition_timing.xdf`
**MD5:** `622de33038350935c4c879e524b6b680`
**SHA-256:** `f34214b1914c9793b6ed6b41f2197e48c4eaf3810e6bcef785a0c08f2995be09`
**Size:** 25,882 bytes · **Tables:** 10 · **Validation:** PASS (see §3)

**Verdict:** PARTIALLY VALIDATED — suitable for exploratory display in TunerPro.
**Not** a validated tuning definition. Not sufficient to assert target-revision map
identity, units, or physical ignition timing. See §5.

This report is a companion to the artifact. No structural change was made to the XDF
to accommodate it.

---

## 1. Provenance — read this first

The MD5 recorded in the delivery request (`a638453788baef893e2ae29c9334e278`) **does
not match** the file currently at the artifact path. This was investigated rather than
silently reconciled. No file was modified as a result.

| # | Version | Bytes | Line endings | `<!DOCTYPE>` | MD5 |
|---|---|---|---|---|---|
| A | git `HEAD` blob (`a4d2ed30a53c`) | 25,284 | LF | **yes** | `a638453788baef893e2ae29c9334e278` ← **stated in request** |
| B | pre-repair workspace copy | 25,821 | CRLF | yes | (deleted / overwritten) |
| C | `test_c_full_fix.xdf` — **the file actually opened in TunerPro** | 25,884 | CRLF | no | `a3d113d22fea1524f535674aac5d8968` |
| D | **current artifact** | 25,882 | CRLF | no | `622de33038350935c4c879e524b6b680` |

Established facts:

- Version **A** is the blob at `HEAD` in commits `4f0083a`, `6f7f611`, `8765971`. It is
  the only version matching the MD5 in the request. It carries LF endings and a
  `<!DOCTYPE>` block.
- Version **B** was the uncommitted workspace file at the start of the repair session.
  It is byte-identical to **A** except that all 537 line endings are CRLF
  (25,284 + 537 = 25,821). It is the file that produced the TunerPro
  `Error Opening XDF / Expecting '<' CDATA` dialogs.
- Version **C** is the file the user opened and visually confirmed. It was **deleted
  during end-of-session cleanup**, so its MD5 could not be re-measured directly; the
  value above is reconstructed (§1.1).
- Version **D** is the current artifact.

### 1.1 Relationship between C and D

Before C was deleted, a character-level `difflib` comparison against **D** returned
exactly one opcode: an insertion of one CRLF at byte offset 38. That offset is the
position immediately after the XML declaration. Inserting CRLF at offset 38 into **D**
yields 25,884 bytes and MD5 `a3d113d22fea1524f535674aac5d8968`.

**D is therefore byte-identical to the user-inspected file C apart from one blank line**
between the `<?xml?>` declaration and the header comment. That blank line is
insignificant whitespace in the XML prolog. The reconstruction is reproducible:

```python
b = open('out/R0C2J772B_ignition_timing.xdf','rb').read()
cand = b[:38] + b'\r\n' + b[38:]     # -> md5 a3d113d22fea1524f535674aac5d8968
```

**Answer to "is the current file byte-identical to the user-inspected version": no — it
differs by exactly one CRLF, and is otherwise identical.** All map content, addresses,
axes, formulas and dimensions are unchanged.

### 1.2 Unresolved provenance question

Versions A and B both contain a `<!DOCTYPE>`; C and D do not. A is stated to have loaded
successfully, B is documented to have failed. The two differ only in line endings, so
**line endings cannot be ruled out as the actual trigger** for the failure — the DOCTYPE
was removed at the same time, confounding the two variables. C/D are confirmed working,
so this does not block delivery, but the root cause of the load failure is **not
established**. Anyone re-testing should note that removing the DOCTYPE and normalising to
CRLF happened together.

## 2. Changes applied in the repair session

Made to `build_ignition_xdf.py` so the fix survives a rebuild:

1. `<!DOCTYPE>` DTD no longer emitted.
2. `<XDFHEADER>` now opens with `<flags>0x1</flags>` and `<description>`.
3. `uniqueid` emitted as hex (`0x7001`…`0x700A`) rather than decimal (`"1"`…`"10"`).

Map content, addresses, axis pointers, `indexcount`, dimensions and the `X*0.5` formula
were **not** altered. Rebuild is deterministic (verified: same SHA-256 across runs).

The `<?xml version="1.0" encoding="utf-8"?>` declaration was deliberately **kept** —
the other XDFs in this repository carry it and load correctly.

## 3. Validation performed

Method: direct read of `10SW002828_iRom_ori` / `10SW002828_iRom_stage2` and parse of the
XDF. Read-only; no BIN was modified (hashes re-verified against `README.md`, §6).

| Check | Result |
|---|---|
| XML parse, well-formed | PASS — root `XDFFORMAT` version `1.80` |
| Table count | 10 |
| All Z spans within BIN (8,126,464 B) | PASS |
| X/Y axis `indexcount` == declared `mmedcolcount` | PASS (all 20) |
| Z dimensions `rowcount × colcount` == element count | PASS |
| Span overlap across all 30 declared spans (10 maps + 20 axes) | PASS — **0 overlaps** |
| X/Y axes strictly increasing (big-endian uint16) | PASS — all 20 |
| Map bodies distinct (six HIGH-confidence maps) | PASS |
| HIGH-confidence block contiguous | PASS — `0x702E78`–`0x703490`, 1,560 B, no gaps |
| `MATH` formula present on all Z axes | PASS — `X*0.5` |

### 3.1 Geometry

| Key | Conf | Z address | nx × ny | X axis | Y axis | Z span |
|---|---|---|---|---|---|---|
| `KF_ZW_PF1` | HIGH | `0x703350` | 20 × 16 | `0x6EC656` | `0x6EC596` | `0x703490` |
| `KF_ZW_PF2` | HIGH | `0x703210` | 20 × 16 | `0x6EC62E` | `0x6EC576` | `0x703350` |
| `KF_ZW_S_PF1` | HIGH | `0x7030D0` | 20 × 16 | `0x6EC606` | `0x6EC556` | `0x703210` |
| `KF_ZW_S_PF2` | HIGH | `0x702F90` | 20 × 16 | `0x6EC5DE` | `0x6EC536` | `0x7030D0` |
| `KF_ZW_UESP_PF1` | HIGH | `0x702F04` | 10 × 14 | `0x6EC5CA` | `0x6EC51A` | `0x702F90` |
| `KF_ZW_UESP_PF2` | HIGH | `0x702E78` | 10 × 14 | `0x6EC5B6` | `0x6EC4FE` | `0x702F04` |
| `KF_ZW_VP_PF1` | MEDIUM | `0x7072A8` | 20 × 16 | `0x6FA9B2` | `0x6FA96A` | `0x7073E8` |
| `KF_ZW_VP_PF2` | MEDIUM | `0x707168` | 20 × 16 | `0x6FA98A` | `0x6FA94A` | `0x7072A8` |
| `KF_ZWMIN_WSOT` | MEDIUM | `0x706DEC` | 8 × 8 | `0x6F99AE` | `0x6F996E` | `0x706E2C` |
| `KF_ZWMIN_KSOT` | MEDIUM | `0x706E2C` | 8 × 8 | `0x6F99BE` | `0x6F997E` | `0x706E6C` |

The Z axis deliberately has no `indexcount`; its geometry comes from `mmedrowcount` and
`mmedcolcount`. This matches the convention in the XDFs that load correctly.

### 3.2 Axis byte decoding (new observation)

Axis breakpoint arrays on this ECU decode as **big-endian** uint16. Under that reading
every axis is strictly increasing and physically plausible:

- X axes: `500…6950` 1/min (1000…3250 and 320…6528 for the narrower maps)
- Y axes: `1200…18000`, `3000…18000`, `1180…17000`

Read little-endian the same bytes yield non-monotonic garbage. This was a decoding
assumption in the validation script, not a defect in the XDF. Recorded here because it
is easy to get wrong when inspecting these arrays by hand.

### 3.3 Two MEDIUM maps share identical content

`KF_ZWMIN_WSOT` and `KF_ZWMIN_KSOT` are **byte-identical** in the stock image (both
`d7d1d2de…0d2`, 64 bytes). The stated finding "each map's bytes are unique in the target"
holds for the six HIGH-confidence maps, all six of which are distinct. It does **not**
extend to these two MEDIUM maps. Identical warm/cold minimum-timing limits are plausible
in stock calibration, but this was not investigated and is not confirmed either way.

## 4. Raw-byte facts

These are verifiable from the two BINs alone, with no reference image and no A2L.

- The six HIGH-confidence maps occupy a contiguous 1,560-byte block `0x702E78`–`0x703490`
  with no gaps.
- All six HIGH-confidence map bodies are mutually distinct.
- `KF_ZW_PF1`, `KF_ZW_PF2`, `KF_ZW_S_PF1`, `KF_ZW_S_PF2` each contain **exactly 91
  changed cells** relative to the stock read, at **identical cell indices in all four**
  maps (contiguous run, offsets 187–319).
- Raw signed-byte differences at those cells are **+2 (×31) or +4 (×60)**. No other
  delta value occurs.
- `KF_ZW_UESP_PF1`, `KF_ZW_UESP_PF2`, `KF_ZW_VP_PF1`, `KF_ZW_VP_PF2`, `KF_ZWMIN_WSOT`,
  `KF_ZWMIN_KSOT` show **zero** changed cells.
- Axis arrays are strictly increasing under big-endian uint16 decoding (§3.2).

> **Correction carried forward:** earlier analysis in this project reported per-map
> changes of "+27…+51 degrees" and a mean of "+38.8 degrees". Those figures came from an
> indexing bug and are **wrong**. The raw values are +2 and +4. Do not repeat the
> degree figures.

## 5. Inherited interpretations — NOT proven for S15A revision 17

The following come from the Bosch A2L `R0C9J8B2B_3081-080_017_002.a2l`
(project `MG1CS003_BX8_R0C2J8B2B`, version `R0C2J8B2B`), which describes **S15A
revision 18**. The target is **revision 17**. None of the following is confirmed for the
target revision:

- Map identity — that these `KF_ZW_*` maps are ignition timing at all.
- Symbol names and dimensions as applied.
- Signedness of the Z axis. Unsigned decoding gives implausible magnitudes for the
  `KF_ZWMIN_*` maps (176…241 → 88…120° minimum timing), which is a **plausibility
  argument, not target-specific proof**.
- The `×0.5` conversion. Under this assumption the observed +2/+4 raw deltas correspond
  to +1.0/+2.0 degrees, **but this is arithmetic on an inherited assumption and is not a
  measured timing change.**
- Units and semantics: X = engine speed 1/min, Y = air-mass/load.
- That the physical timing change caused by the tuner is any particular value.

Two further cautions that were established earlier and are repeated deliberately:

- **"The +0.5-degree increments corroborate the interpretation" is invalid.** Under the
  assumed ×0.5 conversion, half-degree increments are an automatic consequence of
  integer byte storage. They are not independent evidence.
- **Monotonicity does not independently prove signedness.**

### 5.1 Confidence tiers

- **HIGH (6 maps)** — structural and content correspondence: contiguous block, distinct
  content, axes resolving to plausible strictly-increasing ramps, and (for four of them)
  a coherent tuner's edit pattern.
- **MEDIUM (4 maps)** — `KF_ZW_VP_*` and `KF_ZWMIN_*` were located in a
  differently-laid-out region; the axis/data pairing rests on block-internal ordering
  rather than a single global offset translation.

## 6. Limitations and unverified items

- **The A2L could not be re-validated in this workspace.** `ref/` and
  `mgflasher-map-packs/` are `.gitignore`d and absent, so no `.a2l` file is present.
  All §5 inheritance rests on the recorded analysis in
  `out/IGNITION_TIMING_REINVESTIGATION.md`, not on re-checking the source.
- **"64 bytes either side match the reference" is unverified here** — the S15A-18
  reference image is likewise absent.
- **No S15A revision 17 A2L has been found**, locally or otherwise.
- The root cause of the TunerPro load failure is not established (§1.2).
- No XDF in this repository was ever loaded in TunerPro before the repair session; the
  other XDFs have been confirmed working by the user, but they have not been
  independently re-validated against the BIN here.

## 7. Binary integrity

Unchanged, re-verified at report time against the hashes recorded in `README.md`:

| File | Size | MD5 | SHA-256 |
|---|---|---|---|
| `10SW002828_iRom_ori` | 8,126,464 | `40c3a007f425858e11cd9b0961dd321b` | `fcc9b8f21127627302a0a96823848f9fb11ecc6385f06adf4957e4c591698356` |
| `10SW002828_iRom_stage2` | 8,126,464 | `251f649b87413ec83d01ef7a53bed2af` | `c544c1fd686e3f4edefd1d8d60b48464d434e02945a545044eac6745f4c8b8f5` |

## 8. Audit trail — retained, do not delete

- `out/R0C2J772B_timing_candidates.xdf` — **known bad.** Address-less axes,
  `indexcount=1`, renders as 1×1 tables. Superseded. Retained unaltered for audit.
- Earlier reports under `out/` are unmodified.
- `build_ignition_xdf.py` carries comments recording the `<!DOCTYPE>` removal and the
  reason for it.

## 9. Reproduction

```bash
python build_ignition_xdf.py        # regenerates the artifact deterministically
python tools/validate_xdf.py        # structural validation
```

Both BINs must remain unmodified. Do not flash or tune the ECU. Close TunerPro without
saving; TunerPro writes only when Save/Write-to-flash is invoked.