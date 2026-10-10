# CHANGE_INVENTORY

Read-only pass. **No BIN, XDF, or calibration was created, modified, patched or flashed.**
Exactly two files were added: this document and `out/changed_bytes_inventory.csv`.

---

## 1 — Axes-clean candidate validation

`out/R0C2J772B_CANDIDATE_axesclean.xdf` parsed independently (fresh reader, no project
imports). 71 tables.

### Remaining addressed axes — all valid

```
addressed axes in candidate : 97
addressed axes FAILING sanity (non-negative, <60000, strictly increasing) : 0
```

Every axis address still present was read out of the target BIN and validated. All 97
are well-formed breakpoint arrays.

### The 10 removed axis references are properly neutralised

| Table | Axis | `mmedaddress` | `indexcount` | `MATH` |
|---|---|---|---|---|
| `KL_NEL_TMOT` | x | absent | 1 | absent |
| `KF_EDA_ANZ_SPORT_MD_EM1_IST` | x | absent | 1 | absent |
| `KF_FTRANSVL` | y | absent | 1 | absent |
| `KF_HUBESTM` | y | absent | 1 | absent |
| `BMWtchdiag_pct_WgPHi_M` | x | absent | 1 | absent |
| `BMWtqe_tqc_FlApplStgNorm_T` | x | absent | 1 | absent |
| `KF_MD_RES_NST_KEY` | y | absent | 1 | absent |
| `KF_ST_RKBAS_VVT` | y | absent | 1 | absent |
| `KF_ST_RKBAS_GD` | y | absent | 1 | absent |
| `KL_ENA_NREG_DSC` | x | absent | 1 | absent |

**None implies misleading breakpoints or invalid editor behaviour:**
- `indexcount = 1` — the editor will draw a single implicit breakpoint, not a fabricated array.
- no `mmedaddress` — nothing is read from the binary, so no wrong values can surface.
- no `MATH` — the header `DEFAULTS` (identity) applies; no stray scaling.
- only `mmedelementsizebits="16"` and zero strides remain, which are inert without an address.

Residual element attributes present: `mmedelementsizebits="16"`,
`mmedmajorstridebits="0"`, `mmedminorstridebits="0"` — all no-ops without an address.

**6 tables lost both axes** (`KL_NEL_TMOT`, `KF_EDA_ANZ_SPORT_MD_EM1_IST`,
`BMWtqe_tqc_FlApplStgNorm_T`, `KF_MD_RES_NST_KEY`, `KF_ST_RKBAS_VVT`/`_GD`,
`KL_ENA_NREG_DSC`) and now display as maps with no breakpoint axis. That is the honest
outcome: no axis information is claimed, rather than wrong axis information.

**No removed address was restored.** No axis address was reintroduced anywhere.

---

## 2 — Reproducible change inventory

All 3,821 changed bytes classified exactly once. Byte-level evidence and semantic
identification are held in **separate columns** of the CSV.

| Classification | Changed bytes | % | Basis |
|---|---:|---:|---|
| `VERIFIED_CELL` | 1,458 | 38.16 % | byte-identical to SP15 stock dump **and** axes corroborate |
| `VERIFIED_AXIS` | 47 | 1.23 % | breakpoint bytes identical to SP15 reference |
| `PROBABLE` | 215 | 5.63 % | byte-verified, but axis failed corroboration → deliberately not emitted |
| `UNEXPLAINED` | 2,101 | 54.99 % | no definition in any local file reaches the address |
| **Total** | **3,821** | **100 %** | |

### No double counting — verified three ways

```
regions in CSV                                  : 89
sum of region changed_bytes column              : 3821
independently recomputed diff mask              : 3821
sum of per-byte classification totals            : 3821
NO DOUBLE COUNTING                              : True
```

`out/changed_bytes_inventory.csv` columns: `region, start, end, span, changed_bytes,
classification, reference, byte_level_evidence, semantic_identification, breakdown`.
The `breakdown` column gives the full per-class split within each region, so a
mixed region is not hidden behind its dominant label.

Region-level roll-up (a region is labelled by its majority class):
70 `UNEXPLAINED`, 14 `VERIFIED_CELL`, 3 `PROBABLE`, 2 `VERIFIED_AXIS`.

