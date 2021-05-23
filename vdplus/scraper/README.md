# Web Scraping with VisiData

## Usage

To open a url in RequestsSheet:

    vd -f scrape <url>

- When scraping, web responses are cached in a sqlite db in `.visidata` directory

- `Enter` (`open-row`) to open row as list of HTMLElements

## HTMLElements

HTMLElements Sheet is list of elements as parsed by `beautifulsoup4`.

Standard VisiData exploration techniques can be used to find relevant data, which will help determine the proper selector to use.

- `Enter` to dive into children of cursor element (or children of all selected rows with `g Enter`).
- `go` to batch open links in selected rows on new RequestsSheet, which will fetch each page.
- on RequestsSheet, `;` (addcol-selector) to add column of elements matching given css selector.
    - this is how to cross-tabulate data from multiple pages
    - join multiple elements together using the `soupstr` type (bound to `~` on the HTMLElementsSheet).
