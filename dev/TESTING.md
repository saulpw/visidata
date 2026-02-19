# Testing

## Test Types

VisiData has two test systems:

### 1. Golden tests (integration/replay tests)

Located in `tests/`. These are the primary test suite.

**How it works:** Each test is a command log (`.vd`, `.vdj`, or `.vdx` file) that gets replayed with `--batch --output`. The output is compared against a golden file in `tests/golden/`. If `git diff` shows changes, the test fails.

**Running tests:**
```bash
dev/test.sh              # run all tests
dev/test.sh issue655     # run a single test (matches tests/issue655.vd*)
dev/test.sh -j 4         # run tests in parallel
```

**Test file formats:**
- `.vd` — TSV command log (columns: sheet, col, row, longname, input, keystrokes, comment)
- `.vdj` — JSON command log
- `.vdx` — Simple command format (one command per line: `longname [input]`)

**Golden files:** `tests/golden/testname.ext` — the expected output. The extension determines the save format (`.tsv`, `.csv`, `.html`, etc.).

**Conventions:**
- `-nosave` suffix (e.g., `issue2225-nosave.vdx`) skips golden comparison; useful for tests that only need to not crash
- Tests should modify data and check the result via golden output, rather than using `assert-expr` commands
- Set explicit cursor positions (e.g., `row 6`) rather than relying on defaults, for test hygiene

**Creating a new golden test:**
1. Write a `.vdx` file in `tests/` (simplest format)
2. Generate the golden output:
   ```bash
   PYTHONPATH=. bin/vd --play tests/mytest.vdx --batch --output tests/golden/mytest.tsv \
       --config tests/.visidatarc --visidata-dir tests/.visidata
   ```
3. Review the golden output, then run `dev/test.sh mytest` to confirm it passes

**Useful commands for .vdx tests:**
- `open-file path` — open a data file
- `row N` / `col NAME` — move cursor
- `select-rows` — select all rows
- `define-command longname execstr` — define an ad-hoc command for testing
- `assert-expr expr` / `assert-expr-row expr` — assert (prefer golden output comparison instead)

### 2. Python tests (pytest)

Located in `visidata/tests/`. Run with `pytest`.

```bash
pytest visidata/tests/                    # run all
pytest visidata/tests/test_commands.py    # test all commands execute without error
pytest visidata/tests/test_features.py    # run test_ functions discovered from visidata modules
```

**Key files:**
- `conftest.py` — fixtures: `curses_setup` (mock curses), `mock_screen` (mock screen object)
- `test_commands.py` — runs every registered command once with sample data
- `test_features.py` — discovers `test_*` functions from VisiData's imported modules (e.g., `test_slide_keycol_1` in `features/slide.py`)
- `test_cliptext.py`, `test_date.py`, etc. — unit tests for specific functions

**The `test_features.py` pattern:** Any VisiData module can define `test_*` functions that take `vd` as a parameter. These are auto-discovered and run by pytest. Useful for testing features alongside their implementation (see `features/slide.py` for an example using `vd.runvdx()`).

## Bug Fix Testing

Always test bug fixes with golden tests, not ad-hoc Python scripts. Write the test FIRST, verify it FAILS on the current code, then make the code change and verify the test passes. Create a `.vdx` test in `tests/`, generate golden output, and verify with `dev/test.sh`.

## Sample Data

- `visidata/tests/sample.tsv` — small TSV (44 rows, 7 columns: OrderDate, Region, Rep, Item, Units, Unit_Cost, Total)
- `sample_data/benchmark.csv` — larger CSV (51 rows, 7 columns: Date, Customer, SKU, Item, Quantity, Unit, Paid)
- Various other formats in `sample_data/`

## Test Configuration

- `tests/.visidatarc` — test-specific options
- `tests/.visidata/` — test-specific visidata directory
