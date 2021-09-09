# Hematite

Fork developer note: this is being ported to Python 3. 

This is still a massive WIP, though.

---

A full-featured and high-accuracy implementation of HTTP/1.1 in pure
Python. Core features:

  * Unified Request/Response primitives for server-side and client-side
  * Async-compatible, reentrant, streaming HTTP parser, based on Python generators (coroutines)
  * Built-in nonblocking HTTP client
  * WSGI-compatible

Hematite is still very much a work in progress, but feel free to
`python setup.py develop` and try out some examples!
