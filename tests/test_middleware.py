# -*- encoding: utf-8 -*-

from io import BytesIO
import gzip
from unittest import TestCase

import brotli
from django.middleware.gzip import GZipMiddleware

from compression_middleware.middleware import CompressionMiddleware, compressor
from .utils import UTF8_LOREM_IPSUM_IN_CZECH


class FakeRequestAcceptsBrotli(object):
    META = {
        'HTTP_ACCEPT_ENCODING': 'gzip, deflate, sdch, br'
#         'HTTP_ACCEPT_ENCODING': 'br, gzip, deflate, sdch'
    }


class FakeLegacyRequest(object):
    META = {
#         'HTTP_ACCEPT_ENCODING': 'gzip, deflate, sdch'
#         'HTTP_ACCEPT_ENCODING': ''
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

#         self.assertEqual(response['ETag'], '"foo;br\\"')
        self.assertEqual(response['ETag'], 'W/"foo"')

    def test_middleware_wont_compress_response_if_response_is_small(self):
        fake_request = FakeRequestAcceptsBrotli()
        response_content = "Hello World"

        self.assertLess(len(response_content), 200)  # a < b

        fake_response = FakeResponse(content=response_content)

        compression_middleware = CompressionMiddleware()
        response = compression_middleware.process_response(fake_request, fake_response)

        self.assertEqual(response_content, response.content.decode(encoding='utf-8'))

    def test_middleware_wont_compress_if_client_not_accept(self):
        fake_request = FakeLegacyRequest()
        response_content = UTF8_LOREM_IPSUM_IN_CZECH
        fake_response = FakeResponse(content=response_content)

        compression_middleware = CompressionMiddleware()
        response = compression_middleware.process_response(fake_request, fake_response)

        django_gzip_middleware = GZipMiddleware()
        gzip_response = django_gzip_middleware.process_response(fake_request, fake_response)

        self.assertEqual(response_content, response.content.decode(encoding='utf-8'))

    def test_middleware_wont_compress_if_response_is_already_compressed(self):
        fake_request = FakeRequestAcceptsBrotli()
        response_content = UTF8_LOREM_IPSUM_IN_CZECH
        fake_response = FakeResponse(content=response_content)

        compression_middleware = CompressionMiddleware()
        django_gzip_middleware = GZipMiddleware()

        gzip_response = django_gzip_middleware.process_response(fake_request, fake_response)
        response = compression_middleware.process_response(fake_request, gzip_response)

        self.assertEqual(response_content, gzip_decompress(response.content).decode(encoding='utf-8'))


    def test_content_encoding_parsing(self):
        self.assertEqual(compressor('')[0], None)
        self.assertEqual(compressor('gzip')[0], 'gzip')
        self.assertEqual(compressor('br')[0], 'br')
        self.assertEqual(compressor('gzip, br')[0], 'br')
        self.assertEqual(compressor('br;q=1.0, gzip;q=0.8')[0], 'br')
        self.assertEqual(compressor('br;q=0, gzip;q=0.8')[0], 'gzip')
#         self.assertEqual(compressor('br;q=0, gzip;q=0.8, *;q=0.1')[0], 'gzip')
        self.assertEqual(compressor('*')[0], 'br')
