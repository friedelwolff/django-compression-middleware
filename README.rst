===========================================================================
Django Compression Middleware
===========================================================================


This middleware implements compressed content encoding for HTTP. It is similar
to Django's ``GZipMiddleware`` (`documentation`_), but additionally supports
other compression methods. It is meant to be a drop-in replacement for Django's
``GZipMiddleware``. Its documentation — including security warnings — therefore
apply here as well.

The middleware is focussed on the task of compressing typical Django responses
such as HTML, JSON, etc.  Both normal (bulk) and streaming responses are
supported. For static file compression, have a look at other projects such as
`WhiteNoise`_.

Zstandard is a new method for compression with little client support so far.
Most browsers now support Brotli compression (check support status on `Can I
use... Brotli`_). The middleware will choose the best compression method
supported by the client as indicated in the request's ``Accept-Encoding``
header. In order of preference:

- Zstandard
- Brotli
- gzip

Summary of the project status:

* .. image:: https://travis-ci.org/friedelwolff/django-compression-middleware.svg?branch=master
     :target: https://travis-ci.org/friedelwolff/django-compression-middleware
* .. image:: https://img.shields.io/pypi/djversions/django-compression-middleware.svg
* .. image:: https://img.shields.io/pypi/pyversions/django-compression-middleware.svg
* .. image:: https://img.shields.io/pypi/implementation/django-compression-middleware.svg

.. _`documentation`: https://docs.djangoproject.com/en/dev/ref/middleware/#module-django.middleware.gzip
.. _`WhiteNoise`: https://whitenoise.readthedocs.io/
.. _`Can I use... Brotli`: http://caniuse.com/#search=brotli

Installation and usage
----------------------

The following requirements are supported and tested in all reasonable
combinations:

- Python versions: 2.7, 3.4, 3.5, 3.6, 3.7.
- Interpreters: CPython and PyPy.
- Django versions: 1.11 (LTS), 2.0, 2.1.

.. code:: shell

    pip install --upgrade django-compression-middleware

To apply compression to all the views served by Django, add
``compression_middleware.middleware.CompressionMiddleware`` to the
``MIDDLEWARE`` setting:

.. code:: python

    MIDDLEWARE = [
        # ...
        'compression_middleware.middleware.CompressionMiddleware',
        # ...
    ]

Remove ``GZipMiddleware`` and ``BrotliMiddleware`` if you used it before.
Consult the Django documentation on the correct `ordering of middleware`_.

.. _`ordering of middleware`: https://docs.djangoproject.com/en/dev/ref/middleware/#module-django.middleware.gzip

Alternatively you can decorate views individually to serve them with
compression:

.. code:: python

    from compression_middleware.decorators import compress_page

    @compress_page
    def index_view(request):
        ...

Note that your browser might not send the ``br`` entry in the ``Accept-Encoding``
header when you test without HTTPS (common on localhost). You can force it to
send the header, though. In Firefox, visit ``about:config`` and set
``network.http.accept-encoding`` to indicate support. Note that you might
encounter some problems on the web with such a setting (which is why Brotli is
only supported on secure connections by default).

Credits and Resources
---------------------

The code and tests in this project are based on Django's ``GZipMiddleware`` and
Vašek Dohnal's ``django-brotli``. For compression, it uses the following modules
to bind to fast C modules:

- The `zstandard`_ bindings. It supports both a C module (for CPython) and CFFI
  which should be appropriate for PyPy. See the documentation for full details.
- The `Brotli`_ bindings or `brotlipy`_. The latter is preferred on PyPy since
  it is implemented using cffi. But both should work on both Python
  implementations.
- Python's builtin `gzip`_ module.

.. _zstandard: https://pypi.org/project/zstandard/
.. _Brotli: https://pypi.org/project/Brotli/
.. _brotlipy: https://pypi.org/project/brotlipy/
.. _gzip: https://docs.python.org/3/library/gzip.html

Further readding on Wikipedia:

- `HTTP compression <https://en.wikipedia.org/wiki/HTTP_compression>`__
- `Zstandard <http://www.zstd.net/>`__
- `Brotli <https://en.wikipedia.org/wiki/Brotli>`__
- `gzip <https://en.wikipedia.org/wiki/Gzip>`__

Contributing
------------

1. Clone this repository (``git clone ...``)
2. Create a virtualenv
3. Install package dependencies: ``pip install --upgrade -r requirements_dev.txt``
4. Change some code
5. Run the tests: in the project root simply execute ``pytest``, and afterwards
   preferably ``tox`` to test the full test matrix. Consider installing as many
   supported interpreters as possible (having them in your ``PATH`` is often
   sufficient).
6. Submit a pull request and check for any errors reported by the Continuous
   Integration service.

License
-------

The MPL 2.0 License

Copyright (c) 2019 `Friedel Wolff <https://fwolff.net.za/>`_.
