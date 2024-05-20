import re

from visidata import Path, RepeatFile, vd, VisiData
from visidata.loaders.tsv import splitter

vd.option('http_max_next', 0, 'max next.url pages to follow in http response') #848
vd.option('http_req_headers', {}, 'http headers to send to requests')
vd.option('http_ssl_verify', True, 'verify host and certificates for https')


@VisiData.api
def guessurl_mimetype(vd, path, response):
    content_filetypes = {
        'tab-separated-values': 'tsv'
    }

    for k in dir(vd):
        if k.startswith('open_'):
            ft = k[5:]
            content_filetypes[ft] = ft

    contenttype = response.getheader('content-type')
    subtype = contenttype.split(';')[0].split('/')[-1]
    if subtype in content_filetypes:
        return dict(filetype=content_filetypes.get(subtype), _likelihood=10)



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

    ctx = None
    if not vd.options.http_ssl_verify:
        import ssl

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(path.given, **vd.options.getall('http_req_'))
    try:
        response = urllib.request.urlopen(req, context=ctx)
    except urllib.error.HTTPError as e:
        vd.fail(f'cannot open URL: HTTP Error {e.code}: {e.reason}')
    except urllib.error.URLError as e:
        vd.fail(f'cannot open URL: {e.reason}')

    filetype = filetype or vd.guessFiletype(path, response, funcprefix='guessurl_').get('filetype')  # try guessing by url
    filetype = filetype or vd.guessFiletype(path, funcprefix='guess_').get('filetype')  # try guessing by contents

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
                links = parse_header_links(linkhdr)
                link_data = {}
                for link in links:
                    key = link.get('rel') or link.get('url')
                    link_data[key] = link
                src = link_data.get('next', {}).get('url', None)

            if not src:
                break

            n += 1
            if n > max_next:
                vd.warning(f'stopping at max next pages: {max_next} pages')
                break

            vd.status(f'fetching next page from {src}')
            req = urllib.request.Request(src, **vd.options.getall('http_req_'))
            response = urllib.request.urlopen(req)

    # add resettable iterator over contents as an already-open fp
    path.fptext = RepeatFile(_iter_lines())

    return vd.openSource(path, filetype=filetype)

def parse_header_links(link_header):
    '''Return a list of dictionaries:
    [{'url': 'https://example.com/content?page=1', 'rel': 'prev'},
     {'url': 'https://example.com/content?page=3', 'rel': 'next'}]
    Takes a link header string, of the form
    '<https://example.com/content?page=1>; rel="prev", <https://example.com/content?page=3>; rel="next"'
    See https://datatracker.ietf.org/doc/html/rfc8288#section-3
    '''

    links = []
    quote_space = ' \'"'
    link_header = link_header.strip(quote_space)
    if not link_header: return []
    for link_value in re.split(', *<', link_header):
        if ';' in link_value:
            url, params = link_value.split(';', maxsplit=1)
        else:
            url, params = link_value, ''
        link = {'url': url.strip('<>' + quote_space)}

        for param in params.split(';'):
            if '=' in param:
                key, value = param.split('=')
                key = key.strip(quote_space)
                value = value.strip(quote_space)
                link[key] = value
            else:
                break
        links.append(link)
    return links

VisiData.openurl_https = VisiData.openurl_http
