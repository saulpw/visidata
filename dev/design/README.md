# Design Docs

Architecture and feature design documents for VisiData. See also [175-design-terms.md](175-design-terms.md) for the vocabulary used in these docs.

| File | Topic | Status | Description |
|------|-------|--------|-------------|
| `000-notes.md` | Founding vision | Implemented | Original plan (Oct 2016): sheet model, vi navigation, join design, loaders, outputs |
| `160-longnames.md` | Command naming | Implemented | Naming conventions for command longnames (syscopy, dive, slide, etc.) |
| `169-settings.md` | Settings architecture | Implemented | 7-layer option resolution order, command/keybinding API, options API |
| `173-benchmark.md` | Benchmark use cases | Future | 4 benchmark tasks for measuring VisiData performance |
| `174-keycols.md` | Key column rules | Implemented | 8 rules governing key column behavior |
| `175-design-terms.md` | Design vocabulary | Reference | Types of design statements: "is", "ideally", "someday", "currently", "bonus" |
| `176-miscrules.md` | Implementation gotchas | Reference | Rules about asynccache/calcValue behavior |
| `181-benchmark-data.md` | Benchmark dataset | Future | Spec for fictional benchmark dataset with unicode, errors, control chars, "100 mini-puzzles" |
| `200-splitpane.md` | Split pane | Implemented (v3) | Design and post-mortem: original use cases vs actual implementation |
| `232-input.md` | User input API | Implemented | VisiData.input(), confirm(), choose(), editCell(), completer/history |
| `260-push.md` | Push/reload behavior | Implemented | Gotcha: don't assign members after push (reload may overwrite) |
| `path.md` | visidata.Path | Implemented | Path wrapper API, comparison with pathlib.Path |
