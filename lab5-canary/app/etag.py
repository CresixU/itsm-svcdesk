"""HTTP caching for ticket exports."""
import hashlib


def etag(body: bytes) -> str:
    """A weak ETag for an export; a content fingerprint, not a security control."""
    return 'W/"' + hashlib.sha1(body).hexdigest() + '"'
