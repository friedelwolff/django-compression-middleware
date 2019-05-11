# -*- encoding: utf-8 -*-

# partially based on tests in django and django-brotli

from io import BytesIO
import gzip
import random
from unittest import TestCase

import brotli
import zstandard as zstd

from django.http import (
    FileResponse, HttpResponse,
    StreamingHttpResponse,
)

from django.middleware.gzip import GZipMiddleware
from django.test import RequestFactory, SimpleTestCase
from django.utils import six

from compression_middleware.middleware import CompressionMiddleware, compressor
from .utils import UTF8_LOREM_IPSUM_IN_CZECH


class FakeRequestAcceptsZstd(object):
    META = {
        'HTTP_ACCEPT_ENCODING': 'gzip, deflate, sdch, br, zstd'
    }


class FakeRequestAcceptsBrotli(object):
    META = {
        'HTTP_ACCEPT_ENCODING': 'gzip, deflate, sdch, br'
    }


class FakeLegacyRequest(object):
    META = {
    }


def gzip_decompress(gzipped_string):
    with gzip.GzipFile(mode='rb', fileobj=BytesIO(gzipped_string)) as f:
        return f.read()


class FakeResponse(object):
    streaming = False

    def __init__(self, content, headers=None, streaming=None):
        self.content = content.encode(encoding='utf-8')
        self.headers = headers or {}

        if streaming:
            self.streaming = streaming

    def has_header(self, header):
        return header in self.headers

    def get(self, key):
        return self.headers.get(key, None)

    def __getitem__(self, header):
        return self.headers[header]

    def __setitem__(self, header, value):
        self.headers[header] = value


class MiddlewareTestCase(TestCase):
    def test_middleware_compress_response(self):
        fake_request = FakeRequestAcceptsBrotli()
        response_content = UTF8_LOREM_IPSUM_IN_CZECH
        fake_response = FakeResponse(content=response_content)

        compression_middleware = CompressionMiddleware()
        response = compression_middleware.process_response(fake_request, fake_response)

        decompressed_response = brotli.decompress(response.content)  # type: bytes
        self.assertEqual(response_content, decompressed_response.decode(encoding='utf-8'))
        self.assertEqual(response.get('Vary'), 'Accept-Encoding')

    def test_middleware_compress_response_zstsd(self):
        fake_request = FakeRequestAcceptsZstd()
        response_content = UTF8_LOREM_IPSUM_IN_CZECH
        fake_response = FakeResponse(content=response_content)

        compression_middleware = CompressionMiddleware()
        response = compression_middleware.process_response(fake_request, fake_response)

        cctx = zstd.ZstdDecompressor()
        decompressed_response = cctx.decompress(response.content)  # type: bytes
        self.assertEqual(response_content, decompressed_response.decode(encoding='utf-8'))
        self.assertEqual(response.get('Vary'), 'Accept-Encoding')

    def test_etag_is_updated_if_present(self):
        fake_request = FakeRequestAcceptsBrotli()
        response_content = UTF8_LOREM_IPSUM_IN_CZECH * 5
        fake_etag_content = "\"foo\""
        fake_response = FakeResponse(content=response_content, headers={"ETag": fake_etag_content})

        self.assertEqual(fake_response['ETag'], fake_etag_content)

        compression_middleware = CompressionMiddleware()
        response = compression_middleware.process_response(fake_request, fake_response)

        decompressed_response = brotli.decompress(response.content)  # type: bytes
        self.assertEqual(response_content, decompressed_response.decode(encoding='utf-8'))

        # note: this is where we differ from django-brotli
        # django-brotli's expectation:
        ### self.assertEqual(response['ETag'], '"foo;br\\"')
        # Django's expectation:
        self.assertEqual(response['ETag'], 'W/"foo"')

    def test_middleware_wont_compress_response_if_response_is_small(self):
        fake_request = FakeRequestAcceptsBrotli()
        response_content = "Hello World"

        self.assertLess(len(response_content), 200)  # a < b

        fake_response = FakeResponse(content=response_content)

        compression_middleware = CompressionMiddleware()
        response = compression_middleware.process_response(fake_request, fake_response)

        self.assertEqual(response_content, response.content.decode(encoding='utf-8'))
        self.assertFalse(response.has_header('Vary'))

    def test_middleware_wont_compress_if_client_not_accept(self):
        fake_request = FakeLegacyRequest()
        response_content = UTF8_LOREM_IPSUM_IN_CZECH
        fake_response = FakeResponse(content=response_content)

        compression_middleware = CompressionMiddleware()
        response = compression_middleware.process_response(fake_request, fake_response)

        django_gzip_middleware = GZipMiddleware()
        gzip_response = django_gzip_middleware.process_response(fake_request, fake_response)

        self.assertEqual(response_content, response.content.decode(encoding='utf-8'))
        self.assertEqual(response.get('Vary'), 'Accept-Encoding')

    def test_middleware_wont_compress_if_response_is_already_compressed(self):
        fake_request = FakeRequestAcceptsBrotli()
        response_content = UTF8_LOREM_IPSUM_IN_CZECH
        fake_response = FakeResponse(content=response_content)

        compression_middleware = CompressionMiddleware()
        django_gzip_middleware = GZipMiddleware()

        gzip_response = django_gzip_middleware.process_response(fake_request, fake_response)
        response = compression_middleware.process_response(fake_request, gzip_response)

        self.assertEqual(response_content, gzip_decompress(response.content).decode(encoding='utf-8'))
        self.assertEqual(response.get('Vary'), 'Accept-Encoding')


    def test_content_encoding_parsing(self):
        self.assertEqual(compressor('')[0], None)
        self.assertEqual(compressor('gzip')[0], 'gzip')
        self.assertEqual(compressor('br')[0], 'br')
        self.assertEqual(compressor('gzip, br')[0], 'br')
        self.assertEqual(compressor('br;q=1.0, gzip;q=0.8')[0], 'br')
        self.assertEqual(compressor('br;q=0, gzip;q=0.8')[0], 'gzip')
