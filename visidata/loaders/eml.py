import os

from visidata import VisiData, vd, Column, TableSheet, vlen

@VisiData.api
def open_eml(vd, p):
    return EmailSheet(p.base_stem, source=p)

class EmailSheet(TableSheet):
    rowtype = 'parts'  # rowdef: sub-Messages
    columns = [
        Column('filename', getter=lambda c,r: r.get_filename()),
        Column('content_type', getter=lambda c,r: r.get_content_type()),
        Column('payload', type=vlen, getter=lambda c,r: r.get_payload(decode=False)),
    ]
    def iterload(self):
        import email.parser
        parser = email.parser.Parser()
        with self.source.open(encoding='utf-8') as fp:
            yield from parser.parse(fp).walk()

@EmailSheet.api
def extract_part(sheet, givenpath, part):
    payload = part.get_payload(decode=True)
    if payload is None:
        vd.warning('empty payload')
    else:
        with givenpath.open_bytes(mode='w') as fp:
            fp.write(payload)

@EmailSheet.api
def extract_parts(sheet, givenpath, *parts):
    'Save all *parts* to Path *givenpath*.'
    vd.confirmOverwrite(givenpath, f'{givenpath} already exists, extract anyway?')

    vd.status('saving %s parts to %s' % (len(parts), givenpath.given))

    # forcibly specify save individual files into directory by ending path with /
    if givenpath.is_dir() or givenpath.given.endswith('/') or len(parts) > 1:
        # save as individual files in the givenpath directory
        try:
            os.makedirs(givenpath, exist_ok=True)
        except FileExistsError:
            vd.debug(f'{givenpath} already exists')

        for i, part in enumerate(parts):
            fn = part.get_filename() or f'part{i}'
            vd.execAsync(sheet.extract_part, givenpath / fn, part)
    elif len(parts) == 1:
        vd.execAsync(sheet.extract_part, givenpath, parts[0])
    else:
        vd.fail('cannot save multiple parts to non-dir')

EmailSheet.addCommand('x', 'extract-part', 'extract_part(inputPath("save part as: ", value=cursorRow.get_filename()), cursorRow)')
EmailSheet.addCommand('gx', 'extract-part-selected', 'extract_parts(inputPath("save %d parts in: " % nSelectedRows), *selectedRows)')
