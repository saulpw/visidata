from visidata import Path, RepeatFile, options, vd, VisiData

content_filetypes = {
    'tab-separated-values': 'tsv'
}

vd.option('http_max_next', 0, 'max next.url pages to follow in http response') #848


@VisiData.api
def openurl_http(vd, path, filetype=None):
    schemes = path.scheme.split('+')
    if len(schemes) > 1:
        sch = schemes[0]
        openfunc = getattr(vd, f'openhttp_{sch}', vd.getGlobals().get(f'openhttp_{sch}'))
        if not openfunc:
            vd.fail(f'no vd.openhttp_{sch}')
        return openfunc(Path(schemes[-1]+'://'+path.given.split('://')[1]))

    import requests

    response = requests.get(path.given, stream=True)
    response.raise_for_status()

    if not filetype:
        # try auto-detect from extension
        ext = path.suffix[1:].lower()
        openfunc = getattr(vd, f'open_{ext}', vd.getGlobals().get(f'open_{ext}'))

        if openfunc:
            filetype = ext
        else:
            # if extension unknown, fallback to mime-type
            contenttype = response.headers['content-type']
            subtype = contenttype.split(';')[0].split('/')[-1]
            filetype = content_filetypes.get(subtype, subtype)

    # If no charset is provided by response headers, use the user-specified
    # encoding option (which defaults to UTF-8) and hope for the best.  The
    # alternative is an error because iter_lines() will produce bytes.  We're
    # streaming so can't use response.apparent_encoding.
    if not response.encoding:
        response.encoding = options.encoding

    # Automatically paginate if a 'next' URL is given
    def _iter_lines(path=path, response=response, max_next=options.http_max_next):
        path.responses = []
        n = 0
        while response:
            path.responses.append(response)
            yield from response.iter_lines(decode_unicode=True)

            src = response.links.get('next', {}).get('url', None)
            if not src:
                break

            n += 1
            if n > max_next:
                vd.warning(f'stopping at max {max_next} pages')
                break

            vd.status(f'fetching next page from {src}')
            response = requests.get(src, stream=True)

    # add resettable iterator over contents as an already-open fp
    path.fp = RepeatFile(_iter_lines())

    return vd.openSource(path, filetype=filetype)

VisiData.openurl_https = VisiData.openurl_http
