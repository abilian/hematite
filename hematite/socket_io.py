
import os
import io
import errno
import socket
from threading import Lock

import hematite.compat as compat
import hematite.raw.core as core


def eagain(characters_written=0):
    err = io.BlockingIOError(errno.EAGAIN,
                             os.strerror(errno.EAGAIN))
    err.characters_written = characters_written
    return err


class NonblockingBufferedReader(io.BufferedReader):
    linebuffer_lock = Lock()

    def __init__(self, *args, **kwargs):
        super(NonblockingBufferedReader, self).__init__(*args, **kwargs)
        self.linebuffer = []

    def readline(self, limit=None):
        with self.linebuffer_lock:
            line = super(NonblockingBufferedReader, self).readline(limit)
            if not line:
                return line

            self.linebuffer.append(line)
            if not core.LINE_END.search(line):
                raise eagain()
            line, self.linebuffer = ''.join(self.linebuffer), []
            return line


class NonblockingSocketIO(compat.SocketIO):
    backlog_lock = Lock()

    def __init__(self, *args, **kwargs):
        super(NonblockingSocketIO, self).__init__(*args, **kwargs)
        self.write_backlog = ''

    # TODO: better name (seems verby almost like flush)
    @property
    def empty(self):
        return not self.write_backlog

    def write(self, data=None):
        with self.backlog_lock:
            data = data or self.write_backlog
            written = super(NonblockingSocketIO, self).write(data)
            if written is None:
                raise eagain()
            self.write_backlog = data[written:]
            if self.write_backlog:
                raise eagain()


def readline(io_obj, sock):
    # pulled from the old _select.py
    try:
        return core.readline(io_obj)
    except core.EndOfStream:
        try:
            if not sock.recv(1, socket.MSG_PEEK):
                raise
        except socket.error as e:
            if e.errno != errno.EAGAIN:
                raise
        raise io.BlockingIOError(None, None)


def iopair_from_socket(sock):
    writer = NonblockingSocketIO(sock, "rwb")
    reader = NonblockingBufferedReader(writer)
    return reader, writer
