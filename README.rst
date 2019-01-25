===========================================================================
Django Compresion Middleware: *Middleware to compress responses*
===========================================================================


Introduction
------------

This middleware implements compressed content encoding for HTTP. It is similar
to Django's ``GZipMiddleware`` (`documentation`_), but additionally supports
other compression methods. It is meant to be a drop-in replacement for Django's
``GZipMiddleware``.

The middleware is focussed on the task of compressing typical Django responses
such as HTML, JSON, etc.  For static file compression, have a look at other
projects such as `WhiteNoise`_.

Most browsers now support Brotli compresssion (check support status on `Can I
use... Brotli`_). The middleware will choose the best compression method
supported by the client. In order of preference:

- Brotli
- gzip

For example, Brotli is only used when the client has sent an ``Accept-Encoding``
header containing ``br``.

.. _`documentation`: https://docs.djangoproject.com/en/dev/ref/middleware/#module-django.middleware.gzip
.. _`WhiteNoise`: https://whitenoise.readthedocs.io/
.. _`Can I use... Brotli`: http://caniuse.com/#search=brotli

Installation
------------

- Supported Python versions: 2.7, 3.4, 3.5, 3.6 and 3.7.
  CPython and PyPy is supported.
- Supported Django versions: 1.11 (LTS), 2.0, 2.1.

.. code:: shell

    pip install --upgrade django-compression-middleware


Add ``compression_middleware.middleware.CompressionMiddleware`` to the
``MIDDLEWARE`` setting:

.. code:: python

    MIDDLEWARE = [
        'compression_middleware.middleware.CompressionMiddleware',
        # ...
    ]

Remove ``GZipMiddleware`` and ``BrotliMiddleware`` if you used it before.

Note that your browser might not send the ``br`` entry in the ``Accept-Encoding``
header when you test without HTTPS (common on localhost). You can force it to
send the header, though. In Firefox, visit ``about:config`` and set
``network.http.accept-encoding`` to indicate support. Note that you might
encounter some problems on the web with such a setting (which is why Brotli is
only supported on secure connections by default).

Credits and Resources
---------------------

The code and tests in this project is based on Django's ``GZipMiddleware`` and
Vašek Dohnal's ``django-brotli``. For compression, it uses:

- The `Brotli`_ bindings or `brotlipy`_. The latter is preferred on PyPy since
  it is implemented using cffi. But both should work on both Python
  implementations.
- Python's builtin `gzip`_ module.

.. _Brotli: https://pypi.org/project/Brotli/
.. _brotlipy: https://pypi.org/project/brotlipy/
.. _gzip: https://docs.python.org/3/library/gzip.html

Further readding on Wikipedia:

- `HTTP compression <https://en.wikipedia.org/wiki/HTTP_compression>`__
- `Brotli <https://en.wikipedia.org/wiki/Brotli>`__
- `gzip <https://en.wikipedia.org/wiki/Gzip>`__

Contributing
------------

1. Clone this repository (``git clone ...``)
2. Create a virtualenv
3. Install package dependencies: ``pip install --upgrade -r requirements_dev.txt``
4. Change some code
5. Run tests: in project root simply execute ``pytest``, but preferably ``tox``.
6. Submit a pull request :-)

License
-------

The MPL 2.0 License

Copyright (c) 2019 Friedel Wolff