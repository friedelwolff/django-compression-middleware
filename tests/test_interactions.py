# -*- coding: utf-8 -*-
from __future__ import unicode_literals


# This tests if the middleware works as Django expects from its own
# GZipMiddleware. This way we test the expected interactions with other parts
# of Django, such as ConditionalGetMiddleware, which relies on certain parts
# of the compression middleware, such as e-tags.

# This is mostly unchanged from the Django test suite with the middleware
# imported as GZipMiddleware for testing.


import gzip
import random
from io import BytesIO

from django.http import (
    FileResponse, HttpResponse,
    StreamingHttpResponse,
)
from compression_middleware.middleware import CompressionMiddleware as GZipMiddleware
from django.middleware.http import ConditionalGetMiddleware
from django.test import (
    RequestFactory, SimpleTestCase, ignore_warnings, override_settings,
)
from django.utils import six
from django.utils.six.moves import range


class GZipMiddlewareTest(SimpleTestCase):
    """
    Tests the GZipMiddleware.
    """
    short_string = b"This string is too short to be worth compressing."
    compressible_string = b'a' * 500
    incompressible_string = b''.join(six.int2byte(random.randint(0, 255)) for _ in range(500))
    sequence = [b'a' * 500, b'b' * 200, b'a' * 300]
    sequence_unicode = ['a' * 500, 'é' * 200, 'a' * 300]
    request_factory = RequestFactory()

    def setUp(self):
        self.req = self.request_factory.get('/')
        self.req.META['HTTP_ACCEPT_ENCODING'] = 'gzip, deflate'
        self.req.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (Windows NT 5.1; rv:9.0.1) Gecko/20100101 Firefox/9.0.1'
        self.resp = HttpResponse()
        self.resp.status_code = 200
        self.resp.content = self.compressible_string
        self.resp['Content-Type'] = 'text/html; charset=UTF-8'
        self.stream_resp = StreamingHttpResponse(self.sequence)
        self.stream_resp['Content-Type'] = 'text/html; charset=UTF-8'
        self.stream_resp_unicode = StreamingHttpResponse(self.sequence_unicode)
        self.stream_resp_unicode['Content-Type'] = 'text/html; charset=UTF-8'

    @staticmethod
    def decompress(gzipped_string):
        with gzip.GzipFile(mode='rb', fileobj=BytesIO(gzipped_string)) as f:
            return f.read()

    @staticmethod
    def get_mtime(gzipped_string):
        with gzip.GzipFile(mode='rb', fileobj=BytesIO(gzipped_string)) as f:
            f.read()  # must read the data before accessing the header
            return f.mtime

    def test_compress_response(self):
        """
        Compression is performed on responses with compressible content.
        """
        r = GZipMiddleware().process_response(self.req, self.resp)
        self.assertEqual(self.decompress(r.content), self.compressible_string)
        self.assertEqual(r.get('Content-Encoding'), 'gzip')
        self.assertEqual(r.get('Content-Length'), str(len(r.content)))

    def test_compress_streaming_response(self):
        """
        Compression is performed on responses with streaming content.
        """
        r = GZipMiddleware().process_response(self.req, self.stream_resp)
        self.assertEqual(self.decompress(b''.join(r)), b''.join(self.sequence))
        self.assertEqual(r.get('Content-Encoding'), 'gzip')
        self.assertFalse(r.has_header('Content-Length'))

    def test_compress_streaming_response_unicode(self):
        """
        Compression is performed on responses with streaming Unicode content.
        """
        r = GZipMiddleware().process_response(self.req, self.stream_resp_unicode)
        self.assertEqual(
            self.decompress(b''.join(r)),
            b''.join(x.encode('utf-8') for x in self.sequence_unicode)
        )
        self.assertEqual(r.get('Content-Encoding'), 'gzip')
        self.assertFalse(r.has_header('Content-Length'))

    def test_compress_file_response(self):
        """
        Compression is performed on FileResponse.
        """
        with open(__file__, 'rb') as file1:
            file_resp = FileResponse(file1)
            file_resp['Content-Type'] = 'text/html; charset=UTF-8'
            r = GZipMiddleware().process_response(self.req, file_resp)
            with open(__file__, 'rb') as file2:
                self.assertEqual(self.decompress(b''.join(r)), file2.read())
            self.assertEqual(r.get('Content-Encoding'), 'gzip')
            self.assertIsNot(r.file_to_stream, file1)

    def test_compress_non_200_response(self):
        """
        Compression is performed on responses with a status other than 200
        (#10762).
        """
        self.resp.status_code = 404
        r = GZipMiddleware().process_response(self.req, self.resp)
        self.assertEqual(self.decompress(r.content), self.compressible_string)
        self.assertEqual(r.get('Content-Encoding'), 'gzip')

    def test_no_compress_short_response(self):
        """
        Compression isn't performed on responses with short content.
        """
        self.resp.content = self.short_string
        r = GZipMiddleware().process_response(self.req, self.resp)
        self.assertEqual(r.content, self.short_string)
        self.assertIsNone(r.get('Content-Encoding'))

    def test_no_compress_compressed_response(self):
        """
        Compression isn't performed on responses that are already compressed.
        """
        self.resp['Content-Encoding'] = 'deflate'
        r = GZipMiddleware().process_response(self.req, self.resp)
        self.assertEqual(r.content, self.compressible_string)
        self.assertEqual(r.get('Content-Encoding'), 'deflate')

    def test_no_compress_incompressible_response(self):
        """
        Compression isn't performed on responses with incompressible content.
        """
        self.resp.content = self.incompressible_string
        r = GZipMiddleware().process_response(self.req, self.resp)
        self.assertEqual(r.content, self.incompressible_string)
        self.assertIsNone(r.get('Content-Encoding'))

    def test_compress_deterministic(self):
        """
        Compression results are the same for the same content and don't
        include a modification time (since that would make the results
        of compression non-deterministic and prevent
        ConditionalGetMiddleware from recognizing conditional matches
        on gzipped content).
        """
        r1 = GZipMiddleware().process_response(self.req, self.resp)
        r2 = GZipMiddleware().process_response(self.req, self.resp)
        self.assertEqual(r1.content, r2.content)
        self.assertEqual(self.get_mtime(r1.content), 0)
        self.assertEqual(self.get_mtime(r2.content), 0)


