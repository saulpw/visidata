'''Loader for the jrnl.sh CLI journal file format'''

import re


from visidata import VisiData, TableSheet, ItemColumn, AttrDict


@VisiData.api
def open_jrnl(vd, p):
    return JrnlSheet(p.base_stem, source=p)


class JrnlSheet(TableSheet):
    # rowdef: AttrDict
    columns = [
        ItemColumn('date'),
        ItemColumn('time'),
        ItemColumn('title'),
        ItemColumn('body'),
        ItemColumn('tags'),
    ]
    def iterload(self):
        re_title = re.compile(r'\[(.*?)\s(.*?)\] (.*)')
        prevline = ''
        for line in self.source:
            tags = re.findall(r'(?<!\S)(@[-+*#/\w]+)', line)
            if not prevline:
                m = re_title.match(line)
                if m:
                    row = AttrDict()
                    row.date, row.time, row.title = m.groups()
                    row.body = ''
                    row.tags = ' '.join(tags)
                    yield row
                    continue

            row.body += line + '\n'
            row.tags = ' '.join([row.tags]+tags)
            prevline = line.strip()


@VisiData.api
def save_jrnl(vd, p, *vsheets):
    with p.open(mode='w', encoding=vsheets[0].options.save_encoding) as fp:
        for vs in vsheets:
            for r in vs.iterrows():
                fp.write(f'[{r.date} {r.time}] {r.title}\n')
                body = r.body.strip()
                if body:
                    fp.write(body + '\n')
                fp.write('\n')
