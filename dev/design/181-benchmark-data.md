# Benchmark Dataset

- a coherent, grounded, interesting dataset--probably fictional/manufactured
   - multi-culti/topical; maybe call it "benchmark-2018" and imply future releases
   - with some insights and/or mystery to be solved
   - time/effort required to answer some associated questions are the actual benchmark

- 50-100 rows
- 10-20 columns
   - column with mixed currency
   - lat/long floats
   - nested objects (lists/dicts)
   - unicode names (including east asian half, full, ambiguous widths)
   - date
      - birthdate?
      - some clearly bogus (future/1970/1969/1900) entries
      - weekend pattern
- many types of common errors that can be cleaned
   - like 100 mini-puzzles in one dataset
   - can require deduction about data generally (27/5/84 is reasonable as D/M/YY date)
   - but not anything that requires domain knowledge ()
   - no implication about the central plot or mystery should be in the mistakes
      - an easter egg though could be a pattern of typos by the same enterer mentioned by name in the same dataset

- metadata above header row

columns that require transformation:
   - combined columns (name+address)
   - too-wide (needs to be melted)

with cells that have errors/issues:
   - embedded NULs, spaces, tabs, newlines, other control chars, all manner of unicode spaces and ZWJ
   - float in int column
   - "header" cells with unfilled cells below
   - categorical typos
   - null/None
   - absent value
   - a much too long cell 

- (do not just make up any actual numbers; think about where those numbers come from and derive them from other, more basic numbers, instead)
