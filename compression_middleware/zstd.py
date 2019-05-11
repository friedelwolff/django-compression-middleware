# -*- encoding: utf-8 -*-
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

__all__ = ['zstd_compress', 'zstd_compress_stream']


from django.utils.text import StreamingBuffer

import zstandard as zstd


DEFAULT_LEVEL = 7


def zstd_compress(content):
    cctx = zstd.ZstdCompressor(level=DEFAULT_LEVEL)
    return cctx.compress(content)


def zstd_compress_stream(sequence):
    buf = StreamingBuffer()
    cctx = zstd.ZstdCompressor(level=DEFAULT_LEVEL)
    with cctx.stream_writer(buf, write_return_read=False) as compressor:
        yield buf.read()
        for item in sequence:
            if compressor.write(item):
                yield buf.read()
        compressor.flush()
        yield buf.read()
