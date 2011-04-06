##############################################################################
#
# Copyright (c) 2008 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Package setup.

$Id$
"""
import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name='keas.build',
    version='0.2.1dev',
    author = "Stephan Richter and the Zope Community",
    author_email = "zope-dev@zope.org",
    description='A Build System',
    long_description=(
        read('README.txt')
        + '\n\n' +
        read('src','keas','build','index.txt')
        + '\n\n' +
        read('CHANGES.txt')
        ),
    license = "ZPL 2.1",
    keywords = "zope3 release build",
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Framework :: Buildout'],
    url = 'http://pypi.python.org/pypi/keas.build',
    packages = find_packages('src'),
    include_package_data = True,
    package_dir = {'': 'src'},
    namespace_packages = ['keas'],
    extras_require = dict(
      test = [
          'zope.testing',
          ],
    ),
    install_requires=[
        'BeautifulSoup',
        'setuptools',
        ],
    zip_safe = False,
    entry_points = """
    [console_scripts]
    build = keas.build.build:main
    build-package = keas.build.package:main
    install = keas.build.install:main
    """,
    )
