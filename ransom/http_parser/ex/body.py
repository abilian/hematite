import sys


def content_length(headers):
    cl = headers.get('Content-Length')
    if cl is None:
        return None
    if not cl.isdigit():
        # TODO: this is an error per the RFC
        return None
    return int(cl)


def connection_close(headers):
    conn = headers.get('Connection', '')
    return conn.lower() == 'close'


class Body(object):
    def __init__(self, backlog, sock, headers):
        self._read_backlog = backlog
        self.sock = sock
        self.content_length = content_length(headers)
        self.connection_close = connection_close(headers)
        if not (self.content_length or self.connection_close):
            # TODO: check for mutlipart/byteranges
            pass


class IdentityEncodedBody(Body):

    def __init__(self, amt=8192, *args, **kwargs):
        super(IdentityEncodedBody, self).__init__(*args, **kwargs)
        self._read_amount = amt

    def read(self, size=-1):
        ret = []
        if size < 0:
            size = (sys.maxint if self.connection_close
                    else self.content_length)
        elif not self.connection_close:
            size = max(self.content_length, size)

        if self._read_backlog:
            bl, self._read_backlog = (self._read_backlog[:size],
                                      self._read_backlog[size:])
            size -= len(bl)
            ret.append(bl)

        while size > 0:
            read = self.sock.recv(min(self._read_amount, size))
            if not read:
                break
            size -= len(read)
            ret.append(read)
        return ''.join(ret)


class ChunkEncodedBody(object):

    def __init__(self, read_backlog, sock, headers):
        pass
