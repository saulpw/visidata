from functools import partial

from visidata import *

# Commands known to not work
# ^ Rename current column (and related commands; fails with view_pandas)


class StaticFrameAdapter:

    def __init__(self, frame):
        import static_frame as sf
        if not isinstance(frame, sf.Frame):
            vd.fail('%s is not a StaticFrame Frame' % type(frame).__name__)
        self.frame = frame

    def __len__(self):
        if 'frame' not in self.__dict__:
            return 0
        return len(self.frame)

    def __getitem__(self, k):
        if isinstance(k, slice):
            return StaticFrameAdapter(self.frame.iloc[k])
        return self.frame.iloc[k] # return a Series

    def __getattr__(self, k):
        if 'frame' not in self.__dict__:
            raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{k}'")
        return getattr(self.frame, k)

    def pop(self, k):
        row = self.frame.iloc[k]
        self.frame = self.frame.drop.iloc[k]
        return row.values.tolist()

    def insert(self, k, row):
        import static_frame as sf
        f = sf.Frame.from_records([row], columns=self.frame.columns)
        self.frame = sf.Frame.from_concat((
                self.frame.iloc[0: k],
                f,
                self.frame.iloc[k:],
                ), index=sf.IndexAutoFactory)


class StaticFrameSheet(Sheet):
    '''Sheet sourced from a static_frame.Frame

    Note:
        Columns starting with "__vd_" are reserved for internal usage
        by the VisiData loader.
    '''

    def dtype_to_type(self, dtype):
        import numpy as np

        if dtype == bool:
            return bool
        if dtype.kind == 'U':
            return str
        if dtype.kind == 'M':
            return date
        if np.issubdtype(dtype, np.integer):
            return int
        if np.issubdtype(dtype, np.floating):
            return float
        return anytype

    @property
    def frame(self):
        if isinstance(getattr(self, 'rows', None), StaticFrameAdapter):
            return self.rows.frame

    @frame.setter
    def frame(self, val):
        if isinstance(getattr(self, 'rows', None), StaticFrameAdapter):
            # If we already have a rows attribute and it is a SFA, then we assume val us a Frame and inject it intot the SFA
            self.rows.frame = val
        else:
            self.rows = StaticFrameAdapter(val)
        self.name = '' if val.name is None else val.name

    def getValue(self, col, row):
        '''Look up column values in the underlying Frame.'''
        return col.sheet.frame.loc[row.name, col.name]

    def setValue(self, col, row, val):
        '''
        Update a column's value in the underlying Frame, loosening the
        column's type as needed.
        '''
        dtype_old = col.sheet.frame.dtypes[col.name]
        f = col.sheet.frame.assign.loc[row.name, col.name](val)
        dtype_new = f.dtypes[col.name]
        if dtype_old != dtype_new:
            vd.warning(f'Type of {val} does not match column {col.name}. Changing type.')
            col.type = self.dtype_to_type(dtype_new)
        # assign back to frame, convert to StaticFrameAdapter
        self.rows = StaticFrameAdapter(f)

    def reload(self):
        import static_frame as sf

        if isinstance(self.source, sf.Frame):
            frame = self.source
        elif isinstance(self.source, Path):
            filetype = getattr(self, 'filetype', self.source.ext)
            if filetype == 'tsv':
                readfunc = sf.Frame.from_tsv
            if filetype == 'csv':
                readfunc = sf.Frame.from_csv
            elif filetype == 'json':
                readfunc = sf.Frame.from_json
            else:
                vd.error('no supported import for:' + filetype)
            frame = readfunc(str(self.source))
        else:
            # we might introspect self.source to introduce more handling
            try:
                frame = sf.Frame(self.source)
            except ValueError as err:
                vd.fail('error building Frame from source data: %s' % err)

        # If the index is not an IndexAutoFactory, try to move it onto the Frame. If this fails it might mean we are trying to unset an auto index post selection
        if frame.index.depth > 1 or frame.index._map: # if it is not an IndexAutoFactory
            frame = frame.unset_index()

        # VisiData assumes string column names
        if frame.columns.dtype != str:
            frame = frame.relabel(columns=frame.columns.astype(str))

        dtypes = frame.dtypes

        self.columns = []
        for col in (c for c in frame.columns if not c.startswith("__vd_")):
            self.addColumn(Column(
                col,
                type=self.dtype_to_type(dtypes[col]),
                getter=self.getValue,
                setter=self.setValue
            ))

        self.rows = StaticFrameAdapter(frame)
        self._selectedMask = sf.Series.from_element(False, index=frame.index)

    @asyncthread
    def sort(self):
        '''Sort rows according to the current self._ordering.'''
        by_cols = []
        ascending = []
        for col, reverse in self._ordering[::-1]:
            by_cols.append(col.name)
            ascending.append(not reverse)

        # NOTE: SF does not yet support ascending per column yet; just take the first
        self.rows = StaticFrameAdapter(self.rows.frame.sort_values(
                by_cols,
                ascending=ascending[0]),
                )

    def _checkSelectedIndex(self):
        import static_frame as sf
        if self._selectedMask.index is not self.frame.index:
            # selection is no longer valid
            vd.status('sf.Frame.index updated, clearing {} selected rows'
                      .format(self._selectedMask.sum()))
            self._selectedMask = sf.Series.from_element(False, index=self.frame.index)

    def rowid(self, row):
        return getattr(row, 'name', None) or ''

    def isSelected(self, row):
        if row is None:
            return False
        self._checkSelectedIndex()
        return self._selectedMask.loc[row.name]

    def selectRow(self, row):
        'Select given row'
        self._checkSelectedIndex()
        self._selectedMask = self._selectedMask.assign.loc[row.name](True)

    def unselectRow(self, row):
        self._checkSelectedIndex()
        is_selected = self._selectedMask.loc[row.name]
        self._selectedMask = self._selectedMask.assign.loc[row.name](False)
        return is_selected

    @property
    def nSelectedRows(self):
        self._checkSelectedIndex()
        return self._selectedMask.sum()

    @property
    def selectedRows(self):
        import static_frame as sf

        self._checkSelectedIndex()
        # NOTE: we expect to have already moved a real index onto the Frame by the time this is called; this selection will create a new index that is not needed, so replace it with an IndexAutoFactory
        f = self.frame.loc[self._selectedMask].relabel(sf.IndexAutoFactory)
        return StaticFrameAdapter(f)

    # Vectorized implementation of multi-row selections
    @asyncthread
    def select(self, rows, status=True, progress=True):
        self.addUndoSelection()
        for row in (Progress(rows, 'selecting') if progress else rows):
            self.selectRow(row)

    @asyncthread
    def unselect(self, rows, status=True, progress=True):
        self.addUndoSelection()
        for row in (Progress(rows, 'unselecting') if progress else rows):
            self.unselectRow(row)

    def clearSelected(self):
        import static_frame as sf
        self._selectedMask = sf.Series.from_element(False, index=self.frame.index)

    def selectByIndex(self, start=None, end=None):
        self._checkSelectedIndex()
        self._selectedMask = self._selectedMask.assign.iloc[start:end](True)

    def unselectByIndex(self, start=None, end=None):
        self._checkSelectedIndex()
        self._selectedMask = self._selectedMask.assign.iloc[start:end](False)

    def toggleByIndex(self, start=None, end=None):
        self._checkSelectedIndex()
        self.addUndoSelection()
        self._selectedMask = self._selectedMask.assign.iloc[start:end](
                ~self._selectedMask.iloc[start:end])

    def _selectByILoc(self, mask, selected=True):
        self._checkSelectedIndex()
        self._selectedMask = self._selectedMask.assign.iloc[mask](selected)

    @asyncthread
    def selectByRegex(self, regex, columns, unselect=False):
        '''
        Find rows matching regex in the provided columns. By default, add
        matching rows to the selection. If unselect is True, remove from the
        active selection instead.
        '''
        import static_frame as sf
        import re

        columns = [c.name for c in columns]
        flags = re.I if 'I' in vd.options.regex_flags else None
        masks = self.frame[columns].via_re(regex, flags).search()
        if unselect:
            self._selectedMask = self._selectedMask & ~masks.any(axis=1)
        else:
            self._selectedMask = self._selectedMask | masks.any(axis=1)

    def addUndoSelection(self):
        vd.addUndo(undoAttrCopyFunc([self], '_selectedMask'))

    @property
    def nRows(self):
        if self.frame is None:
            return 0
        return len(self.frame)

    def newRows(self, n):
        '''
        Return n rows of empty data.
        '''
        import static_frame as sf
        def items():
            for col, dtype in zip(self.frame.columns, self.frame.dtypes):
                array = np.empty(n, dtype=dtype)
                array.flags.writeable = False
                yield col, array
        return sf.Frame.from_items(items())

    def addRows(self, rows, index=None, undo=True):
        import static_frame as sf

        # identify empty rows and expand them to column width with None
        rows_exp = []
        for row in rows:
            if len(row) == 0:
                rows_exp.append(
                        list(None for _ in range(len(self.frame.columns)))
                        )
            else:
                rows_exp.append(row)

        if index is None:
            index = len(self.frame) # needed for undo
            f = sf.Frame.from_records(rows_exp, columns=self.frame.columns)
            self.frame = sf.Frame.from_concat(self.frame, f, index=sf.IndexAutoFactory)
        else:
            f = sf.Frame.from_records(rows_exp, columns=self.frame.columns)
            self.frame = sf.Frame.from_concat((
                    self.frame.iloc[0: index],
                    f,
                    self.frame.iloc[index:],
                    ), index=sf.IndexAutoFactory)

        self._checkSelectedIndex()
        if undo:
            vd.addUndo(self._deleteRows, range(index, index + len(rows)))

    def _deleteRows(self, which):
        import static_frame as sf
        self.frame = self.frame.drop.iloc[which].reindex(sf.IndexAutoFactory)
        self._checkSelectedIndex()

    def addRow(self, row, index=None):
        self.addRows([row], index)
        vd.addUndo(self._deleteRows, index or self.nRows - 1)

    def delete_row(self, rowidx):
        import static_frame as sf
        oldrow = self.frame.iloc[rowidx].values.tolist() # a series

        vd.addUndo(self.addRows, [oldrow], rowidx, False)
        self._deleteRows(rowidx)
        vd.memory.cliprows = [oldrow]

    def deleteBy(self, by):
        '''Delete rows for which func(row) is true.  Returns number of deleted rows.'''
        import static_frame as sf
        oldidx = self.cursorRowIndex
        nRows = self.nRows
        vd.addUndo(setattr, self, 'frame', self.frame)

        self.frame = self.frame[~by].reindex(sf.IndexAutoFactory)
        ndeleted = nRows - self.nRows

        vd.status('deleted %s %s' % (ndeleted, self.rowtype))
        return ndeleted

    def deleteSelected(self):
        '''Delete all selected rows.'''
        self.deleteBy(self._selectedMask)



