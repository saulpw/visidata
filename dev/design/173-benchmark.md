# Benchmark

Using an interactive tool or the commandline (no scripts):

1. load/parse the dataset
2. clean various issues with the dataset
   - remove all X
   - simple subst of all foo to bar (in this column only--foo is in other columns too)
3. summarize
   - group by year (partial date)
   - sum on float col
   - sort result numerically
   - filter out results with count < 3
4. save as tsv
   - remove all but the 3 columns wanted

SQL can do most of this if the data is in a database first.

## Use this valid jsonl dataset

- utf8, a mix of 1x, 1.5x, 2x, and ambiguous width characters
- jsonl
- some rows missing some fields
- first row not having all the fields
- some cells null
- an overlong cell
- embedded spaces, newlines, tabs, nulls, other control characters
