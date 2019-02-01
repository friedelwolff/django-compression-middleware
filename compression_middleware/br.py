# -*- encoding: utf-8 -*-
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

__all__ = ['brotli_compress', 'brotli_compress_stream']


from brotli import compress, Compressor


DEFAULT_LEVEL = 4


def brotli_compress(content):
    return compress(content, quality=DEFAULT_LEVEL)


def brotli_compress_stream(sequence):
    yield b''

    compressor = Compressor(quality=DEFAULT_LEVEL)
    try:
        # Brotli bindings
        process = compressor.process
    except AttributeError:
        # brotlipy
        process = compressor.compress

    for item in sequence:
        out = process(item)
        if out:
            yield out
    out = compressor.finish()
    if out:
        yield out