class StaticFrameIndexSheet(IndexSheet):
    rowtype = 'sheets'
    columns = [
        Column('sheet', getter=lambda col, row: row.source.name),
        ColumnAttr('name', width=0),
        ColumnAttr('nRows', type=int),
        ColumnAttr('nCols', type=int),
    ]

    nKeys = 1
    def iterload(self):
        for sheetname in self.source.keys():
            # this will combine self.name, sheetname into one name
            yield StaticFrameSheet(self.name, sheetname, source=self.source[sheetname])



def view_sf(container):
    import static_frame as sf

    name = '' if container.name is None else container.name

    # multi-Frame containers
    if isinstance(container, sf.Bus):
        run(StaticFrameIndexSheet(name, source=container))
    elif isinstance(container, sf.Batch):
        run(StaticFrameIndexSheet(name, source=container.to_bus()))
    # Frame-like containers
    elif isinstance(container, sf.Quilt):
        run(StaticFrameSheet(name, source=container.to_frame()))
    # convertable to a Frame
    elif isinstance(container, sf.Series):
        run(StaticFrameSheet(name, source=container.to_frame()))
    elif isinstance(container, sf.Index):
        run(StaticFrameSheet(name, source=container.to_series().to_frame()))
    elif isinstance(container, sf.IndexHierarchy):
        run(StaticFrameSheet(name, source=container.to_frame()))
    # Frame
    else:
        run(StaticFrameSheet(name, source=container))


