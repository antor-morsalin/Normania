# Normania — immediate capture and OTHERWISE repair

Updated September 17, 2026, from the September 16 fixed project. The project keeps the 6-row × 5-column board, DICT_5X5_250, corner IDs 200–203, and the existing programming marker IDs.

## Run

Extract this archive and open the included `Normania` folder in your terminal. Use all the included files together; the `App`, `Data`, and `Parsing` folders must remain alongside `main.py`.

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

If updating your existing project, copy `main.py` and the included `App`, `Data`, and `Parsing` Python files into their matching folders. The archive is also a complete standalone copy. Python must have Tk support for the desktop interface, as your current installation does.

## What was fixed

- Capture now accepts the first nonempty, valid reading immediately. There is no two-second countdown, minimum number of repeated readings, or motion-triggered restart. Unreadable or invalid programs keep the camera open until corrected or cancelled.
- `OTHERWISE` now also works immediately after an `END` that closed its IF. Both supported layouts are shown below. The condition's truth value affects execution, never whether the parser recognizes the branch.
- A row containing only `SHOW` now produces a clear row-specific error instead of `IndexError`. In live capture, the camera continues reading and shows the problem until the missing value is visible.
- Assignments require `IS`; IF headers require `THEN`; loops require `TIMES`. Extra blocks are validated rather than silently discarded.
- IF, OTHERWISE, nested REPEAT, and END use explicit scope records. Errors identify the physical row and relevant opening structure. Empty bodies, duplicate OTHERWISE blocks, extra END blocks, and missing END blocks are reported without guessing the intended program.
- `REPEAT C TIMES` remains supported. C must contain a non-negative integer when the loop runs.
- Repeated marker IDs remain separate physical blocks. Detection uses normal and contrast-enhanced images, plus another reading of the perspective-corrected board from the same frame.
- Corner selection uses geometry rather than assuming a particular rotation of each printed marker. Invalid geometry, cell collisions, non-finite positions, and positions close to cell boundaries receive clear errors.
- Capture reuses that exact validated matrix for execution and never combines tokens from different frames.
- The capture window displays all detected rows and marker labels. The main window also has a “VIEW DETECTED ROWS” button.
- Marker 38 maps to `MY NAME IS` in the latest supplied ArUco map. The missing matching syntax entry has been added without changing its ID.
- Expected errors stay in the interface rather than escaping as Tkinter callback tracebacks. Runtime errors identify board rows. Long loops and excessive output are bounded.

## IF and OTHERWISE

The usual layout has one END after both branches:

```text
IF | 1 | IS | 2 | THEN
SHOW | GREAT JOB
OTHERWISE
SHOW | KEEP TRYING
END
```

This layout is now also accepted, with an END before OTHERWISE and another END after its body:

```text
IF | 1 | IS | 2 | THEN
SHOW | GREAT JOB
END
OTHERWISE
SHOW | KEEP TRYING
END
```

Both print only `KEEP TRYING`, because `1 IS 2` is false. Changing the first value to `2` prints only `GREAT JOB`. An unrelated instruction between END and OTHERWISE breaks their connection. OTHERWISE still needs an IF; END after REPEAT does not supply one. In nested programs an already-open IF takes precedence over a just-closed IF.

## Your reported example

The supplied crash contains only `SHOW` in row 3. Your later reading identifies the intended message as `KEEP TRYING`, marker 41. With that marker detected, the program is:

```text
Row 1: C | IS | 4
Row 2: REPEAT | C | TIMES
Row 3: SHOW | KEEP TRYING
Row 4: END
Row 5: SHOW | YOU CAN DO IT
Row 6: (empty)
```

It prints `KEEP TRYING` four times, then `YOU CAN DO IT` once. The error fixture preserves the original missing marker; the software does not invent it.

## Replay without a camera

Run these from the included `Normania` folder:

```bash
python3 main.py --matrix examples/repeat_c.json
python3 main.py --matrix examples/if_otherwise.json
python3 main.py --matrix examples/if_end_otherwise.json
python3 main.py --matrix examples/missing_show_value.json
python3 main.py --image examples/synthetic_repeat_board.png --debug debug
```

The missing-value example deliberately exits with a row 3 error. To diagnose a real photograph, replace the image path with your saved board photo. Successful live captures save `App/test.png`, `App/detected_board.png`, and `App/last_capture.json`; the latter can also be replayed with `--matrix`.

## Validation and limits

93 automated tests passed, including immediate capture with a simulated camera and Tk event loop, invalid readings followed by a valid reading with board movement and no elapsed time, both IF/OTHERWISE layouts with true and false conditions, and physical row numbers for errors. The existing regression checks cover the reported SHOW crash, loop output, nested scopes, malformed rows, GUI callback recovery, and actual ArUco decoding of synthetic images with mirroring, rotation, perspective, low light, blur, and reduced size. The suite also checks 2,500 randomly generated malformed matrices for unexpected parser failures.

The full image → matrix → parser → execution path was checked against the included synthetic loop board in the previous update. Current test environment: Python 3.12, OpenCV 5.0, NumPy 2.3.5, and CustomTkinter 6.0. The Mac camera and Python 3.14 installation have not been tested here.

A fully hidden or consistently unreadable marker cannot be inferred reliably. In particular, an undetected OTHERWISE can leave a syntactically valid IF with two output rows. The additional reading passes within each frame help recover markers, but validity alone cannot confirm that every physical block was seen. Use VIEW DETECTED ROWS after capture to confirm the reading matches the physical board. Use a flat board, visible markers, and even lighting. There are no changes to the marker dictionary or printed IDs.

To run the regression suite:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q
```

Detector parameter reference: [OpenCV ArUco documentation](https://docs.opencv.org/4.13.0/d5/dae/tutorial_aruco_detection.html).
