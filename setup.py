#!/usr/bin/env python3

from setuptools import find_packages, setup

setup(name='OnionPerf',
      version='1.0',
      description='A utility to monitor, measure, analyze, and visualize the performance of Tor and Onion Services',
      author='Rob Jansen',
      url='https://gitlab.torproject.org/tpo/network-health/metrics/onionperf',
      packages=find_packages(where="onionperf"),
      package_dir={"": "onionperf"},
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
      ],
      scripts=['onionperf/onionperf']
     )
