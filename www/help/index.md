# Support {#support}

*How do I install VisiData?*

Add installation instructions here.

*Where can I learn how to use VisiData?*

We have documentation in various levels of detail available at [visidata.org/docs](http://visidata.org/docs/) from [an overview of all commands](http://visidata.org/man/) to [workflow recipes](http://visidata.org/howto).

If you have a workflow which you do not see covered, please don't hestitate to [file an issue](https://github.com/saulpw/visidata/issues/new) or post a comment in any of our [community spaces](https://github.com/saulpw/visidata/blob/develop/CONTRIBUTING.md#community). Our documentation is an ongoing effort, and we wish to prioritise the writing of recipes around user needs.

*I found a bug!*

[Create a GitHub issue](https://github.com/saulpw/visidata/issues/new) if something doesn't appear to be working right. If you get an unexpected error, please include the full stack trace that you get with `^E` and the saved Commandlog (`^D`).

*Where can I go if I have further questions or requests?*

- [r/visidata](http://reddit.com/r/visidata) on reddit
- [#visidata](irc://freenode.net/#visidata) on [freenode IRC](https://webchat.freenode.net)
- [saul@visidata.org](mailto:saul@visidata.org) to discuss feature requests and extensions
- [anja@visidata.org](mailto:anja@visidata.org) to discuss documentation/tests or to request tutorials


## Troubleshooting

*Whenever I try graphing, I get an empty chart*

Oh dear. Let us try to get to the bottom of this. Please run through the following options and contact us with the answers if the issue persists.

1. Is the terminal set to use 256 colors? Most terminals do support 256 colors, but may have a different default configuration. Try adding `TERM=xterm-256color` to your `~/.bashrc`.
2. Which terminal program are you using? If you are using a Mac, does the same thing happen in both iTerm and Mac Terminal?
3. What color theme is your terminal set to?  If you try with another theme, does that produce the same result?
4. Have you modified any other VisiData options (e.g. in `.visidatarc`)?  Particularly theme/display options.
