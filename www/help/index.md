## Troubleshooting

*Whenever I try graphing, I get an empty chart*

1. Is the terminal set to use 256 colors? Most terminals do support 256 colors, but may have a different default configuration. Try adding `TERM=xterm-256color` to your `~/.bashrc`.
2. Which terminal program are you using? If you are using a Mac, does the same thing happen in both iTerm and Mac Terminal?
3. What color theme is your terminal set to?  If you try with another theme, does that produce the same result?
4. Have you modified any other VisiData options (e.g. in `.visidatarc`)?  Particularly theme/display options.
