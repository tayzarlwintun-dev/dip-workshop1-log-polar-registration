# Tests and Failures

| Date | Step | Test | Expected | Got | OK? | Notes |
|---|---|---|---|---|---|---|
| 2026-11-04 | 0 | Libraries installed in .venv | cv2, numpy, matplotlib, scipy | all present | yes | |
| 2026-11-04 | 1 | Make 4 test pictures | 4 png files + json | 4 files + json | yes | test1 has 17.9% black corners |
| 2026-11-04 | 1 | Overview figure readable | titles visible | titles cut off | no → fixed | added bbox_inches="tight" |
| 2026-11-04 | 1 | Add own test5 (90°, ×1.2, shift 10,10) | 5th picture appears | test5 made, sideways | yes | black bars top/bottom (tall photo turned 90°) |
| 2026-11-04 | 2 | test1 log-polar = original slid −30 rows | difference drops a lot | 27.4 → 2.0 | yes | rotation = slide |
| 2026-11-04 | 2 | test2 log-polar = original slid +17.5 cols | difference drops a lot | 24.9 → 6.5 | yes | zoom = slide right |
| 2026-11-04 | 2 | test3/4/5 with slide only | no match (shifted) | 29.9 / 42.7 / 50.2 | expected | center moved → need Step 4 |
| 2026-11-04 | 2 | Slide direction for counter-clockwise turn | +30 rows (first guess) | −30 rows | fixed | OpenCV y-axis points down |
| 2026-11-04 | 3 | test1 rotation found by itself | 30° | 30.00° (peak 0.85) | yes | |
| 2026-11-04 | 3 | test2 zoom found by itself | ×1.5 | ×1.487 (peak 0.70) | yes | 0.9% error |
| 2026-11-04 | 3 | test3/4/5 (shifted) | weak / wrong | 1–2° off, peak ~0.04 | expected | close by luck (small shift), not reliable |
| 2026-11-04 | 4 | test1/test2 (not shifted) with center search | same as Step 3 | correct, best spot = middle | yes | |
| 2026-11-04 | 4 | test3/4/5 (shifted) with center search | correct angle, zoom, shift | all correct, shift err 0.6–1.7 px | yes | peak 10× stronger than Step 3 |
| 2026-11-04 | 5 | Fixed photos line up with original | small difference, < 3 px off | all 5 lined up, 0.01–2.04 px | yes | |
| 2026-11-04 | 5 | "Pixels off" measure for test4 | ~2 px | 7.98 px (first try) | no → fixed | measured over whole photo; now only visible part |
| 2026-11-04 | 5 | Overview figure title | readable | overlapped row 1 | no → fixed | moved title up |
| 2026-11-04 | 6 | Optimizer improves Step 4 numbers | pixels off goes down | did not move (stopped after 1 look) | no → fixed | cv2.warpAffine rounds to 1/32 px; use map_coordinates |
| 2026-11-04 | 6 | test2/test4 improve | pixels off goes down | barely changed (2.04 → 1.94) | no → fixed | edge pixels slipping out; trim outer frame |
| 2026-11-04 | 6 | All tests after fixes | < 0.1 px off | 0.00–0.04 px | yes | test4 zoom exactly ×2.0000 |
| 2026-11-04 | 8 | Friend's method on my 5 tests | all correct | all correct, 0.26–1.49 px (before LM), ≤ 0.053 px after | yes | ~10 s/test vs mine ~4 s (same computer) |
| 2026-11-04 | 8 | Big shift, original's middle outside test photo (first try) | friend works | both fail | not fair → changed | friend needs the original's middle visible |
| 2026-11-04 | 8 | B1 friend-style (zoom 2.13, 201°, stretch), small shift | both < 0.1 px | mine 1.15 px, friend 0.001 px | partly | my optimizer: too little blur; blur 4,2,1,0.5 → 0.004 px |
| 2026-11-04 | 8 | B2/B3 big shift (~100 px) | mine fails, friend works | mine 303 / 1449 px, friend 0.001 / 0.009 px | expected | my search box is only ±60 px |
| 2026-11-04 | 9 | Rough search with phase correlation only (whole picture) | B2 found | B2 fails, true spot ranked ~2000th | no → fixed | sky/edges fool it → add cross-correlation judge |
| 2026-11-04 | 9 | Gray fill of black areas | B2 fixed | still fails | no | not the cause alone (kept anyway) |
| 2026-11-04 | 9 | Rough search with cross-correlation only | all found | B1, B3 fail | no → fixed | → 2 judges, 6 spots each |
| 2026-11-04 | 9 | Anchor = most detailed spot only | B3 better | B3 0.044 px but B1, C1 broke | no → fixed | repeating windows → 2 anchors + real-match check |
| 2026-11-04 | 9 | 2 anchors, skip if < 30 px apart | test4 OK | test4 failed | no → fixed | always try both |
| 2026-11-04 | 9 | Exact search every 2nd pixel | faster, same result | C1 (zoom ×3) failed | no → fixed | needle 1 px wide → every pixel, half-size clock |
| 2026-11-04 | 9 | New Step 4+6 on my 5 tests | all correct | Step 6: 0.00–0.02 px | yes | Step 4 alone 0.39–1.66 px |
| 2026-11-04 | 9 | Old vs new vs friend, 13 tests | new best | old 5/13, new 13/13, friend 10/13 | yes | new worst 0.044 px (B3) |
| 2026-11-04 | 9 | Optimizer alone from "no change" | gets lost | 42–15,058 px off | yes (expected) | paper's main point |
| 2026-11-04 | 10 | My Mac run of Steps 4–6 + Step 9 | same as cloud | same verdicts; Step 4 2.6–3.2 s per test | yes | tiny rounding differences only |
| 2026-11-04 | 10 | Clean final folder, Steps 1–7 run on their own | all work | all work, 5/5 + 8/8 under 0.1 px | yes | no friend code, no version 1 |
| 2026-11-04 | 10 | Step 7 figure titles | readable | bottom titles touched top pictures | no → fixed | more space between rows |
