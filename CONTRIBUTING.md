# Contributing

*Adapted from [ziglang's CONTRIBUTING.md](https://github.com/ziglang/zig/blob/master/CONTRIBUTING.md)*

## Start a Project Using VisiData

One of the best ways you can contribute to VisiData is to start building loaders or plugins. Here are some great examples:

    - [jsvine's custom visidata plugins](https://github.com/jsvine/visidata-plugins)
    - [layertwo's pcap loader](https://github.com/saulpw/visidata/blob/develop/visidata/loaders/pcap.py)
    - [vls](https://github.com/saulpw/visidata/blob/develop/vsh/vls)

Without fail, these projects lead to discovering bugs and help flesh out the API, which result in design improvements in VisiData. Importantly, each issue found this way comes with real world motivations, so it is easy to explain your reasoning behind proposals and core feature requests.

## Feature Requests

VisiData is designed to be extensible, and most feature requests can be implemented as a small plugin.
If this would require changes to the VisiData core, and a reasonable design is approved, then the issue can stay open until the core changes have been made.
Otherwise, in the spirit of Marie Kondo, the issue will be closed without prejudice.

Feature requests with some amount of working Python code are more likely to get attention.
Design proposals with concrete use cases are very welcome.

## Spread the Word

Another way to contribute is to write about VisiData, host a workshop, or speak about VisiData at a conference. Here are some examples:

    - [jsvine's Introduction to VisiData](https://jsvine.github.io/intro-to-visidata/index.html)
    - [aborruso tweeted](https://twitter.com/aborruso/status/1152161585835728896)
    - [VisiData Workshop hosted in London]()
    - [saulpw gave a lightning talk](https://www.youtube.com/watch?v=N1CBDTgGtOU)

VisiData is an ambitious, niche project, with no advertising budget. Word of mouth is the only way people find out about it, and the more people hear about it, the more people will use it, and the more the ecosystem will develop.

## Writing a well constructed bug report

If you encounter any bugs or have any problems, please [create an issue on GitHub](https://github.com/saulpw/visidata/issues).

A great bug report will include:
    - a stacktrace, if there is an unexpected error; the most recent full stack traces can be viewed with `Ctrl+E` (then saved with `Ctrl+S`)
    - a [.vd](http://visidata.org/docs/save-restore/) and sample dataset that reproduces the issue
    - a .png/.gif (esp. for user interface changes)

Some examples of great bug reports:
    - [#350 by @chocolateboy](https://github.com/saulpw/visidata/issues/350)
    - [#340 by @Mikee-3000](https://github.com/saulpw/visidata/issues/340)

## Money

If VisiData has saved you time and effort, please contribute to [my Patreon](https://www.patreon.com/saulpw).

## Editing source code

Code in /plugins or visidata/loaders is welcome, as long as it is useful to someone and safe for everyone.
Major updates or additions to the core code should be proposed via an Issue before submitting a PR.

VisiData has two main branches:

    - [stable](https://github.com/saulpw/visidata/tree/stable) has the last known good version of VisiData (what is in pypi/brew/apt).
    - [develop](https://github.com/saulpw/visidata/tree/develop) has the most up-to-date version of VisiData (which will eventually be merged to stable).

All pull requests should be submitted against `develop`.

## Open Source License and Copyright
VisiData is an open-source tool that can be installed and used for free (under the terms of the [GPL3](https://www.gnu.org/licenses/gpl-3.0.en.html)).

The core VisiData utility and rendering library will always be both free and libre.

Plugins (and loaders and apps) retain the copyright of the contributing authors, as maintained in the `__author__` metadata. All plugins must have the licensing terms compatible with GPL3.
The copyright for all other code in VisiData is assigned to [Saul Pwanson <vd@saul.pw>](mailto:vd@saul.pw).
