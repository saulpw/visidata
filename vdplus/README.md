# VisiData Plus

VisiData Plus contains many useful loaders and features for [VisiData](https://visidata.org).

### APIs

- [Google Drive](https://github.com/saulpw/vdplus/tree/develop/api/google): list/open/delete files via [Google Drive API](https://developers.google.com/drive/).
- [Google Sheets](https://github.com/saulpw/vdplus/tree/develop/api/google): load/save new sheet (with `.g` extension) via [Google Sheets API](https://developers.google.com/sheets/).
- [Airtable](https://github.com/saulpw/vdplus/tree/develop/api/airtable): load/save existing table via [Airtable API](https://airtable.com/api).
- [Reddit](https://github.com/saulpw/vdplus/tree/develop/api/reddit): read-only interface to [Reddit API](https://www.reddit.com/dev/api) for subreddits, redditors, submissions, and comments.
- [Zulip](https://github.com/saulpw/vdplus/tree/develop/api/zulip): read-only interface to [Zulip chat API](https://github.com/zulip/zulip).
- [RC Together](https://github.com/saulpw/vdplus/tree/develop/api/rctogether): control an army of bots via [RC Together API](https://docs.rctogether.com/).
- [bit.io](https://github.com/saulpw/vdplus/tree/develop/api/bitio): interface to [bit.io](https://bit.io) API.


### File formats

- [orgmode](): read/save .org and .md files; filetypes `org`, `md`, `forg` (with a list of files), and `orgdir` (with a directory of .org files)
- [jrnl.sh](https://jrnl.sh): read/save journal files; filetype `jrnl`
- various [mailbox formats](https://docs.python.org/3/library/mailbox.html): `mbox`, `maildir`, `mmdf`, `babyl`, `mh`

### Other data libraries

- [Ibis](https://ibis-project.org): connect to various database backends (currently only sqlite is supported in vdplus) and query without loading the entire database.

### Other features/tools

- [graphing](https://github.com/saulpw/vdplus/tree/develop/graphing): save scatterplot as .svg
- [web scraper](https://github.com/saulpw/vdplus/tree/develop/scraper): scrape urls from web pages and web pages from urls iteratively and interactively.
- [ping](https://github.com/saulpw/vdplus/tree/develop/ping): interactive ping+traceroute
- [top](https://github.com/saulpw/vdplus/tree/develop/top): interactive process viewer
- [Galactic Conquest](https://github.com/saulpw/vdplus/tree/develop/galcon): a remake of the classic [Galcon](http://www.galcon.com/classic/history.html).

- [light color scheme](https://github.com/saulpw/vdplus/tree/develop/lightscheme.py): use `vd.use_light_colors()` in .visidatarc

## License

The code and documentation in this repository, hereafter "VisiData Plus", is **not** open-source software.

VisiData Plus is copyright [Saul Pwanson](https://github.com/saulpw), who has the sole authority to release, license, or redistribute its contents.

As an individual, you may use VisiData Plus under the [PolyForm Non-Commercial Use license](LICENSE.polyform-non-commercial.txt).

Other license terms are available for VisiData Plus; contact [Saul Pwanson](mailto:vdplus@saul.pw) for more information.

Individual components of VisiData Plus may be available to convert to open-source license, particularly if you are willing to expand, maintain, and package that component for release.

If you submit a Pull Request to this repository, you **must** digitally sign the [Contributor Assignment Agreement](https://github.com/saulpw/vdplus/tree/develop/CONTRIBUTING.md) before it can be merged.

## Installing VisiData Plus

1. Clone this repo into `.visidata/vdplus`:

```
    git clone git@github.com:saulpw/vdplus ~/.visidata/vdplus
```

2. Add this line to your `.visidatarc` (which is usually in your home directory) for every component you want to use:

```
    import vdplus
```

Additional options may be necessary for certain components; see the README for each component.

3. Install Python requirements for that component:

```
    pip3 install -r ~/.visidata/vdplus/<component>/requirements.txt
```

4. You may have to upgrade to the [unreleased "develop" branch of VisiData](https://github.com/saulpw/visidata/tree/develop):

```
    pip3 install git+https://github.com/saulpw/visidata.git@develop
```
