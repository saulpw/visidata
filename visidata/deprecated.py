import visidata


def deprecated(ver):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # ideally would include a stacktrace
            visidata.warning(f'{func.__name__} deprecated since v{ver}')
            return func(*args, **kwargs)
        return wrapper
    return decorator


@deprecated('1.6')
def copyToClipboard(value):
    return visidata.clipboard().copy(value)
