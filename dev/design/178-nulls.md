# Null values

In version 1.3 and earlier, there were several options like `empty_is_null` to determine which values counted as null.  But this was poorly-defined and not implemented consistently.  After 1.3 it was simplified to:

1. The null values are:
   a. None
   b. the options.null_value (default None)

2. Null values interact with:
   a. aggregation: the denominator counts only non-null values
   b. descr`I`be: only null values count in the nulls column
   c. `f`ill only null values
   d. `M`elt only non-null values
   e. go to prev/next null (`z<` and `z>`)
