# https://github.com/guipsamora/pandas_exercises/blob/master/04_Apply/US_Crime_Rates/Exercises_with_solutions.ipynb

1. 
2. wget https://raw.githubusercontent.com/guipsamora/pandas_exercises/master/04_Apply/US_Crime_Rates/US_Crime_Rates_1960_2014.csv
3. bin/vd !$
5. '@' on 'year' to convert to date
6. '!' on 'year' to set as key
4. go to 'C'olumns sheet,
   'g#' to set all non-keys as int
   'g+sum' to add sum aggr to them
   'e'dit population aggregators to 'max'
   'q'uit out
7. '-' on 'total' column
8. '~' on 'Year' (back to string), '=Year[:3]+"0s"' to create decade column ('^Decade' to rename if desired)
   b. 'F' on decade column
9. 'C'olumns, 'g+keymax', 'zF', 'M' to melt/transpose into 
   ...but we don't want max absolute anyway, we want max pct/population

