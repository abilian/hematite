# -*- coding: utf-8 -*-


from hematite import serdes
from hematite.fields import RESPONSE_FIELDS
from hematite.constants import CODE_REASONS
from hematite.socket_io import iopair_from_socket, readline

# capital M stands out more, less likely to have a conflict
from hematite.raw import messages as M
from hematite.raw.body import ChunkEncodedBody
from hematite.raw.response import RawResponse
from hematite.raw.envelope import ResponseEnvelope
from hematite.raw.envelope import StatusLine, Headers, HTTPVersion


_DEFAULT_VERSION = HTTPVersion(1, 1)


class Response(object):
    # TODO: from_request convenience method?
    def __init__(self, status_code, body=None, **kw):
        self.status_code = int(status_code)
        self.reason = kw.pop('reason', None)
        if self.reason is None:
            self.reason = CODE_REASONS.get(self.status_code, '')
        self._raw_headers = kw.pop('headers', Headers())  # TODO
        self.version = kw.pop('version', _DEFAULT_VERSION)

        self._body = body
        self._data = None

        self._init_headers()
        # TODO: lots
        return

    # TODO: could use a metaclass for this, could also build it at init
    _header_field_map = dict([(hf.http_name, hf) for hf in RESPONSE_FIELDS])
    locals().update([(hf.attr_name, hf) for hf in RESPONSE_FIELDS])
    _init_headers = serdes._init_headers
    _get_header_dict = serdes._get_headers

    @property
    def is_chunked(self):
        return isinstance(self._body, ChunkEncodedBody)

    def _load_data(self):
        if self.is_chunked:
            chunk_list = []
            while True:
                chunk = self._body.read_chunk()
                if not chunk:
                    break
                chunk_list.append(chunk)
            data = ''.join(chunk_list)
        else:
            data = self._body.read()
        self._data = data

    def get_data(self, as_bytes=True):
        if self._data is None:
            self._load_data()
        if as_bytes:
            return self._data
        try:
            charset = self.content_type.charset
            return self._data.decode(charset)
        except:
            # TODO: what to do here?
            pass
        return self._data

    @classmethod
    def from_raw_response(cls, raw_resp):
        sl = raw_resp.status_line
        kw = {'status_code': sl.status_code,
              'reason': sl.reason,
              'version': sl.version,
              'headers': raw_resp.headers,
              'body': raw_resp.body}
        return cls(**kw)

    def to_raw_response(self):
        status_line = StatusLine(self.version, self.status_code, self.reason)
        headers = self._get_header_dict()
        return RawResponse(status_line, headers, self._body)

    @classmethod
    def from_bytes(cls, bytestr):
        raw_resp = RawResponse.from_bytes(bytestr)
        return cls.from_raw_response(raw_resp)

    def to_bytes(self):
        raw_resp = self.to_raw_response()
        return raw_resp.to_bytes()

    @classmethod
    def from_io(cls, io_obj):
        raw_resp = RawResponse.from_io(io_obj)
        return cls.from_raw_response(raw_resp)

    def to_io(self, io_obj):
        raw_resp = self.to_raw_response()
        return raw_resp.to_io(raw_resp)

    def validate(self):
        pass


class _State(object):
    # TODO: ssl_connect?
    (NotStarted, LookupHost, Connect, SendRequestHeaders, SendRequestBody,
     ReceiveResponseHeaders, ReceiveResponseBody, Complete) = range(8)


class ClientResponse(Response):
    # TODO: are we going to need want_read/want_write for SSL?

    def __init__(self, client, request=None):
        self.client = client
        self.request = request
        self.raw_request = request.to_request_envelope()
        self.state = _State.NotStarted
        self.socket = None
        self.timings = {}

        self.raw_response = ResponseEnvelope()
        self._resp_body = None
        self._resp_body_parts = []

        self._writer_iter = self.raw_request._make_writer()
        # TODO: request body/total bytes uploaded counters
        # TODO: response body/total bytes downloaded counters
        # (for calculating progress)

    def process(self):
        if self.request is None:
            raise ValueError('request not set')
        state, request = self.state, self.request
        if state is _State.NotStarted:
            self.addrinfo = self.client.get_addrinfo(request)
            self.state += 1
        elif state is _State.Connect:
            self.socket = self.client.get_socket(request, self.addrinfo)
            self._reader, self._writer = iopair_from_socket(self.socket)
            self.state += 1
        elif state is _State.SendRequestHeaders:
            pass

        # TODO: return socket

    def fileno(self):
        if self.socket:
            return self.socket.fileno()
        return -1  # or raise an exception?

    def write_request_headers(self):
        if not self.writer.empty:
            self.writer.write(None)

        next_bit = next(self._writer_iter, M.Empty)
        if next_bit is M.Empty:
            self.state = self.output_envelope.state
            return True
        self.writer.write(next_bit.value)
        return False

    def read_response_headers(self):
        while not self.complete:
            if self.state.type == M.NeedLine.type:
                line = readline(self.reader, self.sock)
                next_state = M.HaveLine(value=line)
            else:
                raise RuntimeError('Unknown state {0}'.format(self.state))
            self.state = self.output_envelope.reader.send(next_state)
        assert self.complete, "Unknown state {0}".format(self.state)
        return self.complete


class Joinable(object):
    "just a sketch of an interface"

    # TODO: attribute/property?
    def want_read(self):
        pass

    def want_write(self):
        pass

    def do_read(self):
        pass

    def do_write(self):
        pass
