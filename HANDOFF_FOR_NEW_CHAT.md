# Handoff for a New Chat – READ THIS FIRST

This file tells a new Claude chat everything about this project, so it does not need to
re-read all the code (saves tokens). For more detail: `REPORT_NOTES.md` (full results),
`JOURNAL.md` (step-by-step history), `QUESTIONS_AND_ANSWERS.md` (simple explanations).
Only open the `.py` files if you really need a code detail.

---

## 1. About me and how to help me

- I'm Tayzar, a master's student (TGGS, Digital Image Processing course). MacBook Air, VS Code.
- **Explain very simply, step by step, with examples and pictures. Avoid technical words**
  (I got very confused by words like "unrolling", "peak", "shift" without examples).
  Good explanations that worked: house/tree/car example, "clock picture" (what you see
  around a dot, written in a row), 8 colored boxes that slide when the photo turns,
  tuning a radio, walking blindfolded downhill.
- I don't write code myself. Claude writes it, tests it, saves it into my folder, explains
  what it does BEFORE I run it, and tells me what I should see. I run it and paste the output.
- After each step: update the notes files (`JOURNAL.md`, `TESTS_AND_FAILURES.md`, `IDEAS.md`,
  `README.md`, `QUESTIONS_AND_ANSWERS.md` when I ask questions) and give me the git commands.
- Go one step at a time and wait for me.

## 2. The project in one paragraph

Workshop 1: **image registration with the log-polar transform**, based on the paper by
G. Wolberg & S. Zokai, *"Robust Image Registration Using Log-Polar Transform"* (+ lecture
slides "1.Image Registration"). The teacher gave no instructions, so I chose the steps myself.
Goal: picture 2 is the same scene **turned, zoomed and moved**; the program finds those
3 amounts by itself and puts picture 2 back on top of picture 1. It does NOT find
differences between pictures – it only lines them up.

Folder: `.../TGGS_1st_semester/Digital_image_processing_by_Wannida_Sae-tang/Workshop/Workshop 1/Workshop_1_project`
Python 3.14 in `.venv` (opencv-python 5.0, numpy, scipy, matplotlib). Git repo, branch `main`.
graphify is installed with a git hook (output `graphify-out/`, ignored in git).

## 3. Files

| File | What it does |
|---|---|
| `images/original.jpg` | Bangkok skyline photo, 418 × 625 px |
| `step1_make_test_images.py` | makes 5 test photos with KNOWN turn/zoom/shift → `images/generated/`, answer key `results/test_cases.json` |
| `step2_log_polar.py` | log-polar ("clock picture") of each photo + proof that turn = slide down, zoom = slide right |
| `step3_find_rotation_scale.py` | phase correlation finds the slide → turn + zoom (only works without shift) |
| `step4_find_shift.py` | searches many centers in the original, keeps best peak → turn + zoom + shift |
| `step5_align_and_overlay.py` | puts test photos back (`images/aligned/`), red/cyan overlay before vs after |
| `step6_optimizer.py` | bonus: Levenberg–Marquardt fine-tuning of 6 affine knobs (SSD), like the paper (v2: blur 4→2→1→0.5) |
| `step8_compare_with_friend.py` | my OLD method (v1) vs friend's, on my tests + friend-style tests |
| `step9_old_vs_new.py` | old (v1) vs new (v2) vs friend on 13 tests |
| `friend_version/` | copy of friend's `registration.py`, `demo_tools.py` |
| `COMPARISON_WITH_FRIEND.md`, `IMPROVEMENTS.md` | comparison and version-2 explanation |
| `results/*.json`, `results/*.png` | all numbers and figures |
| `REPORT_NOTES.md` | report skeleton with all tables, figures, limits, conclusion |

## 4. Test cases (answer key)

Recipe (Step 1): rotate + zoom around the picture middle (209, 312.5) with
`cv2.getRotationMatrix2D(center, angle, scale)`, then add the shift. Positive angle =
counter-clockwise. Shift +x = right, +y = down.

| Test | Turn | Zoom | Shift (x, y) |
|---|---|---|---|
| test1 | 30° | ×1.0 | (0, 0) |
| test2 | 0° | ×1.5 | (0, 0) |
| test3 | 45° | ×1.5 | (20, −15) |
| test4 | 135° | ×2.0 | (−25, 30) |
| test5 | 90° | ×1.2 | (10, 10) (my own test) |

## 5. Method and key settings

- **Step 2:** `cv2.warpPolar(..., cv2.WARP_POLAR_LOG)`, grayscale, 360 rows (1 row = 1°) ×
  256 columns, center = picture middle, max radius 375.9 px (half diagonal).
  Counter-clockwise turn → slide UP (−rows), because OpenCV's y-axis points down.
