# Design notes for cell errors

- disp_error_note appears in cells with errors
- error message itself does not appear (cell value is blank)
- z^E on that cell shows error and stacktrace
- F (freq-column) on column with errors shows only one error per type (errors are grouped by string repr)
- freq key columns for error bins have error note
- error messages should be displayed in freq sheet values for those bins (to differentiate error types)
- z^E (error-cell) on F key for error shows at least stringified error (ideally would show stacktrace)
- ENTER (dive-row) on F error row goes to list of source rows with that error, named <sheet>_errors
- type and format errors should display similarly to how they display on source sheets
   - test by making a column with both errors and non-ints an int column, and Freqing it
- sort column with errors should work, putting errors at one end of the list or the other
- Freq/Pivot group should be by visible format string, not typed value
- nulls on typed columns are shown as null on the freq/pivot sheet (not textified 'None' nor error)
