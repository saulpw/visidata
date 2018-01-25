## misc. notes

These don't have a clear home, but should be moved when one is found.

### colors

- Get a curses attr with `colors[options.color_foo]`

- Combine colors with `attr, precedence = colors.update(attr, oldprecedence, options.color_bar, newprecedence)`
    - attributes are additive only.
    - unknown colors are ignored.
    - once a color is in the attribute, further colors are ignored at the same precedence.
    - colors (but not attributes) replace at higher precedence.
    - thus 'bold 217 blue' means "bold+217", unless 217 is not a valid color (non-256 color terminal), in which case it means "bold+blue"
