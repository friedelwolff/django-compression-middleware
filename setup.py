#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
from platform import python_implementation
from setuptools import setup

install_requires = ['django', 'zstandard']
if python_implementation() == 'PyPy':
    install_requires.append('brotlipy')
else:
    install_requires.append('Brotli')


setup(
    name='django-compression-middleware',
    version='0.5.0',
    description="""Django middleware to compress responses using several algorithms.""",
    long_description=io.open("README.rst", 'r', encoding="utf-8").read(),
    url='https://github.com/friedelwolff/django-compression-middleware',
    author='Friedel Wolff',
    author_email='friedel@translate.org.za',
    packages=['compression_middleware'],
    install_requires=install_requires,
    python_requires=">=3.8",
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Framework :: Django :: 4.1',
        'Framework :: Django :: 4.2',
        'Framework :: Django :: 5.0',
        'Framework :: Django :: 5.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
        'Topic :: Internet :: WWW/HTTP :: ASGI :: Middleware',
    ]
)
