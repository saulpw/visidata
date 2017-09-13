# https://github.com/guipsamora/pandas_exercises/blob/master/02_Filtering_%26_Sorting/Chipotle/Exercises_with_solutions.ipynb

1. n/a
2. wget https://raw.githubusercontent.com/justmarkham/DAT8/master/data/chipotle.tsv
3. n/a
4. a. move to item_price and press '$'
   b. create new column with comparison  `=item_price>10`
   c. move to that column and press 'F', see number of True
5. a. go to item_name and '!', same with 'quantity' (to do this with their workflow)
   b.  move to item_price and `+min` [to get min(price) in the next step]
   c.  'gF' to group by those keys ("remove duplicates")
   d.  move to quantity and press ',' to select quantity=1, then " to get only those
   e.  hide quantity column with '-'
   f.  move 

5. alternate:
   a. set type of quantity to int with '#'
   b. `=item_price/quantity` to create a column with per_item_price
   c. (opt) '^' to rename column to per_item_price if you wish
   d. `+avg` on per_item_price
   e. move to item_name and `F`
   f. move to avg_per_item_price and ']' to sort descending
   g. (opt) go to Columns sheet and unhide 'count' ('e'dit width to non-zero)

6. move to item_name and '[' to sort ascending
7. move to item_price, '[' to sort descending, 'cquan' to move to quantity column
8. 'F' on item_name, /Veggie Salad Bowl, see count
  alt: g/Veggie Salad Bowl, `,"`, see num rows
9. a. 'F' on item_name, ENTER on "Canned Soda" rows to get only those rows from source sheet
   b. `=quantity>1`, `,` on a True row, " to see only those.
   b alt: 'F' on that column, see number of True