@override_settings(USE_ETAGS=True)
class ETagGZipMiddlewareTest(SimpleTestCase):
    """
    ETags are handled properly by GZipMiddleware.
    """
    rf = RequestFactory()
    compressible_string = b'a' * 500

    def test_strong_etag_modified(self):
        """
        GZipMiddleware makes a strong ETag weak.
        """
        request = self.rf.get('/', HTTP_ACCEPT_ENCODING='gzip, deflate')
        response = HttpResponse(self.compressible_string)
        response['ETag'] = '"eggs"'
        gzip_response = GZipMiddleware().process_response(request, response)
        self.assertEqual(gzip_response['ETag'], 'W/"eggs"')

    def test_weak_etag_not_modified(self):
        """
        GZipMiddleware doesn't modify a weak ETag.
        """
        request = self.rf.get('/', HTTP_ACCEPT_ENCODING='gzip, deflate')
        response = HttpResponse(self.compressible_string)
        response['ETag'] = 'W/"eggs"'
        gzip_response = GZipMiddleware().process_response(request, response)
        self.assertEqual(gzip_response['ETag'], 'W/"eggs"')

    def test_etag_match(self):
        """
        GZipMiddleware allows 304 Not Modified responses.
        """
        request = self.rf.get('/', HTTP_ACCEPT_ENCODING='gzip, deflate')
        response = GZipMiddleware().process_response(
            request,
            ConditionalGetMiddleware().process_response(request, HttpResponse(self.compressible_string))
        )
        gzip_etag = response['ETag']
        next_request = self.rf.get('/', HTTP_ACCEPT_ENCODING='gzip, deflate', HTTP_IF_NONE_MATCH=gzip_etag)
        next_response = ConditionalGetMiddleware().process_response(
            next_request,
            HttpResponse(self.compressible_string)
        )
        self.assertEqual(next_response.status_code, 304)

