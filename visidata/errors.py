from visidata import vd, VisiData, ExpectedException, options, stacktrace

@VisiData.global_api
def exceptionCaught(vd, exc=None, **kwargs):
    'Maintain list of most recent errors and return most recent one.'
    if isinstance(exc, ExpectedException):  # already reported, don't log
        return
    vd.lastErrors.append(stacktrace())
    if kwargs.get('status', True):
        vd.status(vd.lastErrors[-1][-1], priority=2)  # last line of latest error
    if options.debug:
        raise