#         self.assertEqual(compressor('br;q=0, gzip;q=0.8, *;q=0.1')[0], 'gzip')
        self.assertEqual(compressor('*')[0], 'zstd')


class StreamingTest(SimpleTestCase):
    """
    Tests streaming.
    """
    short_string = b"This string is too short to be worth compressing."
    compressible_string = b'a' * 500
    incompressible_string = b''.join(six.int2byte(random.randint(0, 255)) for _ in range(500))
    sequence = [b'a' * 500, b'b' * 200, b'a' * 300]
    sequence_unicode = [u'a' * 500, u'é' * 200, u'a' * 300]
    request_factory = RequestFactory()

    def setUp(self):
        self.req = self.request_factory.get('/')
        self.req.META['HTTP_ACCEPT_ENCODING'] = 'gzip, deflate, br'
        self.req.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (Windows NT 5.1; rv:9.0.1) Gecko/20100101 Firefox/9.0.1'
        self.resp = HttpResponse()
        self.resp.status_code = 200
        self.resp.content = self.compressible_string
        self.resp['Content-Type'] = 'text/html; charset=UTF-8'
        self.stream_resp = StreamingHttpResponse(self.sequence)
        self.stream_resp['Content-Type'] = 'text/html; charset=UTF-8'
        self.stream_resp_unicode = StreamingHttpResponse(self.sequence_unicode)
        self.stream_resp_unicode['Content-Type'] = 'text/html; charset=UTF-8'

    def test_compress_streaming_response(self):
        """
        Compression is performed on responses with streaming content.
        """
        r = CompressionMiddleware().process_response(self.req, self.stream_resp)
        self.assertEqual(brotli.decompress(b''.join(r)), b''.join(self.sequence))
        self.assertEqual(r.get('Content-Encoding'), 'br')
        self.assertFalse(r.has_header('Content-Length'))
        self.assertEqual(r.get('Vary'), 'Accept-Encoding')

    def test_compress_streaming_response_unicode(self):
        """
        Compression is performed on responses with streaming Unicode content.
        """
        r = CompressionMiddleware().process_response(self.req, self.stream_resp_unicode)
        self.assertEqual(
            brotli.decompress(b''.join(r)),
            b''.join(x.encode('utf-8') for x in self.sequence_unicode)
        )
        self.assertEqual(r.get('Content-Encoding'), 'br')
        self.assertFalse(r.has_header('Content-Length'))
        self.assertEqual(r.get('Vary'), 'Accept-Encoding')
