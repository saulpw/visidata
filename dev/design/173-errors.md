# Grouping Errors and Nulls

a) rollups of all typed columns with errors and None values keep the display on screen and and in newly saved data
b) [all] distinct Exceptions and None values are not grouped together in any context
c) [melt] Nones do not show up for value fields in melt, errors do for now
d) [describe] Nones and errors are not considered when calculating descriptive statistics
e) [pivot] errors (values or in the key column for pivot) are grouped together by their error message and would ideally be displayed similarly on all derivative sheets.

## notes 

- 'None' refer to values that are Python None, and not just nulls by e.g. `zero_is_null`
- filtering by `is_null` is applied *after* typing
