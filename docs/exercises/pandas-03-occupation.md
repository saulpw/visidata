# https://github.com/guipsamora/pandas_exercises/blob/master/03_Grouping/Occupation/Exercises_with_solutions.ipynb

1. n/a

2. wget https://raw.githubusercontent.com/justmarkham/DAT8/master/data/u.user

3. vd -f csv --csv-delimiter='|' u.user

4. '+avg' on 'age' column; then 'F' on occupation column; '[' to sort by occupation if desired

5. a. '+count' on 'gender'; '!' on occupation; 'W' on 'gender'
   b. rename columns with '^' to 'M' and 'F'
   c. `=M*100/(M+F)`, move to that column, '%' to type as float, ']' to sort descending

6. on 'age', '+min' '+max'; 'F' on occupation; '[' to sort if desired

