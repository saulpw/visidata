
The process of designing a sheet is:

1. Create a subclass of Sheet.
2. Define `reload()` member to collect the rows from the sources.  Document the row definition (rowdef).
3. Declare the available columns.
4. Create a command to instantiate the Sheet subclass.
5. Seed the workflow with the obvious commands.
6. Make a test .vd demonstrating the functionality of the new sheet and its commands.

