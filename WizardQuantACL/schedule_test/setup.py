# -*- coding: utf-8 -*-
# ! /user/bin/env python
from setuptools import find_packages

# or
# from setuptools import find_namespace_packages
version = "0.0.9a5"

metadata = dict(
    name='ACLScheduleTest',
    version=version,
    description='ScheduleTest Module from Advanced Computing Lab',
    long_description='A ScheduleTest platform for DAG(Directed Acyclic Graph) schedule algorithm backtest from '
                     'Advanced Computing Lab',
    author='Wizardquant[Advanced Computing Lab]',
    author_email="lijunyi@wizardquant.com",
    python_requires='>=3.6, !=3.0.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*',
    packages=find_packages(),
    zip_safe=False,
    install_requires=[
        'pandas>=1.1.0',
        'matplotlib>=3.3.0',
        'numpy>=1.18.4',
    ],
    dependency_links=[
	'https://pypi.tuna.tsinghua.edu.cn/simple/',
        'http://mirrors.aliyun.com/pypi/simple',
        'https://pypi/python.org/simple',
    ],
    universal=True
)

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# Normal Python Package, no permision needed
setup(**metadata)
