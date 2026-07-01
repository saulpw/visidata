# dev/

Resources for VisiData contributors and maintainers.

## Contributor Guides

| File | Description |
|------|-------------|
| `STYLE.md` | Code style guide |
| `GIT.md` | Git workflow and branching conventions |
| `DOCS.md` | Documentation standards |
| `PERFORMANCE.md` | Performance guidelines |
| `TESTING.md` | Test framework guide (golden tests, pytest, writing new tests) |

## Checklists

| File | Description |
|------|-------------|
| `checklists/release.md` | Release process checklist |
| `checklists/feature.md` | New feature checklist (docs, tests, marketing, sample data) |
| `checklists/manual-tests.md` | Manual testing checklist (cmdlog, replay, options, split window, etc.) |
| `checklists/add-command.md` | Adding a new command |
| `checklists/add-aggregator.md` | Adding a new aggregator |

## Design Docs

See [design/README.md](design/README.md) for full index.

## Scripts

| File | Description |
|------|-------------|
| `test.sh` | Run test suite (batched, fast; `-d` for debug; see `TESTING.md`) |
| `diff-test.sh` | Diff-based test runner |
| `run-tests-individually.sh` | Run each test in its own process (isolated, slower; see `TESTING.md`) |
| `mkman.sh` | Generate manpage |
| `mkpandas-df.py` | Generate pandas DataFrame test fixtures |
| `zsh-completion.py` | Generate zsh completions |

## Data Files

| File | Description |
|------|-------------|
| `formats.jsonl` | Format metadata (builds visidata.org/formats) |
| `types.jsonl` | Type system structure |

## Test Fixtures

| File | Description |
|------|-------------|
| `stdin.vdj` | Used in CI (`.github/workflows/main.yml`) |
| `quit.vdx` | Quit test fixture |
| `formats.vd` | Format test fixture |
| `vduplot.vdx` | Unicode plot test |

## Packaging

| File | Description |
|------|-------------|
| `debian/` | Debian packaging files |
| `build-container` | Container build script |
| `visidata-brew.rb` | Homebrew formula (stale — pins v1.2) |
| `requirements-dev.txt` | Dev dependencies |

## Media

| File | Description |
|------|-------------|
| `kb-blank.svg` | Blank keyboard layout template |
| `kb-layout.svg` | VisiData keyboard layout |
| `vdlogo.svg` | VisiData logo |

## Other

| File | Description |
|------|-------------|
| `zsh-completion.in` | Zsh completion template |
| `workshop-outline.md` | Workshop outline |
