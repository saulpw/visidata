---
eleventyNavigation:
  key: Checklists for Contributing to VisiData
  order: 99
---

## [Submitting a Core Loader](#loader) {#loader}
A deeper explanation of all of these steps can be found [in the loaders api documentation](https://www.visidata.org/docs/api/loaders.html).

- Create an `open_foo` function that returns the new `FooSheet`.
- Set an appropriate `rowtype` string.
- Provide a `# rowdef: ` comment. This describes the structure of a row (e.g. its base class) in a **Sheet**.
- If the loader's dependencies are not part of Python3 stdlib, note the additional dependencies in the `requirements.txt` (include a comment adjacent to the dep with the name of the loader).
- Check in a small sample dataset, in that format, to the `sample_data` folder
- Add a `load-foo.vd` to `tests/`. `load-foo.vd` should simply open the checked-in sample dataset and have a simple interaction if the source includes multiple tables.
- After replaying `vd load-foo.vd`, save the final sheet as `load-foo.tsv`. Save `load-foo.tsv` in `tests/golden/`.
- add a section on the loader to the [formats.jsonl](https://github.com/saulpw/visidata/blob/develop/dev/formats.jsonl).

## [Submitting an External Plugin](#plugins) {#plugins}
A deeper explanation of all of this framework can be found [in the plugins api documentation](https://www.visidata.org/docs/api/plugins.html).

- Host a single Python file containing all of the plugin's code.
- In the https://github.com/visidata/dlc/blob/stable/plugins.jsonl file in the `visidata:dlc` repo, add a row for each plugin with all of the necessary information.
