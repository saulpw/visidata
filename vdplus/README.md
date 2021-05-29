# VisiData Plus

This repo contains many interesting plugins for use with [VisiData](https://visidata.org).

## Plugins

### APIs

- [Google Drive](https://github.com/saulpw/vdplus/tree/develop/api/google): list/open/delete files via [Google Drive API](https://developers.google.com/drive/).
- [Google Sheets](https://github.com/saulpw/vdplus/tree/develop/api/google): load/save new sheet (with `.g` extension) via [Google Sheets API](https://developers.google.com/sheets/).
- [Airtable](https://github.com/saulpw/vdplus/tree/develop/api/airtable): load/save existing table via [Airtable API](https://airtable.com/api).
- [Reddit](https://github.com/saulpw/vdplus/tree/develop/api/reddit): read-only interface to [Reddit API](https://www.reddit.com/dev/api) for subreddits, redditors, submissions, and comments.
- [Zulip](https://github.com/saulpw/vdplus/tree/develop/api/zulip): read-only interface to [Zulip chat API](https://github.com/zulip/zulip).
- [RC Together](https://github.com/saulpw/vdplus/tree/develop/api/rctogether): control an army of bots via [RC Together API](https://docs.rctogether.com/).
- [bit.io](https://github.com/saulpw/vdplus/tree/develop/api/bitio): interface to [bit.io](https://bit.io) API.

### Other tools

- [Web Scraper](https://github.com/saulpw/vdplus/tree/develop/api/scraper): scrape urls from web pages and web pages from urls iteratively and interactively.
- [ping](https://github.com/saulpw/vdplus/tree/develop/api/ping): interactive ping+traceroute
- [top](https://github.com/saulpw/vdplus/tree/develop/api/top): interactive process viewer
- [Galactic Conquest](https://github.com/saulpw/vdplus/tree/develop/api/galcon): a remake of the classic [Galcon](http://www.galcon.com/classic/history.html).

## No License Granted By Default

The code in this repository, hereafter "VisiData Plus", is **not** open-source software.

All code and documentation in this repository is copyright [Saul Pwanson](https://github.com/saulpw), who has the sole authority to release, license, or redistribute its contents.

You **must not** redistribute any of the source code contained in this repository, unless it has been explicitly released under an Open Source License.

You **may** use components which have been released under an Open Source License; see the component-level READMEs for information.

You **may** use other components on a trial basis to discover their capabilities.

You **may** view or read any of the source code, to learn about Python, or how to make VisiData plugins, or how to use a specific API or library.

You **may** request permission to use one or more components in this repository on an ongoing basis by contacting [Saul Pwanson](mailto:vdplus@saul.pw), who probably will agree to liberal terms if you ask nicely, and particularly if you express interest in expanding, maintaining, and/or packaging a component for release.

You **must** digitally sign the [Contributor Assignment Agreement](https://github.com/saulpw/vdplus/tree/develop/CONTRIBUTING.md) in order to submit changes to this repository.

## Installing a component

1. Clone this repo into `.visidata/vdplus`:

    git clone git@github.com:saulpw/vdplus ~/.visidata/vdplus

2. Add this line to your `.visidatarc` (which is usually in your home directory) for every component you want to use:

    import vdplus.<component>

Additional options may be necessary; see the README for each component.

3. Install Python requirements for that component:

    pip3 install -r ~/.visidata/vdplus/<component>/requirements.txt

4. You may have to upgrade to the [unreleased "develop" branch of VisiData](https://github.com/saulpw/visidata/tree/develop):

    pip3 install git+https://github.com/saulpw/visidata.git@develop
