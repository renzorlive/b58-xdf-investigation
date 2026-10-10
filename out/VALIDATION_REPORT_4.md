# Validation pass — report #4

Baseline: `INVESTIGATION_REPORT_3.md`. Both BINs unchanged (md5 `40c3a00…` / `251f649…`).
`out/R0C2J772B_verified.xdf` unchanged (87 tables). `out/R0C2J772B_CANDIDATE.xdf`
regenerated: **71 tables, 0 audit problems**.

---

## 1 — Audit result: the candidate XDF FAILED and has been corrected

Auditing `out/R0C2J772B_CANDIDATE.xdf` against `out/per_table_audit.csv` raised
**301 problems** on the 68 tables it contained. Root cause:

> **Every conversion formula had been flattened to `X`.** The source SP15 XDF contains
> **82 distinct `MATH` equations**, including non-linear ones such as
> `1/(X*0.000011518903) * 80.11750567498999`. My report-3 generator emitted
> `equation="X"` unconditionally, so every non-identity map was being displayed at
> its raw stored value.

Every table was therefore wrong by its scaling factor. Examples:

| Map | Source formula | Was displayed as | Should be |
|---|---|---|---|
| `KF_LABAS_1` | `(X*0.0002441406)*14.7` | ×1 | AFR = λ×14.7 |
| `KL_NEL_TMOT` | ×0.392156862745 | ×1 | ×0.392 |
| `KF_FMS_HFMPL_MX/MN` | ×0.0078740157 | ×1 | ×0.00787 |

**Fixes applied to `regen_candidate.py`:**
- Conversion formula carried through verbatim from the source XDF (28 distinct formulas
  now present in the candidate).
- Axis element widths carried through (previously forced to 16-bit).
- Axis `MATH` equations carried through.
- Duplicates removed (2 tables were emitted twice).
- Full-precision scaling recorded in the CSV (was 6 sig-fig, causing false mismatches).

**Three additional findings from the audit:**
- 7 tables have data that is 100 % identical but whose **axes do not corroborate** at the
  same delta. Demoted VERIFIED → PROBABLE: `KL_T_IKAT_SOUND_MX`, `KL_NKW_SOUND_MX`,
  `KL_NKW_SOUND_MN`, `BMWchas_st_OpmBasc_M`, `KF_DZWT_PF2`, `BMWtqe_b_SptDet4NoiseAcvn_M`,
  `BMWtqe_b_Clu4NoiseDeac_T`.
- 0 duplicate Bosch names, **0 overlapping cell ranges**, 0 tables out of file bounds.
- Endianness confirmed `MSB_FIRST` (big-endian) on every emitted table, per both the XDF
  and the A2L `BYTE_ORDER` declarations.

Final audit: **71 tables, 0 problems.**

---

## 2 — K_MAX family: the A2L contradicts report #3. I was wrong about the units.

The DAMOS A2L `R0C9J8B2B_3081-080_017_002.a2l` is the authoritative source and gives:

```
/begin COMPU_METHOD lFwocba_tlxgpab_wmDuExd_NCRoa0o
    RAT_FUNC  "%6.3" "Nm"   COEFFS 0 1 0 0 0 1
/end COMPU_METHOD
```

**Unit is Nm, scaling is identity.** Report #3's "relative charge ratio K<1, ÷1000,
0.65 bar" reading was wrong and is retracted. Nothing in the source supports
interpreting 650 as a pressure of any kind.

The A2L also revealed the family is **six** curves, not two — six `CHARACTERISTIC`
blocks at consecutive 24-byte strides, each with its own axis:

