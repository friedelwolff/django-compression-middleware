# -*- encoding: utf-8 -*-
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

__all__ = ['brotli_compress']


from brotli import compress


DEFAULT_LEVEL = 4


def brotli_compress(content):
    return compress(content, quality=DEFAULT_LEVEL)