- **Step 3:** own phase correlation with NumPy FFT, Hanning window on columns, parabola
  sub-pixel fit. turn = −dy/360·360°, zoom = exp(dx·log(R)/256). "Peak" = confidence (1 = perfect).
- **Step 4:** TEST photo's log-polar around its middle is fixed; search centers in the
  ORIGINAL within ±60 px (look radius 180 px); coarse every 4 px (961 spots) then fine ±4 px
  (81 spots); best peak wins. Shift = −zoom · rotate(spot − middle). ~1.7 s per test on my Mac.
- **Step 5:** same matrix, applied with `cv2.WARP_INVERSE_MAP`. Overlay: original = red,
  fixed test = cyan; gray = lined up. "Pixels off" measured only on visible pixels.
- **Step 6:** `scipy.optimize.least_squares(method="lm")` on 6 knobs (a1..a6), residual =
  brightness difference, blur σ = 2 then 1, exact bilinear sampling with
  `scipy.ndimage.map_coordinates`, outer frame trimmed by 6 px.

## 5b. Version 2 of Step 4 (current, Step 9)
Whole-picture search: gray-fill + 200 px frame; rough search on 4× smaller copy (90×64 log-polar,
batched scipy rfft2), two judges (cross-correlation + phase correlation) × 6 spots; every pixel
±5 px with 180×128 log-polar; final ±1 px with 360×256. Two anchors (test middle + most-detailed
spot), keep the one whose put-back picture matches best (NCC). shift = anchor − middle − L(spot − middle).
Old version kept as `find_turn_zoom_shift_OLD`. Results v2: 13/13 tests < 0.1 px (old 5/13,
friend 10/13); ~8 s per test on cloud (old ~4 s). Table below = version 1.

## 6. Final results (version 1)

| Test | Step 4 found (turn, zoom, shift) | Pixels off Step 4 | Pixels off Step 6 |
|---|---|---|---|
| test1 | 30.00°, ×1.000, (0, 0) | 0.01 | 0.00 |
| test2 | 0.02°, ×1.493, (0, 0) | 0.64 | 0.04 |
| test3 | 44.71°, ×1.504, (20.3, −15.9) | 0.93 | 0.00 |
| test4 | 135.10°, ×1.961, (−23.5, 29.2) | 2.04 | 0.01 |
| test5 | 89.87°, ×1.201, (9.6, 9.6) | 0.56 | 0.02 |

- Step 3 alone (no center search): exact for test1/test2 (peaks 0.85 / 0.70), but shifted
  tests had peaks only ~0.03–0.04 and 1–2° errors.
- Step 4: all 5 correct (angle ≤ 0.29°, zoom ≤ 1.93%, shift ≤ 1.7 px).
- Step 6: all 5 within 0.05 px; correction matrices near identity, like the paper.

Bugs fixed (details in `JOURNAL.md`): turn direction sign; "pixels off" measured on invisible
area; `cv2.warpAffine` rounds to 1/32 px so the optimizer saw no change (→ `map_coordinates`);
edge pixels blocked zoom changes in the optimizer (→ trim outer frame).

Differences from the paper: we search centers in the original (paper crops reference center
and searches the other image); phase correlation instead of plain cross-correlation; coarse grid
instead of image pyramid; synthetic test photos (paper used real photos).

## 7. DONE: compare with my friend's work (see `COMPARISON_WITH_FRIEND.md`, Step 8)

Summary: same idea, both Python. Friend = cross-correlation + searches the WHOLE test photo
(works for big shifts, ~2.5× slower); mine = phase correlation + ±60 px box (fails for
shifts > 60 px). Both ≤ 0.06 px after LM on my 5 tests. Friend's blur steps (4,2,1,0)
make the optimizer more robust. Original task text below.

### Original task

I will upload my friend's version of the same workshop. Please:
1. Read this file first (don't re-read my code unless needed).
2. Look at my friend's work and explain **in simple words with examples** what is
   **the same** and what is **different**. Useful things to compare:
   - Language / tools (Python or MATLAB? which libraries?)
   - Which steps they did (test pictures? log-polar? find turn+zoom? find shift? optimizer?)
   - How they find the slide (cross-correlation, phase correlation, something else?)
   - How they handle the shift (center search like the paper, Fourier–Mellin, or not at all?)
   - Log-polar settings (size, center, max radius), test cases, photo used
   - Accuracy (how close to the true answers) and speed, if they report it
   - Whether they used the optimizer (Levenberg–Marquardt) or not
   - What they explain or show better than me, and what I did that they didn't
3. If useful, run their code on my test photos (or mine on theirs) to compare fairly.
4. Put the comparison in a new file (e.g. `COMPARISON_WITH_FRIEND.md`), update the notes,
   and give me the git commands.
