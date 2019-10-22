# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

__all__ = ['compress_page', 'compress_exempt']

from functools import wraps

from .middleware import CompressionMiddleware
from django.utils.decorators import decorator_from_middleware


compress_page = decorator_from_middleware(CompressionMiddleware)
compress_page.__doc__ = "Decorator to compress the view response if the client supports it."

def compress_exempt(view_func):
    """Prevent a view from being compressed by the middleware."""
    @wraps(view_func)
    def _wrapped_view_func(request, *args, **kwargs):
        # request.compress_exempt = True
        response = view_func(request, *args, **kwargs)
        return response

    return _wrapped_view_func