| Bosch variable | Data (user) | Axis (user) | axis bytes = ref | Stock | Tuned |
|---|---|---|---|---|---|
| `KL_MD_K_MAX_VL_HS` | `0x6F8CA0` | `0x6F8D98` | yes | 500 Nm | **650 Nm** |
| `KL_MD_K_MAX_VL` | `0x6F8CB8` | `0x6F8DB0` | yes | 500 Nm | **650 Nm** |
| `KL_MD_K_MAX_RST_HS` | `0x6F8CD0` | `0x6F8DC8` | yes | 300 Nm | 300 Nm |
| `KL_MD_K_MAX_RST` | `0x6F8CE8` | `0x6F8DE0` | yes | 300 Nm | 300 Nm |
| `KL_MD_K_MAX_BST_HS` | `0x6F8D00` | `0x6F8DF8` | yes | 300 Nm | **650 Nm** |
| `KL_MD_K_MAX_BST` | `0x6F8D18` | `0x6F8E10` | yes | 485 Nm | **650 Nm** |

All six at delta **+0x3F9D0**, data and axis both byte-identical to the SP15 reference.
This also resolves the `VL`/`VL_HS` collision I reported in #3 as "indistinguishable" —
they are separate curves at `0x6F8CA0` and `0x6F8CB8`.

**What the tuner did:** raised the full-load and boost-curve torque ceilings from
500 Nm to 650 Nm, and flattened the `BST` taper (485 → 291 Nm) to a constant 650 Nm,
leaving the launch-control (`RST`) pair untouched. Read plainly: **a torque-limit
increase of ~30 %**, which is exactly what a Stage 2 tune does and exactly why the ECU
needed the torque model raised alongside it.

Axis input quantity is `Nkw_opt` (optimal-power operating point), unit `1/min`,
`MONOTONY STRICT_INCREASE`.

---

## 3 — Timing family: still excluded, and why

The A2L confirms the structure I hypothesised and adds detail:

```
/begin CHARACTERISTIC KF_ZW_S_PF2
   "Base ignition angle path 2 safe"   MAP   0x96C37C0
   AXIS_DESCR COM_AXIS Nkw ... 20 pts ... MONOTONY STRICT_INCREASE   PHYS_UNIT "1/min"
   AXIS_DESCR COM_AXIS NO_INPUT_QUANTITY ... 16 pts ... MONOTONY STRICT_INCREASE  PHYS_UNIT "%"
```

- **16 × 20 uint8 map** — structure confirmed independently of the XDF.
- Both axes **STRICT_INCREASE** in the source.
- Conversion: `aAwkuzc_BFpgCmb_tmDukma_q__aa0o` → `RAT_FUNC COEFFS 0 2 0 0 0 1`, i.e.
  **× 2, degrees**.

**Two problems keep them out:**

1. **The mirrored-orientation hypothesis is not supported.** Both axes are declared
   `STRICT_INCREASE`, and the axes I located in your BIN (`0x6EC536`, `0x6EC556`,
   `0x6EC5DE`…) are also strictly increasing. A genuine mirror would require a
   descending axis somewhere. The staircase difference is real but unexplained.
2. **The scaling does not reconcile.** Applying ×2 degrees to the *reference's own
   stock* bytes gives 104–160° for row 0 (`raw 52–80`). That is not a credible B58
   ignition map, so either the A2L's compu method or my assumption about which bytes
   are the map is wrong. I cannot close this offline.

**Identity also remains ambiguous**: nothing links a specific data block to a specific
axis pair once the orientation question is open. Per the standing instruction —
structure alone is not sufficient — **no ignition definition is emitted.**

---

## 4 — Largest unexplained regions: negative results

| Region | Span | Changed | Search performed | Result |
|---|---|---|---|---|
| `0x7311B4-0x731365` | 434 | 288 | all 399 `CHARACTERISTIC`s of the SP15 A2L + all 1116 XDF tables, delta 0x3F800–0x41800 | **no match** |
| `0x730A8C-0x730B1D` | 146 | 128 | same | **no match** |
| `0x6FB116-0x6FB181` | 108 | 72 | same | **no match** |
| `0x6F1BA0-0x6F1C1F` | 128 | 44 | same | **no match** |

The only hits for `0x7311B4`/`0x730A8C` were degenerate: `InjSys_nLowrThdCvo_C`, declared
**1×0** (a zero-cell map cannot cover a 434-byte region), and `IKCtl_FacKnockDet*` maps
landing at unrelated deltas. **No claim is made about these regions.** They remain the
largest single block of unexplained tuner activity.

