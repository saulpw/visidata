# ZettelData

Turns a directory of .org or .md files into database that can be worked like a Zettelkasten.

## Supported syntax

- `--- [comment]` at start of line starts a new section
- any number of `#` or `*` (followed by a space) leads a headline
- `#+key: value` adds metadata to next element (headline, table, section, )
- `:tag1:tag2:`
- `[[tagname]]` links to that set of tags
- `[[url]]` links to external url
- `[[url][linktext]]` links to url with linktext
- all other markup/orgmode/whatever is ignored and passed through

## Usage

From CLI:

- `vd file.org`
- or `find orgfiles -name '*.org' | vd -f forg`

Then within VisiData:

- `(` and `)` family of commands opens row(s) instead of columns.
- Enter to dive into one item in visidata
  - `g Enter` to dive into multiple items
- `Ctrl+O` to open with external editor
- select rows and then `gy` to cut and `p` to paste into the current item.
- `d` to delete rows and then `z Ctrl+S` to commit the changes


## Design thoughts

- The zettel should be atomic, but too many individual files require specialized tools and workflows.
- A small book should be one file; a large book maybe one file per chapter.