# Override with vectorized implementations
StaticFrameSheet.addCommand(None, 'stoggle-rows', 'toggleByIndex()', 'toggle selection of all rows')
StaticFrameSheet.addCommand(None, 'select-rows', 'selectByIndex()', 'select all rows')
StaticFrameSheet.addCommand(None, 'unselect-rows', 'unselectByIndex()', 'unselect all rows')

StaticFrameSheet.addCommand(None, 'stoggle-before', 'toggleByIndex(end=cursorRowIndex)', 'toggle selection of rows from top to cursor')
StaticFrameSheet.addCommand(None, 'select-before', 'selectByIndex(end=cursorRowIndex)', 'select all rows from top to cursor')
StaticFrameSheet.addCommand(None, 'unselect-before', 'unselectByIndex(end=cursorRowIndex)', 'unselect all rows from top to cursor')
StaticFrameSheet.addCommand(None, 'stoggle-after', 'toggleByIndex(start=cursorRowIndex)', 'toggle selection of rows from cursor to bottom')
StaticFrameSheet.addCommand(None, 'select-after', 'selectByIndex(start=cursorRowIndex)', 'select all rows from cursor to bottom')
StaticFrameSheet.addCommand(None, 'unselect-after', 'unselectByIndex(start=cursorRowIndex)', 'unselect all rows from cursor to bottom')


