#!/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='call_forward_switcher_dcm',
    version='0.2',
    description='Call forward switcher for dcm',
    author='eisin',
    author_email='eisin@noreply.github.com',
    url='https://github.com/eisin/call-forward-switcher-dcm',
    install_requires=[
        'twilio',
    ],
    license='Apache License Version 2.0',
    packages=['call_forward_switcher_dcm'],
)
