#!/usr/bin/env python

import io
import os
import re

from setuptools import setup

package_name = "picast"
root_dir = os.path.abspath(os.path.dirname(__file__))


def readme():
    with io.open(os.path.join(os.path.dirname(__file__), 'README.rst'), mode="r", encoding="UTF-8") as readmef:
        return readmef.read()


with open(os.path.join(root_dir, package_name, '__init__.py')) as f:
    init_text = f.read()
    version = re.search(r'__version__\s*=\s*[\'\"](.+?)[\'\"]', init_text).group(1)
    license = re.search(r'__license__\s*=\s*[\'\"](.+?)[\'\"]', init_text).group(1)
    author = re.search(r'__author__\s*=\s*[\'\"](.+?)[\'\"]', init_text).group(1)
    author_email = re.search(r'__author_email__\s*=\s*[\'\"](.+?)[\'\"]', init_text).group(1)
    url = re.search(r'__url__\s*=\s*[\'\"](.+?)[\'\"]', init_text).group(1)

assert version
assert license
assert author
assert author_email
assert url

setup(name=package_name,
      version=version,
      description='A simple wireless display receiver/sink for Raspberry Pi',
      url=url,
      license=license,
      long_description=readme(),
      author=author,
      author_email=author_email,
      packages=[package_name],
      requires=['PyGObject', 'pyyaml', 'zeroconf'],
      scripts=['bin/picast'],
      classifiers=['Development Status :: 3 - Alpha',
                   'Environment :: X11 Applications',
                   'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python',
                   'Topic :: Utilities',
                   ],
      )