StaticFrameSheet.addCommand(None, 'random-rows', 'nrows=int(input("random number to select: ", value=nRows)); vs=copy(sheet); vs.name=name+"_sample"; vs.rows=StaticFrameAdapter(sheet.frame.sample(nrows or nRows)); vd.push(vs)', 'open duplicate sheet with a random population subset of N rows'),
StaticFrameSheet.addCommand(None, 'random-columns', 'ncols=int(input("random number to select: ", value=nCols)); vs=copy(sheet); vs.name=name+"_sample"; vs.source=sheet.frame.sample(columns=(ncols or nCols)); vd.push(vs)', 'open duplicate sheet with a random population subset of N columns'),

# Handle the regex selection family of commands through a single method,
# since the core logic is shared
StaticFrameSheet.addCommand('|', 'select-col-regex', 'selectByRegex(regex=input("select regex: ", type="regex", defaultLast=True), columns=[cursorCol])', 'select rows matching regex in current column')
StaticFrameSheet.addCommand('\\', 'unselect-col-regex', 'selectByRegex(regex=input("select regex: ", type="regex", defaultLast=True), columns=[cursorCol], unselect=True)', 'unselect rows matching regex in current column')
StaticFrameSheet.addCommand('g|', 'select-cols-regex', 'selectByRegex(regex=input("select regex: ", type="regex", defaultLast=True), columns=visibleCols)', 'select rows matching regex in any visible column')
StaticFrameSheet.addCommand('g\\', 'unselect-cols-regex', 'selectByRegex(regex=input("select regex: ", type="regex", defaultLast=True), columns=visibleCols, unselect=True)', 'unselect rows matching regex in any visible column')

# Override with a pandas/dataframe-aware implementation
StaticFrameSheet.addCommand('"', 'dup-selected', 'vs=StaticFrameSheet(sheet.name, "selectedref", source=selectedRows.frame); vd.push(vs)', 'open duplicate sheet with only selected rows')

