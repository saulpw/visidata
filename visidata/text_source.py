import re

from visidata import vd, BaseSheet

vd.option('regex_skip', '', 'regex of lines to skip in text sources', help='regex')
vd.option('regex_flags', 'I', 'flags to pass to re.compile() [AILMSUX]', replay=True)

@BaseSheet.api
def regex_flags(sheet):
    'Return flags to pass to regex functions from options'
    return sum(getattr(re, f.upper()) for f in sheet.options.regex_flags)


class FilterFile:
    def __init__(self, fp, regex:str, regex_flags:int=0):
        import re
        self._fp = fp
        self._regex_skip = re.compile(regex, regex_flags)

    def readline(self) -> str:
        while True:
            line = self._fp.readline()
            if self._regex_skip.match(line):
                continue
            return line

    def __getattr__(self, k):
        return getattr(self._fp, k)

    def __iter__(self):
        return self

    def __next__(self):
        line = self.readline()
        if not line:
            raise StopIteration
        return line

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        return self._fp.__exit__(*args, **kwargs)


@BaseSheet.api
def open_text_source(sheet):
    'Open sheet source as text, using sheet options for encoding and regex_skip.'
    fp = sheet.source.open(encoding=sheet.options.encoding, encoding_errors=sheet.options.encoding_errors)
    regex_skip = sheet.options.regex_skip
    if regex_skip:
        return FilterFile(fp, regex_skip, sheet.regex_flags())
    return fp
