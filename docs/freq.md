# Frequency Table Reference

the below also applies to the [PivotSheet]

## binning

### discrete binning
-
### numeric binning
- separate error/null bins
### bin display
### number of bins
### errors

## commands tables
- inline commands.tsv entries
   - global: zF gF F
   - FreqTable
      - ENTER/gENTER

- selection propagation
- freeze-sheet with g' to get an plain data sheet with the same data

## options table

- `disp_histogram`
- `disp_histlen`
- `histogram_bins`

## aggregators

# Internals

- source is the source sheet
- rowdef: FreqRow(pivot)
  - .pivotrows = { aggvalue: list(values) }
- numeric bin keys
- nonKeyVisibleCols
- [PivotTable] Column.aggvalue
- addAggregateCols
- groupRows
