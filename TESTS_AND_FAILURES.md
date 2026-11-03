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
