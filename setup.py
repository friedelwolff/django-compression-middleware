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
    version='0.3.0',
    description="""Django middleware to compress responses using several algorithms.""",
    long_description=io.open("README.rst", 'r', encoding="utf-8").read(),
    url='https://github.com/friedelwolff/django-compression-middleware',
    author='Friedel Wolff',
    author_email='friedel@translate.org.za',
    packages=['compression_middleware'],
    install_requires=install_requires,
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
    ]
)