**Important:** the two inventory totals differ by design from earlier figures —
`PROBABLE` bytes are counted in their own class, not folded into `VERIFIED`. This keeps
the distinction between *byte-level* evidence and *semantic* identification, which is the
point of this pass.

---

## 3 — Software provenance for EPST `R0C9J772B`

Exhaustive search of the local tree:

| Search | Result |
|---|---|
| Filenames containing `772` | 4 XDF/A2L files, all **`R1C9J772B`** (R1C9, not R0C9) |
| Text content containing `R0C9J772B` | only my own generated files in `out/` |
| Binary content containing `R0C9J772B` | **only `10SW002828_iRom_ori` and `…_stage2`** (3 occurrences each) |

The string appears in **no** reference pack, **no** stock dump, and **no** metadata file
in this project. The only `J772B` software family available locally is `R1C9J772B`,
which is a **different EPST** and is not treated as equivalent.

**Exact missing artifacts** — any **one** of these unblocks further work:
1. A stock BIN read from an ECU reporting EPST `R0C9J772B` — enables content-anchoring
   and collapses the address uncertainty entirely.
2. The DIATX P/N for `R0C9J772B` (e.g. `R?C9J772B_3076-xxx_xxx_xxx`) as reported by a
   bench tool — keys the correct pack in the mgflasher repository.
3. Any XDF, A2L or DAMOS file generated for EPST `R0C9J772B`.
4. The XDF/A2L file the tuner actually used.

Absent these, no Bosch name is assigned to any unresolved region.

---

## 4 — Unresolved findings preserved

No further attempt was made to identify these, and none is claimed:

| Region | Status |
|---|---|
| `0x70318B`, `0x7032CB`, `0x70340B` | **unidentified** — ignition-scale blocks, no Bosch name assigned |
| `0x7311B4` | **unresolved** — no definition in any local file |
| `0x730A8C` | **unresolved** — no definition in any local file |
| `0x6FB116`, `0x6F1BA0` | **unresolved** — no definition in any local file |
| `0x6F7F2E` | **unresolved** — 6 × 1×12 curves saturated to 32767, structure only |

No inference of safety, correctness or intended function has been drawn from value
plausibility for any of these. **Unidentified is not the same as benign.**

---

## 5 — Integrity

| Artifact | MD5 | Size |
|---|---|---|
| `10SW002828_iRom_ori` | `40c3a007f425858e11cd9b0961dd321b` | 8,126,464 |
| `10SW002828_iRom_stage2` | `251f649b87413ec83d01ef7a53bed2af` | 8,126,464 |
| `out/R0C2J772B_verified.xdf` | `a9cf2244711a8b573ed94dbdff01ef10` | 141,733 |
| `out/R0C2J772B_CANDIDATE.xdf` | `fba37eadf02d1d12f1b7bca1a530b8fa` | 103,223 |
| `out/R0C2J772B_CANDIDATE_axesclean.xdf` | `aa01976c1d66047a9e92110ee39efe44` | 101,325 |

Both BIN hashes match the recorded baseline. The legacy verified XDF hash matches the
value recorded in `FINAL_FORENSIC_AUDIT.md`. No flash-ready calibration, `.bin`, `.hex`
or `.s19` file exists anywhere in the tree. Nothing was cleaned up; all prior artifacts
are intact.

---

## Verdict

**Verified.** 71 definitions with byte-level proof against an SP15 stock dump; 27 linear
conversion formulas, 59 cross-checked to A2L `COMPU_METHOD` with 6 documented unit
conversions; 97 addressed axes all structurally valid; 10 bad axis references removed and
properly neutralised. 1,505 changed bytes (39.4 %) are explained by the axes-clean
candidate.

**Unidentified.** 2,101 changed bytes (55.0 %) in 70 regions, plus 215 `PROBABLE` bytes in
tables withheld for failing axis corroboration. The ignition blocks and the four
unresolved regions carry **no** identification and **no** safety inference.

**Evidence needed to proceed.** A single artifact carrying EPST `R0C9J772B` — a stock BIN,
a DIATX P/N, an XDF/A2L/DAMOS file for that EPST, or the tuner's own definition file.
Nothing local provides it, and no amount of further analysis of the current files can
substitute for it: the remaining uncertainty is *which software variant this is*, not how
to read the bytes.