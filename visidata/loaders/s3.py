from visidata import openurl_https, Path
from urllib.parse import urlparse

def openurl_s3(path, filetype=None):
    import boto3

    s3_url = urlparse(path.given)

    https_url = boto3.client("s3").generate_presigned_url(
        "get_object",
        Params={
            "Bucket": s3_url.netloc,
            "Key": s3_url.path.lstrip("/"),
        },
        ExpiresIn=5*60,     # seconds
    )

    return openurl_https(Path(https_url), filetype=filetype)
