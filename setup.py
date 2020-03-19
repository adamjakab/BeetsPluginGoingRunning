#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/17/20, 10:25 PM
#  License: See LICENSE.txt
#

import pathlib
from setuptools import setup
from distutils.util import convert_path

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

main_ns = {}
ver_path = convert_path('beetsplug/goingrunning/version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

# Setup
setup(
    name='beets-goingrunning',
    version=main_ns['__version__'],
    description='A beets plugin for creating and exporting songs matching '
                'your running session.',
    author='Adam Jakab',
    author_email='adam@jakab.pro',
    url='https://github.com/adamjakab/BeetsPluginGoingRunning',
    license='MIT',
    long_description=README,
    long_description_content_type='text/markdown',
    platforms='ALL',

    include_package_data=True,
    test_suite='test',
    packages=['beetsplug.goingrunning'],

    python_requires='>=3.6',

    install_requires=[
        'beets>=1.4.9',
    ],

    tests_require=[
        'pytest', 'nose', 'coverage',
        'mock', 'six', 'yaml',
        'requests'
    ],

    extras_require={
        'tests': ['requests'],
    },

    classifiers=[
        'Topic :: Multimedia :: Sound/Audio',
        'License :: OSI Approved :: MIT License',
        'Environment :: Console',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
)
