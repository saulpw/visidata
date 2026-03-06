# Testing

VisiData has two test systems:

## 1. Golden tests (integration/replay tests)

Located in `tests/`. These are the primary test suite.

**How it works:** Each test is a command log (`.vd`, `.vdj`, or `.vdx` file) that gets replayed in batch mode. The output is written to `tests/output/` and compared against the expected output in `tests/golden/` using `diff`. If they differ, the test fails. Tests also fail if any command raises an exception during replay.

**Console output:** Only warnings, errors, and diffs are shown. In debug mode (`-d`), the full diff is printed and replay aborts on the first error. Errors include the test name for context.

**Running tests:**

Use `dev/test.sh` directly (not `bash dev/test.sh`) so that permission prompts can be approved in bulk.

```bash
dev/test.sh              # run all tests (batched, fast)
dev/test.sh issue655     # run one test
dev/test.sh foo bar baz  # run multiple tests
dev/test.sh -d           # debug mode: abort on first error, show diffs

dev/perftest.sh          # run perf benchmarks (sequential, per-test timing)

dev/run-tests-individually.sh                # run each test in its own process (slower, isolated)
dev/run-tests-individually.sh tests/foo.vdx  # run specific tests individually
```

By default, `test.sh` splits tests into `nproc` parallel batches for speed (~5s). Use `-j N` to control parallelism. Use `run-tests-individually.sh` to run each test in its own process — slower but provides full isolation, useful for debugging cross-test contamination.

The replay file is now always loaded as `vdx`, but tests may be in vd, vdj, or vdx format; the `.vdx` loader now interprets all three formats (even commingled).

Prefer vdx format for new tests.

**What the harness checks:**
1. **Runtime errors** — any exception during replay (tracked via `vd.lastErrors`)
2. **Missing output** — expected output files that were never created
3. **Diff failures** — output that doesn't match the golden file
4. **No golden file** — output files with no corresponding golden file

A test fails if any of these conditions are true for it.

**Test file formats:**
- `.vd` — TSV command log (columns: sheet, col, row, longname, input, keystrokes, comment)
- `.vdj` — JSON command log: {sheet, col, row, longname, input, keystrokes, comment}
- `.vdx` — Simple command format (one command per line: `longname [input]`; sheet/row/col not as context but as separate movement commands)

All three formats allow `#` line comments.

**Golden files:** `tests/golden/testname.ext` — the expected output (committed, read-only reference). The extension determines the save format (`.tsv`, `.csv`, `.html`, etc.).

**Test output:** `tests/output/testname.ext` — actual output from the latest test run (gitignored, never committed). Compare against golden with `diff tests/golden/name.ext tests/output/name.ext`.

**Conventions:**
- `-nosave` suffix (e.g., `issue2225-nosave.vdx`) skips golden comparison; runs in a separate batch without `replay_ignore_errors`, so `assert-expr` failures are caught. Use for tests that verify internal state via assertions rather than output comparison. Also required for graph/canvas tests, since the pixel buffer is not populated in batch mode (cursor-based commands are no-ops).
- `-broken` suffix skips the test entirely
- `-manual` suffix skips the test entirely (for tests not suitable for automation but worth keeping)
- `-perf` suffix skips the test in `test.sh`; run separately via `dev/perftest.sh`
- `-flaky` suffix runs the test but treats failures as non-fatal
- `-311` suffix runs only on Python 3.11+; `-n311` runs only below 3.11
- Tests should modify data and provide golden output file, rather than using `assert-expr` commands
- Set explicit cursor positions (e.g., `row 6`) rather than relying on defaults, for test hygiene
- Explicit saving is not necessary, as the test harness will save the top sheet to the proper output file
- Never fetch from the network in tests; use local fixture files instead (flaky connections cause spurious CI failures)

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

## Batch replay internals

The test harness (`dev/test.sh`) splits tests into parallel VDX batches (sequential chunks so tests with similar imports share a process), separated by `replay-reset` / `replay-output` / `replay-end` commands (defined in `visidata/features/replay_bulk.py`).

**Batch structure:**
```
option global replay_ignore_errors True
replay-reset tests/output/foo.tsv      # reset state, set output path
<contents of tests/foo.vdx>            # test commands
replay-output                           # save top sheet, reset
replay-reset tests/output/bar.tsv      # next test...
<contents of tests/bar.vdx>
replay-output
replay-reset baz-nosave                 # nosave tests use replay-end instead
<contents of tests/baz-nosave.vdx>
replay-end                              # no save
replay-exit                             # end of batch
```

**Key commands:**
- `replay-reset <path>` — call `resetVisiData()` to get clean state (including resetting options to defaults), set output path
- `replay-output` — save current sheet to path
- `replay-end` — no-op (for nosave tests)
- `replay-exit` — no-op (end of batch)

**Error handling:** `replay_ignore_errors` lets the batch continue past individual command errors. Errors printed via `vd.status()` appear on stderr for diagnostic purposes, but do not affect test pass/fail. Only output correctness (golden file diffs) determines test success.

## 2. Python tests (pytest)

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

**The `feature.py:def test_feature(vd)` pattern:** Any VisiData module can define `test_*` functions that take `vd` as a parameter. These are auto-discovered and run by pytest. Useful for testing features alongside their implementation (see `features/slide.py` for an example using `vd.runvdx()`).

## Test Style

When a test is a series of one-liner asserts (like testing a pure function with many input/output pairs), combine them into a single test function. Add a short comment at the end of each line if the reason isn't obvious from the assertion itself. Don't create separate test functions for each case.

## Bug Fix Testing

Always write tests FIRST, verify they FAIL on the current code, then fix the code and verify the tests pass. Use the appropriate test type:

- **Unit tests** (pytest) for pure functions like `wraptext()`, `clipstr()`, `iterchunks()` — add to existing test files in `visidata/tests/`
- **Golden tests** for behavior that requires the full VisiData UI/session — create a `.vdx` test in `tests/`

For golden tests: create a `.vdx` file, generate golden output, and verify with `dev/test.sh`.

# Sample Data

- `sample_data/benchmark.csv`:  small CSV (51 rows, 7 columns: Date, Customer, SKU, Item, Quantity, Unit, Paid)
- Various other formats in `sample_data/`
- Every new loader should provide its test data of `sample_data/benchmark.filetype` in its own format (if applicable), with columns properly typed.

# vdsql Tests

vdsql has its own test suite in `visidata/apps/vdsql/tests/`, run via `visidata/apps/vdsql/test.sh`. These are golden tests using the same pattern (replay `.vdj` files, compare output against `tests/golden/`). CI runs them separately via `.github/workflows/vdsql.yml`.

```bash
cd visidata/apps/vdsql && bash test.sh           # run all vdsql tests
cd visidata/apps/vdsql && bash test.sh unselect   # run a single test
```

# Test Configuration

- `tests/.visidatarc` — test-specific options
- `tests/.visidata/` — test-specific visidata directory