Structurally `0x7311B4` shows repeating 6-value groups on a 514-step axis family
(`258, 772, 1286, 1800, 2314, …`), which resembles a load or temperature axis, but no
available reference defines anything there.

---

## 5 — Reconciling 73 / 43 / 71

These are three different sets and the counts are not comparable:

| Set | Count | What it is |
|---|---|---|
| SP15 byte-verified | 73 | Tables from the SP15 primary reference placed by 100 % byte match **and** a unique delta |
| Legacy byte-identical | 43 | Tables from the **superseded SP11** pack that happen to be byte-identical |
| **Candidate XDF emitted** | **71** | 65 SP15 + 6 A2L-only `KL_MD_K_MAX_*`, after demoting 7 with non-corroborating axes |

- **73 → 65**: seven SP15 tables were demoted for failing the axis-corroboration rule
  (§1). Their *data* is still 100 % identical, so they remain in coverage as PROBABLE.
- **6 added**: the `KL_MD_K_MAX_*` family exists only in the A2L, not the SP15 XDF.
- **The 43 legacy tables are not in the candidate XDF.** They come from an SP11
  reference that this audit has now shown to be unreliable (it produced 38 bad
  placements). They are retained in `out/R0C2J772B_verified.xdf` as historical evidence
  and counted in coverage, but they are not proposed for use.

### Coverage — deduplicated changed bytes

```
SP15 verified (73 tables)                  1,458
Legacy byte-identical (43 tables)          1,392
K_MAX family (6 tables, counted in SP15)      96
----------------------------------------------------------------
COMBINED, deduplicated                     1,904 / 3,821  =  49.8 %
Unexplained                                1,917
```

Corrections to earlier figures:
- `overlap sp15 & kmax = 144` bytes — the six K_MAX curves are already inside the SP15
  set's address span, so they must not be added twice.
- `overlap sp15 & legacy = 4,664` bytes of address space — this is *address overlap*, not
  changed-byte overlap, and is **excluded** from the percentage.
- Report #3 quoted 37.6 % for the SP15 set alone. That under-counted because it used the
  pre-demotion set and excluded the K_MAX family. 49.8 % is the deduplicated figure for
  everything currently evidenced.

Coverage is computed as `|changed ∩ (cells ∪ axes)|`, each byte counted once,
`cells ∩ axes = 0`.

---

## Deliverables

| File | Status |
|---|---|
| `out/R0C2J772B_CANDIDATE.xdf` | **regenerated — 71 tables, 0 audit problems, correct scaling** |
| `out/per_table_audit.csv` | 115 rows: 71 VERIFIED / 39 PROBABLE / 2 PARTIAL / 3 REJECT |
| `out/kmax_family.json` | six A2L-verified curves with byte-identity flags |
| `out/coverage_report4.json` | deduplicated coverage |
| `out/R0C2J772B_verified.xdf` | **unchanged**, 87 tables |
| `10SW002828_iRom_ori`, `…_stage2` | **unchanged** |

No flash-ready calibration was produced. No unresolved map was promoted.

## Open items
1. **Ignition maps** — blocked on the orientation/scaling contradiction (§3). Needs a
   second SP15 A2L for a different market (e.g. `R0C9J8D2B_3081-080_021_002`) to see
   whether the same discrepancy appears there; if not, the A2L is the outlier.
2. **`0x7311B4` / `0x730A8C`** — no definition exists in any available file. Most likely
   a code or datalog structure rather than a calibration map.
3. **`0x6F7F2E`** — 6 × 1×12 curves saturated to 32767, structure proven, identity still
   absent. The A2L contains no `KL_MD_K_MAX_*_STRG` characteristic at the matching delta.
4. **FUEL/IGNITION category coverage** — the highest-value tuning maps (main timing,
   lambda setpoints beyond the four found) remain unlocated.