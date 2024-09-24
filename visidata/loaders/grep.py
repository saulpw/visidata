#!/usr/bin/python3

from visidata import vd, VisiData, JsonSheet, ColumnAttr, Path, ENTER, AttrDict, ExpectedException, stacktrace, TypedExceptionWrapper
import json
import os
from os import linesep

@VisiData.api
def open_grep(vd, p):
    return GrepSheet(p.base_stem, source=p)

@VisiData.api
def save_grep(vd, p, *vsheets):
    vd.save_jsonl(p, *vsheets)

def format_row(rowdict):
    # handle rows that are output of 'rg --json'
    if 'type' in rowdict and rowdict['type'] == 'match':
        match_data = rowdict['data']
        d = {
            'file':    match_data['path']['text'],
            'line_no': match_data['line_number'],
            'text':    match_data['lines']['text'].rstrip(linesep)
        }
        return AttrDict(d)
    # handle a .grep file that was saved by visidata, or
    # ripgrep rows that were preprocessed by jq:  'rg --json |jq [...]'
    if 'line_no' in rowdict:
        rowdict['text'] = rowdict['text'].rstrip(linesep)
        return AttrDict(rowdict)
    return None

class GrepSheet(JsonSheet):
    # The input file is in JSON Lines format, where each line describes a JSON object.
    # The JSON objects are either in the ripgrep grep_printer format:
    # https://docs.rs/grep-printer/0.1.0/grep_printer/struct.JSON.html
    # or contain the keys 'file', 'line_no', and 'text'.
    _rowtype = 'lines'  # rowdef: AttrDict

    columns = [
        ColumnAttr('file', type=str),
        ColumnAttr('line_no', type=int),
        ColumnAttr('text', type=str)
    ]
    nKeys = 2
    def iterload(self):
        with self.open_text_source() as fp:
            for L in fp:
                try:
                    if not L: # skip blank lines
                        continue
                    json_obj = json.loads(L)
                    if not isinstance(json_obj, dict):
                        vd.fail(f'line does not hold a JSON object:  {L}')
                    row = format_row(json_obj)
                    if not row: #skip lines that do not contain match data
                        continue
                    yield row
                except ValueError as e:
                    if self.rows:   # if any rows have been added already
                        e.stacktrace = stacktrace()
                        yield TypedExceptionWrapper(json.loads, L, exception=e)  # an error on one line
                    else:
                        # If input is not JSON, parse it as output of 'grep -n':  file:line_no:text
                        # If that does not parse, parse it as output of typical 'grep':  file:text
                        with self.open_text_source() as fp:
                            try:
                                extract_line_no = True
                                for L in fp:
                                    L = L.rstrip(linesep)
                                    sep1 = L.index(':')
                                    if extract_line_no:
                                        sep2 = L.find(':', sep1+1)
                                        try:
                                            if sep2 == -1: raise ValueError
                                            line_no = int(L[sep1+1:sep2]) # may raise ValueError
                                            if line_no < 1: raise ValueError
                                            text = L[sep2+1:]
                                        except ValueError: # if we can't find a line_no that is > 0, with a separator after it
                                            extract_line_no = False
                                            line_no = None
                                            text = L[sep1+1:]
                                    else:
                                        text = L[sep1+1:]
                                    yield AttrDict({'file':    L[:sep1],
                                                    'line_no': line_no,
                                                    'text':    text})
                            except ValueError:
                                vd.fail('file is not grep output')
                        break

    def afterLoad(self):
        if self.nRows == 0:
            vd.status('no grep results found in input data')

@GrepSheet.api
def sysopen_row(sheet, row):
    '''Open the file in an editor at the specific line.'''
    if sheet.nRows == 0: return
    try:
        given = row.file
        if vd.options.grep_base_dir and not os.path.isabs(given):
            given = vd.options.grep_base_dir + os.sep + row.file
        p = Path(given)
    except TypeError:
        vd.fail(f'cannot open row: {given}')
    if p.exists():
        # works for vim and emacsclient
        if row.line_no is not None:
            vd.launchEditor(p.given, f'+{row.line_no:d}')
        else:
            vd.launchEditor(p.given)
    else:
        vd.fail(f'cannot find file: {p.given}')

GrepSheet.addCommand(ENTER, 'sysopen-row', 'sysopen_row(cursorRow)', 'open current file in external $EDITOR, at the line')

vd.addGlobals({
    'GrepSheet': GrepSheet,
})
vd.option('grep_base_dir', None, 'base directory for relative paths opened with sysopen-row')
