# VisiData Development Guide

Quick reference for VisiData development. For detailed coding patterns, conventions, and best practices, see **[dev/STYLE.md](dev/STYLE.md)**.

`CLAUDE.md` and `AGENTS.md` are complementary: use this file for primary contributor workflow and architecture context, and use `AGENTS.md` for concise agent-oriented repository guidance.

## Important Note About AI Usage

VisiData (created in 2016) is 99% written by humans and is NOT a vibe-coded AI project.  This file is meant to allow AI-assisted development of features and bugfixes.  **All code must be reviewed and approved and tested by a human before being merged into the codebase or submitted as a PR.**

## Repository Structure

```
visidata/
├── visidata/              # Main package
│   ├── *.py              # Core modules (sheet.py, column.py, etc.)
│   ├── features/         # Auto-loaded feature plugins
│   ├── loaders/          # File format loaders
│   ├── apps/             # Standalone applications
│   └── experimental/     # Experimental features (load/install with 'import visidata.experimental.foo')
├── tests/                # Test files
├── docs/                 # Documentation
└── dev/                  # Development utilities and docs
```

## Features Directory (`visidata/features/`)

- All `.py` files in this directory are **automatically imported** when VisiData starts
- Each feature file should be self-contained
- Features extend VisiData functionality without modifying core files

## Quick Reference

### Core Classes
- `BaseSheet` - Minimal sheet functionality
- `Sheet` / `TableSheet` - Sheet with columns and rows (most common)
- `Column` - Column definition with getter/setter

### Adding Commands
```python
BaseSheet.addCommand('', 'command-name', 'code', 'help text')
```

### Adding to Global Namespace
```python
vd.addGlobals(MyClass=MyClass)  # Use keyword args, not dict
```

### Adding Menu Items
```python
vd.addMenuItems('''
    Menu > Submenu > Item Name > command-name
''')
```

### Example Feature Structure
```python
from visidata import vd, Sheet, Column

# rowdef: description of what a row represents
class MySheet(Sheet):
    rowtype = 'items'
    columns = [
        Column('name', getter=lambda c,r: r.attribute),
    ]

    def reload(self):
        self.rows = [...]

BaseSheet.addCommand('', 'my-command', 'code', 'help')
vd.addGlobals(MySheet=MySheet)
```

## Development Workflow

1. Add `.py` file to `visidata/features/`
2. Run `vd` and test interactively
3. Iterate and refine
4. Document with docstrings and comments

## Make Targets

- `make test` — run all tests
- `make help` — list all targets

## Documentation

For comprehensive development documentation, see the `dev/` directory:

### [dev/STYLE.md](dev/STYLE.md) - Coding Style and Patterns
Use this when writing code, creating features, or defining sheets and columns.
- Naming conventions (camelCaps, under_score, etc.)
- Feature file structure and patterns
- Sheet and Column class patterns
- Command and menu integration
- API decorators
- Best practices and examples

### [dev/GIT.md](dev/GIT.md) - Version Control Practices
Use this when making commits or preparing pull requests.
- Commit message format and conventions
- Issue tracking in code
- Branch and merge workflow
- Patch-safe commit marking

### [dev/DOCS.md](dev/DOCS.md) - Documentation Writing
Use this when writing user-facing documentation, help text, or in-app guides.
- VisiData's markdown syntax
- Display attribute syntax (colors, clickable links)
- Option and command reference format
- Technical writing guidelines

### [dev/PERFORMANCE.md](dev/PERFORMANCE.md) - Performance Analysis
Use this when investigating or optimizing performance issues.
- Finding reproducible performance issues
- Profiling techniques and tools
- Analyzing profiling results
- Optimization workflow

### [dev/OPTIONS.md](dev/OPTIONS.md) - Options System
Use this when working with options, adding new options, or understanding how configuration resolves.
- Resolution chain (instance → class → global → default)
- How sheets and paths participate in options
- Setting and reading options at different levels

## Updating Documentation

When making **user-facing changes** (new commands, changed behavior, new options, new/changed loaders, UI changes), check [docs/README.md](docs/README.md) to identify which documentation files need to be updated.
