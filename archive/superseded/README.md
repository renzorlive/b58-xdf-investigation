# Superseded artifacts

Kept for the audit trail. **Do not use any of these.**

| File | Why it was superseded |
|---|---|
| `R0C2J772B_timing_candidates.xdf` | All 7 tables declared `indexcount=1` on the X/Y axes, so TunerPro rendered each as a **single cell**. Also labelled the data uint8 when it is signed int8, and its `702F18` table straddles two real maps. |
| `TIMING_CANDIDATE_AUDIT.md` | The audit of the above. Superseded by `out/IGNITION_TIMING_FINAL_VALIDATION.md`. |
| `IGNITION_TIMING_REINVESTIGATION.md` | Correctly identified the maps, but three quantitative claims were wrong: the tuning delta (~20x too high, from an indexing bug), a vacuous "+0.5 deg" check presented as corroboration, and an incorrect monotonicity claim. Corrected in `out/IGNITION_TIMING_FINAL_VALIDATION.md`. |
| `R0C2J772B_verified.xdf` | All 87 tables share `uniqueid 0x0` → 87 duplicate-uniqueid errors in TunerPro. Pre-existing defect, unrelated to timing. |
| `R0C2J772B_CANDIDATE.xdf` | Early candidate set, superseded by `R0C2J772B_manual_inspection.xdf`. |
| `R0C2J772B_CANDIDATE_axesclean.xdf` | Same, axis-cleaning variant. |

They remain in git history, so nothing is actually lost.
