# Workshop 1 – Image Registration with the Log-Polar Transform (final version)

Digital Image Processing course (TGGS, 1st semester) – Tayzar Lwin Tun.
Based on: G. Wolberg & S. Zokai, "Robust Image Registration Using Log-Polar Transform".

## Goal
Line up two pictures of the same scene when the second one is
**rotated, zoomed and shifted**. The program finds those three amounts
automatically, then puts picture 2 back on top of picture 1.

## Result
- My 5 test photos: all lined up within **0.02 px** (after the optimizer).
- 8 harder photos (paper-style turn 201° + zoom ×2.13 + stretch, zoom up to ×3, moves up to 192 px):
  all within **0.044 px**.
- Zoom range: works from ×0.5 to ×2 (×3 only sometimes); fails at ×4+ and ×0.35- (see `step8_zoom_limits.py`).
  A test-only experiment reaches ×0.35 – ×5 (see `experiments/zoom_fix/`, main method unchanged).
- Compared with my old version 1 and my friend's version on 13 photos:
  old 5/13, friend 10/13, **this final version 13/13** (see `IMPROVEMENTS.md`).

## Steps (scripts)
| Script | What it does |
|---|---|
| `step1_make_test_images.py` | makes 5 test photos with a KNOWN turn / zoom / shift |
| `step2_log_polar.py` | log-polar ("clock picture") + proof: turn = slide down, zoom = slide right |
| `step3_find_rotation_scale.py` | finds turn + zoom by itself (only works without shift) |
| `step4_find_shift.py` | **final search**: whole picture, 2 judges, 2 anchors → turn + zoom + shift |
| `step5_align_and_overlay.py` | puts the test photos back, red/cyan overlay |
| `step6_optimizer.py` | Levenberg–Marquardt fine-tuning of 6 numbers (like the paper) |
| `step7_hard_tests.py` | 8 hard test photos (B0–B3 paper-style, C1–C4 extra) with Steps 4 + 6 |
| `step8_zoom_limits.py` | how far can we zoom? ×0.25 … ×10 → works ×0.5 – ×2 |
| `experiments/zoom_fix/zoom_fix_test.py` | TEST ONLY: zoom guesses + swap photos → works ×0.35 – ×5 |

(The journal uses its own step numbers: "Step 7" there = report notes, Steps 8–9 = comparison
and improvement. The old version 1 and the comparison scripts are in the git history.)

## Documents
- `REPORT_NOTES.md` – everything for the report (method, tables, figures, limits)
- `IMPROVEMENTS.md` – what changed in the final version, old vs new vs friend vs paper
- `COMPARISON_WITH_FRIEND.md` – my method vs my friend's (same / different)
- `JOURNAL.md` – what was done at each step
- `TESTS_AND_FAILURES.md` – tests and what went wrong
- `QUESTIONS_AND_ANSWERS.md` – my questions with simple answers
- `IDEAS.md` – ideas for later
- `HANDOFF_FOR_NEW_CHAT.md` – summary for a new Claude chat (read first)

## Folders
- `images/original.jpg` – the Bangkok photo; `images/generated/` – test photos; `images/aligned/` – put back
- `results/` – all numbers (`.json`) and figures (`.png`)

## How to run (Mac)
```bash
python3 -m venv .venv                 # only the first time
source .venv/bin/activate
pip install -r requirements.txt       # only the first time
python step1_make_test_images.py
python step2_log_polar.py
python step3_find_rotation_scale.py
python step4_find_shift.py            # ~3 s per test on a MacBook Air
python step5_align_and_overlay.py
python step6_optimizer.py
python step7_hard_tests.py            # ~1-2 min
python step8_zoom_limits.py           # ~2-4 min
```

## Tools
Python 3.14, OpenCV, NumPy, SciPy, Matplotlib, VS Code, macOS.
Optional: graphify (code map for AI tools), settings in `.graphifyignore`.
