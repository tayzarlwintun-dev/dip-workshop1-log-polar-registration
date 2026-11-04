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
| 1 | Make test pictures with a known rotation / zoom / shift | done |
| 2 | Log-polar transform | done |
| 3 | Find rotation and zoom (cross-correlation) | done |
| 4 | Find the shift (search for the center) | done |
| 5 | Align picture 2 onto picture 1 and overlay | done |
| 6 | Optimizer fine-tuning (bonus) | done |
| 7 | Report notes | done |
| 8 | Compare with my friend's work | done |
| 9 | Improve my method with my friend's ideas (version 2) | done |

## Folder layout
- `images/` – input photos (`original.jpg`)
- `results/` – pictures and numbers the scripts make
- `JOURNAL.md` – what was done at each step
- `TESTS_AND_FAILURES.md` – tests we ran and what went wrong
- `IDEAS.md` – ideas for later
- `QUESTIONS_AND_ANSWERS.md` – my questions with simple answers
- `REPORT_NOTES.md` – everything for the report (method, results tables, figures, limits)
- `COMPARISON_WITH_FRIEND.md` – my method vs my friend's (same / different, fair tests)
- `IMPROVEMENTS.md` – what changed in version 2, old vs new vs friend vs paper
- `friend_version/` – copy of my friend's code (used by Step 8)
- `HANDOFF_FOR_NEW_CHAT.md` – summary for a new Claude chat (read first)

## How to run
```bash
source .venv/bin/activate
python step1_make_test_images.py   # make test pictures
python step2_log_polar.py          # log-polar pictures + slide check
python step3_find_rotation_scale.py  # find rotation + zoom by itself
python step4_find_shift.py           # also find the shift (search the whole picture, version 2)
python step5_align_and_overlay.py    # put test photos back + red/cyan overlay
python step6_optimizer.py            # fine-tune with Levenberg-Marquardt (bonus)
python step8_compare_with_friend.py  # my OLD method vs my friend's (~2-3 min)
python step9_old_vs_new.py           # old vs new vs friend, 13 tests (~10-15 min)
```

## Tools
Python 3.14, OpenCV, NumPy, Matplotlib, SciPy, VS Code, macOS.
Optional: graphify (code map for AI tools). Settings in `.graphifyignore`;
its output folder `graphify-out/` is not saved in git.
