# Frequency Tables are how you GROUP BY

Frequency Tables group rows into bins by column value, and includes summary columns for source columns with aggregators.

Set `--numeric-binning` to bin numeric rows into ranges instead of discrete values.

- {help.commands.freq_col}

- {help.commands.freq_keys}

- {help.commands.freq_summary} 

## Aggregators

A **Frequency Table** contains a summary columns for each aggregator added to a source column.
These aggregators need to be added before creating the Frequency Table.
Examples of aggregators include min, max, sum, distinct, count, and list.

- {help.commands.aggregate-col}

Note: set an appropriate type for the aggregator target column, for example {help.commands.type_float}.

## Explore the data

Dive into a group to see the underlying row(s) using the **Frequency Table**:

- {help.commands.open_row}
- {help.commands.dive_selected}

Select a group to select all of its underlying rows in the source sheet.

## Using Split Panes with Frequency Tables

Press `Shift+Z` to open a split pane, and then `Shift+F` to create a **Frequency Table**. The **Frequency Table** will automatically open in the other pane.

See the `SplitpanesGuide` for more.

#### Options

- {help.options.disp_histogram}
- {help.options.histogram_bins}
- {help.options.numeric_binning}
