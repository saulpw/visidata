# VisiData Plus

This repo contains many interesting plugins for use with [VisiData](https://visidata.org).

## Plugins

- [Google Drive](tree/develop/google): list/open/delete files via [Google Drive API](https://developers.google.com/drive/).
- [Google Sheets](tree/develop/google): load/save new sheet (with `.g` extension) via [Google Sheets API](https://developers.google.com/sheets/).
- [Airtable](tree/develop/airtable): load/save existing table via [Airtable API](https://airtable.com/api).
- [Web Scraper](tree/develop/scraper): scrape urls from web pages and web pages from urls iteratively and interactively.
- [Reddit](tree/develop/reddit): read-only interface to [Reddit API](https://www.reddit.com/dev/api) for subreddits, redditors, submissions, and comments.
- [Zulip](tree/develop/zulip): read-only interface to [Zulip chat API](https://github.com/zulip/zulip).
- [RC Together](tree/develop/rctogether): control an army of bots via [RC Together API](https://docs.rctogether.com/).

## No License Granted By Default

The code in this repository, hereafter "VisiData Plus", is **not** open-source software.

All code and documentation in this repository is copyright [Saul Pwanson](https://github.com/saulpw), who has the sole authority to release, license, or redistribute its contents.

You **must not** redistribute any of the source code contained in this repository, unless it has been explicitly released under an Open Source License.

You **may** use components which have been released under an Open Source License; see the component-level READMEs for information.

You **may** use other components on a trial basis to discover their capabilities.

You **may** view or read any of the source code, to learn about Python, or how to make VisiData plugins, or how to use a specific API or library.

You **may** request permission to use one or more components in this repository on an ongoing basis by contacting [Saul Pwanson](mailto:vdplus@saul.pw), who probably will agree to liberal terms if you ask nicely, and particularly if you express interest in expanding, maintaining, and/or packaging a component for release.

You **must** have digitally signed the [Contributor Assignment Agreement](https://github.com/saulpw/vdplus/tree/develop/CONTRIBUTING.md) in order to submit changes to this repository.

## Installing a component

1. Clone this repo into `.visidata/vdplus`:

    git clone git@github.com:saulpw/vdplus ~/.visidata/vdplus

2. Add this line to your `.visidatarc` (which is usually in your home directory) for every component you want to use:

    import vdplus.<component>

3. Install Python requirements for that component:

    pip3 install -r ~/.visidata/vdplus/<component>/requirements.txt

4. You may have to upgrade to the [unreleased "develop" branch of VisiData](https://github.com/saulpw/visidata/tree/develop):

    pip3 install git+https://github.com/saulpw/visidata.git@develop
