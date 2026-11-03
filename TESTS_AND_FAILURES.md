# Tests and Failures

| Date | Step | Test | Expected | Got | OK? | Notes |
|---|---|---|---|---|---|---|
| 2026-11-04 | 0 | Libraries installed in .venv | cv2, numpy, matplotlib, scipy | all present | yes | |
| 2026-11-04 | 1 | Make 4 test pictures | 4 png files + json | 4 files + json | yes | test1 has 17.9% black corners |
| 2026-11-04 | 1 | Overview figure readable | titles visible | titles cut off | no → fixed | added bbox_inches="tight" |
| 2026-11-04 | 1 | Add own test5 (90°, ×1.2, shift 10,10) | 5th picture appears | test5 made, sideways | yes | black bars top/bottom (tall photo turned 90°) |
