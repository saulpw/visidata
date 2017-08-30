# (pandas_exercises 01)[https://github.com/guipsamora/pandas_exercises/blob/master/01_Getting_%26_Knowing_Your_Data/Chipotle/Exercise_with_Solutions.ipynb]

1. pip3 install visidata
2. wget https://raw.githubusercontent.com/justmarkham/DAT8/master/data/chipotle.tsv
3. vd chipotle.tsv
  - alt: curl !$ | vd
4. (look at the screen)
5. (look in the lower right for row count)
6. ^G for # columns
7. 'C' to see all columns
8. n/a
9. go to item_name and press 'F', see top item
10. (look at 'count' column)
11. 'q', go to choice_description, 'F' again; ignore NULL row
12. ['q' again] go to quantity,  '#' to turn into an int, 'g+sum', see status
13. go to item_price, '$' to strip leading chars and turn into float
14. 'g+sum'
15. go to order_id, 'g+distinct'
16. go to item_price, '+sum', go to order_id, 'F', go to sum_item_price, 'g+avg', see status
17. 'q', go to item_name, either 'g+distinct' and look at status, or 'F' and view # rows

