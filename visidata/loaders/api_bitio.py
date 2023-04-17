
from visidata import *

vd.option('bitio_api_key', '', 'API key')

@VisiData.api
def new_bitio(vd, p):
    vd.importExternal('bitdotio')
    vd.requireOptions('bitio_api_key', help='https://docs.bit.io/docs/connecting-via-the-api')
    return BitioReposSheet(p.name, source=p)

vd.openhttp_bitio = vd.new_bitio

@VisiData.lazy_property
def bitio_client(vd):
    import bitdotio
    return bitdotio.bitdotio(vd.options.bitio_api_key)

@VisiData.api
def bitio_api(vd, path, method, **kwargs):
    t = vd.bitio_client.api_client.call_api(path, method,
            header_params={'Accept': 'application/json',
                           'Authorization': 'Bearer '+vd.bitio_client.access_token,
                           'Content-Type': 'application/json'}, async_req=True, body=kwargs)
    if not t.successful():
        vd.warning(resp['Reason'])
    return t.get()


class BitioReposSheet(Sheet):
    rowtype = 'repos'
    columns = [
        AttrColumn('name'),
        AttrColumn('creator'),
        AttrColumn('owner'),
        AttrColumn('bytes', type=int, width=0),
        AttrColumn('collaborators'),
        AttrColumn('description'),
        AttrColumn('documentation'),
        AttrColumn('endpoints'),
        AttrColumn('is_private'),
        AttrColumn('license'),
        AttrColumn('query_count'),
        AttrColumn('stars'),
        AttrColumn('tables'),
        AttrColumn('url'),
        AttrColumn('watchers'),
    ]
    defer = True
    def iterload(self):
        yield from vd.bitio_client.list_repos(self.source.name)


    @asyncthread
    def putChanges(self):
        adds, mods, dels = self.getDeferredChanges()
        for row in dels.values():
            vd.bitio_api(f'/users/{self.source.name}/repos/{row.name}/', 'DELETE')

        for row, rowmods in Progress(list(mods.values()), gerund="updating"):
            kwargs = {col.name: val for col, val in rowmods.items()}
            vd.bitio_api(f'/users/{self.source.name}/repos/{row.name}/', 'PATCH', **kwargs)

    def openRow(self, row):
        return BitioRepoSheet(self.source.name, row.name, source=row)


class BitioRepoSheet(Sheet):
    rowtype = 'tables'
    columns = [
        AttrColumn('url'),
        AttrColumn('current_name'),
        AttrColumn('description'),
        AttrColumn('columns'),
        AttrColumn('num_records', type=int),
        AttrColumn('bytes', type=int),
        AttrColumn('repo'),
        AttrColumn('documentation'),
    ]
    def iterload(self):
        yield from vd.bitio_client.list_tables(self.source.owner.split('/')[-2], self.source.name)

    def openRow(self, row):
        username = row.repo.split('/')[-4]
        repo = row.repo.split('/')[-2]
        return BitioTable(username, repo, source=row)


class BitioTable(Sheet):
    def iterload(self):
        username = self.source.repo.split('/')[-4]
        repo = self.source.repo.split('/')[-2]
        conn = vd.bitio_client.get_connection()
        with conn.cursor() as cur:
            cur.execute(f'SELECT * FROM "{username}/{repo}"."{self.source.current_name}"')
            r = cur.fetchone()
            if r:
                yield r
            self.columns = []
            for c in vd.postgresGetColumns(cur):
                self.addColumn(c)
            yield from cur
