import sys

from .dictutils import OrderedMultiDict, OMD
from io import StringIO


def make_BytestringHelperMeta(target):
    class BytestringHelperMeta(type):
        def __new__(cls, name, bases, attrs):
            if "to_bytes" in attrs:
                attrs[target] = attrs["to_bytes"]
            return super().__new__(cls, name, bases, attrs)

    return BytestringHelperMeta


from urllib.parse import (
    urlparse,
    urlunparse,
    urljoin,
    urlsplit,
    urlencode,
    quote,
    unquote,
    quote_plus,
    unquote_plus,
    urldefrag,
    parse_qsl,
)
from urllib.request import parse_http_list
from http import cookiejar as cookielib
from http.cookies import Morsel
from socket import SocketIO

str = str
bytes = bytes

BytestringHelperMeta = make_BytestringHelperMeta(target="__bytes__")
BytestringHelper = BytestringHelperMeta("BytestringHelper", (object,), {})


# from boltons
def make_sentinel(name="_MISSING", var_name=None):
    class Sentinel:
        def __init__(self):
            self.name = name
            self.var_name = var_name

        def __repr__(self):
            if self.var_name:
                return self.var_name
            return f"{self.__class__.__name__}({self.name!r})"

        if var_name:

            def __reduce__(self):
                return self.var_name

        def __bool__(self):
            return False

    return Sentinel()
