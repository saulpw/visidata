# How can I move around and search?

- basic movement just like vim
  - 'G' 'gg' '^G' work as in vim, as do some of the 'z' scroll commands
- 'g' prefix goes all the way
.  'gh' (or g Left) already goes to the first column, but maybe '0' should also.
- (call out no number prefix?)
- '/' and '?' search for regex, 'n' and 'N' continue.  These should work just like in vim but only within a single column.
  - 'g' searches across all columns
- 'gr'/'gc' go to a specific row or column by number
- 'r' and 'c' go by row key or column name

i
  - 'g' and 'z' are also command prefixes in vd, but in vd they generally means something like 'g'lobal/embi'g'gen and 'z'croll/'z'mallify.  
