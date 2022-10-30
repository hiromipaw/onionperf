#!/usr/bin/env python3

from setuptools import setup

with open('requirements.txt') as f:
    install_requires = f.readlines()

setup(name='OnionPerf',
      version='1.0',
      description='A utility to monitor, measure, analyze, and visualize the performance of Tor and Onion Services',
      author='Rob Jansen',
      url='https://gitlab.torproject.org/tpo/network-health/metrics/onionperf/',
      packages=['onionperf'],
      scripts=['onionperf/onionperf'],
      install_requires=[
        "lxml",
        "matplotlib",
        "networkx",
        "numpy",
        "pandas",
        "scipy",
        "seaborn >= 0.11",
        "stem >= 1.7.0",
        "tgentools @ git+https://github.com/shadow/tgen.git@main#egg=tgentools&subdirectory=tools",
        "requests"
      ]
     )
