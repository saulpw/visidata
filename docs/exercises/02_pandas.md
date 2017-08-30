[pandas_exercises 02](https://github.com/guipsamora/pandas_exercises/blob/master/01_Getting_%26_Knowing_Your_Data/Occupation/Exercise_with_Solution.ipynb)

1. pip3 install visidata
2. wget https://raw.githubusercontent.com/justmarkham/DAT8/master/data/u.user
3. vd -f csv --csv-delimiter="|" u.user
4. (look, move around)
5. 'gj' to go to bottom
6. see number of rows on lower right
7. ^G
8. C
9. no keys yet; press '!' on user_id to 'index' on that column
10. see 'type' column on Columns Sheet
11. (Print only the occupation column)
   a. on main sheet, '-' to hide all but user_id and occupation
or b. on columns sheet, select most rows ('s' on each manually) and 'g-' to hide all
12. g+distinct or 'F'
13. 'F'
14. descr'I'be all numeric columns
15. (same as 14)
16. (same as 14)
17. go to age column, #g+avg
18. '~' (to make string/categorical) and 'F', then 'gj'.
  BONUS:
   - note that there are several with count=1.
   - go to count column on count=1 row, press ',' to select those with count=1
   - 'q' and notice that they are selected on source sheet
   - press '"' to get only those selected rows on their own sheet
