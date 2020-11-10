# Contributing

## Spread the Word

The single best way you can contribute, is to share your enthusiasm about VisiData with other people.
A vibrant community is essential to its sustainable development.

However, direct and forceful promotion is probably not the most effective approach for a tool like VisiData.
People generally need to be exposed several times and from several sources before they will try some terminal utility they've never heard of before.

Some people are interested, but are daunted by the installation process or the interface; you can [help them get it installed](/install), and provide a few pointers to get started.
Don't make it too complicated or overload them with too many features.
Stick to the basics: arrow keys, quit, help, search, sort, freq table.

We also need people to mention VisiData in their forums and communities that relate to data and terminal programs.
Don't spam or do a drive-by promotion; these are largely ineffective and will often be received negatively.
Endorsements have more weight from people who actively post about other relevant topics; we don't want to become the "VisiData Brigade".

Finally, if you are on "Web 2.social", you can post a [tweet](https://twitter.com/visidata) or a [tutorial]() or a [demo](https://www.youtube.com/watch?v=N1CBDTgGtOU) or [host a workshop](https://www.meetup.com/pt-BR/Journocoders/events/258035880/), or anything else you think might make people interested in exploring the wonderful world of VisiData.

## Support on Patreon

If VisiData saves you time on a regular basis, and especially if VisiData makes your paid work easier, please contribute to [my Patreon](https://www.patreon.com/saulpw).

## Start a Project Using VisiData

If you know Python and want to augment it to suit your own workflow, you can create a loader or a plugin.  In support of this, I have written [a detailed api guide for VisiData](https://www.visidata.org/docs/api/).

Here are some great examples:

    - [jsvine's custom visidata plugins](https://github.com/jsvine/visidata-plugins)
    - [layertwo's pcap loader](https://github.com/saulpw/visidata/blob/develop/visidata/loaders/pcap.py)

Without fail, these projects lead to discovering bugs and help flesh out the API, which result in design improvements in VisiData.
Importantly, each issue found this way comes with real world motivations, so it is easy to explain your reasoning behind proposals and core feature requests.

## Feature Requests

VisiData is designed to be extensible, and most feature requests can be implemented as a one line command, or a tiny snippet of code to include in a `.visidatarc`.

If this would require changes to the VisiData core, and a reasonable design is approved, then the issue can stay open until the core changes have been made.
Otherwise, in the spirit of Marie Kondo, the issue will be closed without prejudice.

Feature requests with some amount of working Python code are more likely to get attention.
Design proposals with concrete use cases are very welcome.

## Writing a well constructed bug report

If you encounter any bugs or have any problems, please [create an issue on GitHub](https://github.com/saulpw/visidata/issues).

A great bug report will include:
    - a stacktrace, if there is an unexpected error; the most recent full stack traces can be viewed with `Ctrl+E` (then saved with `Ctrl+S`)
    - a [.vd](http://visidata.org/docs/save-restore/) and sample dataset that reproduces the issue
    - a .png/.gif (esp. for user interface changes)

Some examples of great bug reports:
    - [#350 by @chocolateboy](https://github.com/saulpw/visidata/issues/350)
    - [#340 by @Mikee-3000](https://github.com/saulpw/visidata/issues/340)


## Submitting Source Code

Code in `plugins/` or `visidata/loaders/` is welcome, as long as it is useful to someone and safe for everyone.
Updates or additions to the core code should be proposed via an [Github Issue](https://github.com/saulpw/visidata/issues/new/choose) before submitting a PR.

VisiData has two main branches:

    - [stable](https://github.com/saulpw/visidata/tree/stable) has the last known good version of VisiData (what is in pypi/brew/apt).
    - [develop](https://github.com/saulpw/visidata/tree/develop) has the most up-to-date version of VisiData (which will eventually be merged to stable).

All pull requests should be submitted against `develop`.

# Open Source License and Copyright

VisiData is an open-source utility that can be installed and used for free (under the terms of the [GPL3](https://www.gnu.org/licenses/gpl-3.0.en.html)).

The core VisiData utility and rendering library will always be both free and libre.

As the copyright holder, Saul Pwanson has the authority to negotiate other license terms.

**By submitting changes to this repository, you acknowledge that you assign copyright to the owner of the repository ([Saul Pwanson <vd@saul.pw>](mailto:vd@saul.pw)).**
