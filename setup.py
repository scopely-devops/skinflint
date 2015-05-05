#!/usr/bin/env python

from setuptools import setup, find_packages

import os

requires = ['boto>=2.38.0',
            'python-dateutil>=2.1,<3.0.0',
            'PyYAML>=3.11',
            'XlsxWriter==0.6.7',
            'pytz==2014.10']

setup(
    name='skinflint',
    version=open(os.path.join('skinflint', '_version')).read(),
    description='Tools for processing AWS detailed billing reports',
    long_description=open('README.md').read(),
    author='Mitch Garnaat',
    author_email='mitch@scopely.com',
    url='https://github.com/scopely-devops/skinflint',
    packages=find_packages(exclude=['tests*']),
    package_data={'skinflint': ['_version']},
    package_dir={'skinflint': 'skinflint'},
    install_requires=requires,
    license=open("LICENSE").read(),
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4'
    ),
)
