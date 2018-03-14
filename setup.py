#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages
from pip.req import parse_requirements
from pip.download import PipSession


with open('README.rst') as readme_file:
    readme = readme_file.read()

# get the requirements from requirements.txt
install_reqs = parse_requirements('requirements.txt', session=PipSession())
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='neo-python',
    python_requires='>=3.6',
    version='0.5.8',
    description="Python Node and SDK for the NEO blockchain",
    long_description=readme,
    author="Thomas Saunders",
    author_email='tom@cityofzion.io',
    maintainer="Chris Hager",
    maintainer_email='chris@cityofzion.io',
    url='https://github.com/CityOfZion/neo-python',
    packages=find_packages(include=['neo']),
    scripts=['prompt.py','api_server.py','bootstrap.py','reencrypt_wallet.py'],
    entry_points = {
        'console_scripts': [
            'np_prompt=prompt:main',
            'np_api_server=api_server:main',
            'np_bootstrap=bootstrap:main',
            'np_reencrypt_wallet=reencrypt_wallet:main',
        ],
    },
    data_files=[
        ('neo-python-data',
         ['protocol.testnet.json',
          'protocol.mainnet.json',
          'protocol.coz.json',
          'protocol.privnet.json',
          'neo-privnet.sample.wallet',
          ]),
    ],
    include_package_data=True,
    install_requires=reqs,
    license="MIT license",
    zip_safe=False,
    keywords='neo, python, node',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ]
)
