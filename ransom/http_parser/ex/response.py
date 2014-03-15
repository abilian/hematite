
import socket
from collections import namedtuple
from ransom.http_parser.ex import core
from ransom.http_parser.ex import headers as h
from ransom.http_parser.ex import body as b
from ransom.compat import BytestringHelper, bio_from_socket
from ransom.constants import REASON_CODES


# TODO: timeouts


class ResponseException(Exception):
    pass


class RequestURITooLarge(ResponseException, core.OverlongRead):
    status_code = REASON_CODES['Request-URI Too Large']


class RawResponse(namedtuple('RawResponse', 'status_line headers body'),
               BytestringHelper):

    def to_io(self, io_obj):
        self.status_line.to_io(io_obj)
        self.headers.to_io(io_obj)
        io_obj.write(b'\r\n')

    @classmethod
    def from_io(cls, io_obj):
        status_line = h.StatusLine.from_io(io_obj)
        headers = h.Headers.from_io(io_obj)
        bcls = (b.ChunkEncodedBody
                if cls._is_chunked(headers)
                else b.IdentityEncodedBody)

        return cls(status_line, headers, bcls(io_obj, headers))

    @core._callable_staticmethod
    def _is_chunked(headers):
        # 4.4 #2
        try:
            return headers['transfer-encoding'].lower() != 'identity'
        except KeyError:
            return False

    @property
    def is_chunked(self):
        return self._is_chunked(self.headers)


def test(addr, host, url):
    c = socket.create_connection(addr)
    reql = bytes(h.RequestLine('GET',
                               url,
                               h.HTTPVersion(1, 1)))
    headers = bytes(h.Headers([('Host', host),
                               ('Accept-Encoding', 'chunked'),
                               ('TE', 'chunked')]))
    req = reql + headers + '\r\n\r\n'
    c.sendall(req)
    resp = RawResponse.from_io(bio_from_socket(c, mode='rb'))
    if resp.is_chunked:
        body = []
        while True:
            chunk = resp.body.read_chunk()
            if not chunk:
                break
            body.append(chunk)
        body = ''.join(body)
    else:
        body = resp.body.read()
    return resp, body


if __name__ == '__main__':
    test(('localhost', 8080), host='localhost', url=h.URL('/'))
