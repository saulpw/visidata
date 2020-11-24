
Data gravitates toward tabular form: tables of rows and columns
(why spreadsheets are so popular)
Even non-tabular data (video, geospatial, text) can be meaningfully represented as tabular data in any number of ways.
And metadata is tabular too.

The ideal table structure:

- each row is an "observation"
- each column is an attribute of that observation
- some columns refer to columns in other tables

## Cell-oriented (Spreadsheet)

- anything goes
- immediate, responsive
- presentation-oriented
- lingua franca of the business world
- normal people think in terms of cells
- lineage: VisiCalc - 1-2-3 - Quattro - Excel - Google Sheets
- languages: COBOL, FORTRAN, C

## Column-oriented (APL, Pandas)

- algorithmically efficient, both conceptually and in execution (though maybe not in memory)
- Notation as a Tool of Thought - Iverson
   1967, Iverson APL defines a small set of algorithmic building blocks that cover a vast algorithmic space.
   - lineage: APL -> J -> K
- DataFrames bind columns together.

This is the right approach for high-performance data processing.

## Row-oriented (SQL)

Data is generally acquired and stored as rows.
RDBMS are great for a robust, large-scale, systematic approach to data.

- input constraints enforce structural cleanliness (incl types and relationships)
- lingua franca of IT
- fundamentally row oriented: best for adding and filtering data
- how most data is transmitted and stored
- downside: performance for column-oriented operations


# Platforms

- Python has a rich data ecosystem with modules, internal and external, for dealing with data in all kinds of different formats.
- The terminal is a mature, efficient, and universal interface.
   (Web/API/REST trades efficiency for monetization)




## Hierarchical (JSON, XML)


# other platforms trying to unify the data space

## nushell
## datasette

