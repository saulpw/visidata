
postgres loader

notes:
  - use 'vd postgres://username:password@hostname:port/database' to connect
    - shows list of all user tables
    - press ENTER goes to that table
  - entire table (all columns) queried and loaded into memory, batched with psycopg2's default of 2000 per query

  - shows tables with ncols/nrows
     - fills in nrows in the background (new feature)
     - each nrows cell results in a thread spawning to do a SELECT COUNT(*)
future:
  - allow edits and deletes, place in a queue, commit the queue separately in a transaction
  - only get rows visible onscreen
