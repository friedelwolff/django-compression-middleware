# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import brotli

from django.http import HttpRequest, HttpResponse, StreamingHttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase

from compression_middleware.decorators import compress_page


class CompressPageDecoratorTest(SimpleTestCase):

    compressible_string = b'a' * 500
    sequence = [b'a' * 500, b'b' * 200, b'a' * 300]
    sequence_unicode = ['a' * 500, 'é' * 200, 'a' * 300]
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

    def test_small_page(self):

        @compress_page
        def a_small_view(request):
            return HttpResponse()

        r = a_small_view(self.req)
        self.assertFalse(r.has_header('Content-Encoding'))
        self.assertEqual(r.content, b'')

    def test_normal_page(self):
        @compress_page
        def a_view(request):
            return self.resp

        r = a_view(self.req)
        self.assertEqual(r.get('Content-Encoding'), 'br')
        self.assertEqual(r.get('Content-Length'), str(len(r.content)))
        self.assertTrue(brotli.decompress(r.content), self.compressible_string)

    def test_streaming_page(self):
        @compress_page
        def a_streaming_view(request):
            return self.stream_resp_unicode

        r = a_streaming_view(self.req)
        self.assertEqual(r.get('Content-Encoding'), 'br')
        self.assertFalse(r.has_header('Content-Length'))
        self.assertEqual(
            brotli.decompress(b''.join(r)),
            b''.join(x.encode('utf-8') for x in self.sequence_unicode)
        )
