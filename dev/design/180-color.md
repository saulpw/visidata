# Colors

Take all applied color options
- apply all binary curses attributes from by any colorizer that fires
   - attributes: reverse, bold, underline; possibly also dim and/or blink in some terminals
- apply the highest-precedent color; precedence is hard-coded in the option or colorizer

a) if optname is None, then use the return value of the colorfunc as the colornamestr to apply
b) sort and combine the option names and memoize the resulting attr
