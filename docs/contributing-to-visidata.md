# Checklists for Contributing to VIsiData

## [Submitting a Core Loader](#loader) {#loader}
A deeper explanation of all of these steps can be found [in the api documentation](https://www.visidata.org/docs/api/loaders.html).

- Create an `open_foo` function that returns the new `FooSheet`.
- Set an appropriate `rowtype` string.
- Provide a `# rowdef: ` comment. This describes the structure of a row (e.g. its base class) in a **Sheet**.
- If the loader's dependencies are not part of Python3 stdlib, note the additional dependencies in the `requirements.txt` (include a comment adjacent to the dep with the name of the loader).
- Check in a small sample dataset, in that format, to the `sample_data` folder
- Add a `load-foo.vd` to `tests/`. `load-foo.vd` should simply open the checked-in sample dataset and have a simple interaction if the source includes multiple tables.
- After replaying `vd load-foo.vd`, save the final sheet as `load-foo.tsv`. Save `load-foo.tsv` in `tests/golden/`.
- add a section on the loader to the [formats.jsonl](https://github.com/saulpw/visidata/blob/develop/dev/formats.jsonl).

## [Submitting an External Plugin](#plugins) {#plugins}

- Host a single Python file containing all of the plugin's code.
- Ensure the plugin has a `__version__`.
- In the `visidata/plugins/plugins.jsonl` file in the VisiData repo, add a row for each plugin with all of the necessary information:
    - `url`: link to where the plugin file is hosted; specific commit urls are preferred over branches.
    - `description`: a description of the plugin.
    - `latest_ver`: the current version of the plugin.
    - `latest_release`: the date the current version of the plugin was shipped.
    - `maintainer`: your contact information.
    - `visidata_ver`: the latest version of visidata this plugin was tested on.
    - `pydeps` (optional): Space-separated list of pip-installable Python modules required for the plugin.
    - `vdpugindeps` (optional): Space-separated list of vd plugin dependencies.
    - `sha256`: SHA256 hash of the contents of the plugin .py file for the `latest_release`. A script for obtaining this hash can be found [here](https://raw.githubusercontent.com/saulpw/visidata/develop/dev/vdhash.py).
