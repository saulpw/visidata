
# VisiData types must be callable and idempotent

But, the essential problem with len as type is that it isn't idempotent; len(len(L)) is not valid--all other VisiData types can do that.

The classic VisiData types are: anytype, str, int, float, currency (dirty float), and date.

There's some special case code for anytype detecting that the cell is a list or dict, and displaying it differently.
Of course I wanted to sort by the length, so I would wind up creating a `len(col)` and setting it to int and then sorting by that.

But at one point, I thought, could the base value be a list, and len be the "type"?  I tried it out, and it basically worked.
But, the essential problem with len as type is that it isn't idempotent; len(len(L)) is not valid--all other VisiData types can do that.

So now there is a `vlen` type, which subclasses `int` and provides a `__len__`.  Useful for columns with compound objects; `z#` sets a column to `len` type.

--- 2019-Jan-25
