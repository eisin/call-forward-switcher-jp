#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='call_forward_switcher_jp',
    version='0.6',
    description='Call forward switcher for JP career',
    author='eisin',
    author_email='eisin@noreply.github.com',
    url='https://github.com/eisin/call-forward-switcher-jp',
    install_requires=[
        'twilio',
        'boto3',
        'pytz',
    ],
    license='Apache License Version 2.0',
    packages=['call_forward_switcher_jp.dcm', 'call_forward_switcher_jp.auk'],
)
