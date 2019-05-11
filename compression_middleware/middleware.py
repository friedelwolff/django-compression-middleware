# -*- encoding: utf-8 -*-
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Based on Django's gzip middleware
#        - Copyright (c) Django Software Foundation and individual contributors.
#        - 3-clause BSD
#    and django-brotli
#        - Copyright (c) 2016–2017 Vašek Dohnal (@illagrenan)
#        - MIT Licence


__all__ = ['CompressionMiddleware']


from .br import brotli_compress, brotli_compress_stream
from .zstd import zstd_compress, zstd_compress_stream

from django.middleware.gzip import (
        compress_string as gzip_compress,
        compress_sequence as gzip_compress_stream,
)
from django.utils.cache import patch_vary_headers

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError: # pragma: no cover
    MiddlewareMixin = object


# Minimum response length before we'll consider compression. Small responses
# won't necessarily be smaller after compression, and we want to save at least
# enough to make the time expended worthwhile. Since MTUs around 1500 are
# common, and HTTP headers are often more than 500 bytes (more so if there
# are cookies), we guess that responses smaller than 500 bytes is likely to fit
# in the MTU (or not) mostly due to other factors, not compression.
MIN_LEN = 500

# The compression has to reduce the length, otherwise we're just fooling
# around. Since we'll have to add the Content-Encoding header, we need to
# make that addition worthwhile, too. So the compressed response must be
# smaller by some margin. This value should be at least 24 which is
# len("Content-Encoding: gzip\r\n"), but a bigger value could reflect that a
# non-trivial improvement in transfer time is required to make up for the time
# required for decompression. An improvement of a few bytes is unlikely to
# actually reduce the network communication in terms of MTUs.
MIN_IMPROVEMENT = 100


# supported encodings in order of preference
# (encoding, bulk_compressor, stream_compressor)
compressors = (
        ('zstd', zstd_compress, zstd_compress_stream),
        ('br', brotli_compress, brotli_compress_stream),
        ('gzip', gzip_compress, gzip_compress_stream),
)


def encoding_name(s):
    """Obtain 'br' out of ' br;q=0.5' or similar."""
    # We won't break if the ordering is specified with q=, but we ignore it.
    # Only a quality level of 0 is honoured -- in such a case we handle it as
    # if the encoding wasn't specified at all.
    if ';' in s:
        s, q = s.split(';')
        if '=' in q:
            _, q = q.split('=')
            if float(q) == 0.0:
                return None
    return s.strip()


def compressor(accept_encoding):
    # We don't want to process extremely long headers. It might be an attack:
    accept_encoding = accept_encoding[:200]
    client_encodings = set(encoding_name(e) for e in accept_encoding.split(','))
    if "*" in client_encodings:
        # Our first choice:
        return compressors[0]
    for encoding, compress_func, stream_func in compressors:
        if encoding in client_encodings:
            return (encoding, compress_func, stream_func)
    return (None, None, None)


class CompressionMiddleware(MiddlewareMixin):
    """
    This middleware compresses content based on the Accept-Encoding header.

    The Vary header is set for the sake of downstream caches.
    """
    def process_response(self, request, response):
        # Test a few things before we even try:
        #  - content is already encoded
        #  - really short responses are not worth it
        if \
                response.has_header('Content-Encoding') or \
                (not response.streaming and len(response.content) < MIN_LEN):
            return response

        patch_vary_headers(response, ('Accept-Encoding',))
        ae = request.META.get('HTTP_ACCEPT_ENCODING', '')
        encoding, compress_func, stream_func = compressor(ae)
        if not encoding:
            # No compression in common with client (the client probably didn't
            # indicate support for anything).
            return response

        if response.streaming:
            # Delete the `Content-Length` header for streaming content, because
            # we won't know the compressed size until we stream it.
            response.streaming_content = stream_func(response.streaming_content)
            del response['Content-Length']
        else:
            compressed_content = compress_func(response.content)
            # Return the compressed content only if compression is worth it
            if len(compressed_content) >= len(response.content) - MIN_IMPROVEMENT:
                return response

            response.content = compressed_content
            response['Content-Length'] = str(len(response.content))

        # If there is a strong ETag, make it weak to fulfill the requirements
        # of RFC 7232 section-2.1 while also allowing conditional request
        # matches on ETags.
        # Django's ConditionalGetMiddleware relies upon this etag behaviour.
        etag = response.get('ETag')
        if etag and etag.startswith('"'):
            response['ETag'] = 'W/' + etag
        response['Content-Encoding'] = encoding

        return response
