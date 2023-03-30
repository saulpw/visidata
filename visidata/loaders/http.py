from visidata import Path, RepeatFile, vd, VisiData
from visidata.loaders.tsv import splitter

content_filetypes = {
    'tab-separated-values': 'tsv'
}

vd.option('http_max_next', 0, 'max next.url pages to follow in http response') #848
vd.option('http_req_headers', {}, 'http headers to send to requests')


@VisiData.api
def openurl_http(vd, path, filetype=None):
    schemes = path.scheme.split('+')
    if len(schemes) > 1:
        sch = schemes[0]
        openfunc = getattr(vd, f'openhttp_{sch}', vd.getGlobals().get(f'openhttp_{sch}'))
        if not openfunc:
            vd.fail(f'no vd.openhttp_{sch}')
        return openfunc(Path(schemes[-1]+'://'+path.given.split('://')[1]))

    import urllib.request
    import urllib.error
    import mimetypes

    # fallback to mime-type
    req = urllib.request.Request(path.given, **vd.options.getall('http_req_'))
    response = urllib.request.urlopen(req)

    contenttype = response.getheader('content-type')
    subtype = contenttype.split(';')[0].split('/')[-1]

    filetype = filetype or vd.guessFiletype(path, funcprefix='guessurl_').get('filetype')
    filetype = filetype or content_filetypes.get(subtype, subtype)
    filetype = filetype or vd.guessFiletype(path).get('filetype')

    # Automatically paginate if a 'next' URL is given
    def _iter_lines(path=path, response=response, max_next=vd.options.http_max_next):
        path.responses = []
        n = 0
        while response:
            path.responses.append(response)
            with response as fp:
                for line in splitter(response, delim=b'\n'):
                    yield line.decode(vd.options.encoding)

            linkhdr = response.getheader('Link')
            src = None
            if linkhdr:
                links = urllib.parse.parse_header(linkhdr)
                src = links.get('next', {}).get('url', None)

            if not src:
                break

            n += 1
            if n > max_next:
                vd.warning(f'stopping at max {max_next} pages')
                break

            vd.status(f'fetching next page from {src}')
            response = requests.get(src, stream=True, **vd.options.getall('http_req_'))

    # add resettable iterator over contents as an already-open fp
    path.fptext = RepeatFile(_iter_lines())

    return vd.openSource(path, filetype=filetype)


VisiData.openurl_https = VisiData.openurl_http
