# -*- coding: utf-8 -*-

from io import BytesIO

from raw.headers import StatusLine, Headers, HTTPVersion
from raw.response import RawResponse

from headers import CAP_MAP, default_header_to_bytes, default_header_from_bytes
from fields import RESPONSE_FIELDS

_DEFAULT_VERSION = HTTPVersion(1, 1)


class Response(object):
    # TODO: from_request convenience method?
    def __init__(self, status_code, body, **kw):
        self.status_code = status_code
        self.reason = kw.pop('reason', '')  # TODO look up
        self._raw_headers = kw.pop('headers', Headers())  # TODO
        self.version = kw.pop('version', _DEFAULT_VERSION)

        self._body = body

        self._load_headers()
        # TODO: lots
        return

    # TODO: could use a metaclass for this, could also build it at init
    _header_field_map = dict([(hf.http_name, hf) for hf in RESPONSE_FIELDS])
    locals().update([(hf.attr_name, hf) for hf in RESPONSE_FIELDS])

    def _load_headers(self):
        self.headers = Headers()
        # plenty of ways to arrange this
        hf_map = self._header_field_map
        for hname, hval in self._raw_headers.items(multi=True):
            # TODO: folding
            try:
                norm_hname = CAP_MAP[hname.lower()]
                field = hf_map[norm_hname]
            except KeyError:
                # preserves insertion order and duplicates
                self.headers.add(hname, default_header_from_bytes(hval))
            else:
                field.__set__(self, hval)

    def _get_header_dict(self, drop_empty=True):
        # TODO: option for unserialized?
        ret = Headers()
        hf_map = self._header_field_map
        for hname, hval in self.headers.items(multi=True):
            if drop_empty and hval is None or hval == '':
                # TODO: gonna need a field.is_empty or something
                continue
            try:
                field = hf_map[hname]
            except KeyError:
                ret.add(hname, default_header_to_bytes(hval))
            else:
                ret.add(hname, field.to_bytes(hval))
        return ret

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
        bio = BytesIO(bytestr)
        rr = RawResponse.from_io(bio)
        return cls.from_raw_response(rr)

    def to_bytes(self):
        rr = self.to_raw_response()
        rrio = BytesIO()
        rr.to_io(rrio)
        return rrio.getvalue()

    def validate(self):
        pass


if __name__ == '__main__':
    main()
