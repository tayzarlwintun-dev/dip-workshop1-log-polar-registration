# Workshop 1 – Image Registration with the Log-Polar Transform

Digital Image Processing course (TGGS, 1st semester).
Based on: G. Wolberg & S. Zokai, "Image Registration Using Log-Polar Transform".

## Goal
Line up two pictures of the same scene when the second one is
**rotated, zoomed and shifted**. We find those three amounts
automatically, then put picture 2 back on top of picture 1.

## Plan
| Step | What | Status |
|---|---|---|
| 0 | Set up folder, Python, git | done |
| 1 | Make test pictures with a known rotation / zoom / shift | to do |
| 2 | Log-polar transform | to do |
| 3 | Find rotation and zoom (cross-correlation) | to do |
| 4 | Find the shift (search for the center) | to do |
| 5 | Align picture 2 onto picture 1 and overlay | to do |
| 6 | Optimizer fine-tuning (bonus) | to do |
| 7 | Report notes | to do |

## Folder layout
- `images/` – input photos (`original.jpg`)
- `results/` – pictures and numbers the scripts make
- `JOURNAL.md` – what was done at each step
- `TESTS_AND_FAILURES.md` – tests we ran and what went wrong
- `IDEAS.md` – ideas for later

## How to run
```bash
source .venv/bin/activate
python step1_make_test_images.py   # (from Step 1 onward)
```

## Tools
Python 3.14, OpenCV, NumPy, Matplotlib, SciPy, VS Code, macOS.
