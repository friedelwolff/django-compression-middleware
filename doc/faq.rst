=========
Questions
=========

- What about the `BREACH attack`_?

  Django provides mitigations against the BREACH attack since version 1.10. For
  additional protection, you can consider ``django-debreach`` and rate limiting.
  If you are using the builtin CSRF mechanisms (i.e. not roling your own), you
  are probably safe as far as BREACH is concerned.

.. _BREACH attack: http://breachattack.com/

- Why not implement each possible encoding as its own middleware and apply them
  in order?

  While this is a clean design, it suffers from a few shortcomings. It requires
  developers / system administrators to add multiple middlewares for a single
  concern, and it might duplicate some functionality, such as parsing the
  ``Accept-Encoding`` header.

- Why not let the web server handle the compression?

  It is a good idea to let the web server handle the compression, as it might be
  more optimised for it, and it frees up your application resources for handling
  the application. This middleware is appropriate for cases where the webserver
  is not able to do it or does not support the latest compression algorithms.
  Moreover, compression in middleware unlocks the possibility of caching
  compressed pages which might be beneficial in some cases.

- What about streaming responses?

  Just like ``GZipMiddleware``, streaming responses are supported, and the
  compressed data is streamed as it becomes available from the compressor.

- What about compression with the deflate algorithm?

  The deflate algorithm provides very little benefit over gzip in terms of
  compression — it is actually the same algorithm, but using 11 bytes less
  overhead. Due to historical incompatibilities most people prefer gzip over
  deflate. There is no realistic chance today of a client supporting deflate
  that doesn't also support gzip.

- What about compression with the SDCH algorithm? (Or bzip2, lma, xz...)

  These are not in IANA's `content coding registry`_ and are not widely
  supported by clients.

.. _content coding registry: https://www.iana.org/assignments/http-parameters/http-parameters.xhtml#content-coding


- Does this provide any real value over Django's ``GZipMiddleware``?

  Brotli promises better compression using less CPU time, and fast
  decompression. It is now widely supported in browsers. For small responses
  the effects of any compression algorithm is likely to be small. For a small
  web response of a few KB Brotli is unlikely to need less MTUs than gzip. It
  should use slightly less CPU time for compression and decompression than
  gzip, but the difference will be small. In terms of total time in the
  request-response cycle over the internet, you are unlikely to save more than
  a millisecond. For larger responses, the effects become more pronounced, and
  you might benefit in the order of multiple milliseconds compared to gzip.
  Naturally this all depends heavily on the content of the response, the server
  and client CPUs and the attributes of the network connection.

  Django compression middleware tries to choose parameters so that using Brotli
  should usually use less CPU time and result in a smaller response than with
  gzip. If you specifically target very slow or very fast connections, a slight
  tweak to the compression level might provide a slightly better balance of
  priorities.

- Isn't compression of small responses a waste of time?

  It could well be. Django compression middleware addresses this in two ways:

  - We check if the response after compression is smaller by some margin. If it
    isn't, the uncompressed response is sent.
  - If the response is very small before compression, it is sent uncompressed.

  All of this means that users and system administrators should benefit
  regardless of whether they are on fast or slow connections or computers. The
  benefit in any specific case might be small, but you should benefit in
  aggregate spread over all your responses.

