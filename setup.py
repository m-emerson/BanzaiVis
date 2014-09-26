#!/usr/bin/env python

import os
import sys
import glob

# Try and import pip. We'll stop if it is not present
try:
    import pip
except ImportError:
    print "Installation of BanzaiVis requires pip. Please install it!"
    print "http://pip.readthedocs.org/en/latest/installing.html"
    sys.exit()

from setuptools import setup

__title__         = 'BanzaiVis'
__version__       = '0.0.1'
__description__   = "BanzaiVis manages the results of InterproScan runs"
__author__        = 'Marisa Emerson'
__author_email__  = 'exterminate@dalek.com.au'
__url__           = 'https://github.com/m-emerson/BanzaiVis'


# Helper functions
if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

if sys.argv[-1] == 'clean':
    os.system('rm -rf BanzaiVis.egg-info build dist')
    sys.exit()

if sys.argv[-1] == 'docs':
    os.system('cd docs && make html')
    sys.exit()


packages = [__title__.lower(),]

requires = []
with open('requirements.txt') as fin:
    lines = fin.readlines()
    for line in lines:
        requires.append(line.strip())

# Build lists to package the docs
html, sources, static = [], [], []
html_f    = glob.glob('docs/_build/html/*')
accessory = glob.glob('docs/_build/html/*/*')
for f in html_f:
    if os.path.isfile(f):
        html.append(f)
for f in accessory:
    if f.find("_static") != -1:
        if os.path.isfile(f):
            static.append(f)
    elif f.find("_sources"):
        if os.path.isfile(f):
            sources.append(f)

setup(
    name                 = __title__,
    version              = __version__,
    description          = __description__,
    long_description     = open('README.rst').read(),
    author               = __author__,
    author_email         = __author_email__,
    url                  = __url__,
    packages             = packages,
    test_suite           ="tests",
    package_dir          = {__title__.lower(): __title__.lower()},
    scripts              = [],
    data_files           = [('', ['requirements.txt', 'README.rst']),
                            ('docs', html),
                            ('docs/_static', static),
                            ('docs/_sources', sources)],
    include_package_data = True,
    install_requires     = requires,
    license              = '',
    zip_safe             = False,
    classifiers          = (
        'Private :: Do not upload',),
)
