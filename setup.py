"""
Setup script for pylove package.

This script sets up the metadata and requirements for the pylove package,
allowing it to be installed via setuptools.
"""
from setuptools import setup, find_packages
from version import VERSION  # Importing version from version.py

# get the description programmatically
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# get the requirements programmatically
with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [
        line.strip() for line in f
        if line.strip()
        and not line.startswith('#')
    ]

# create the metadata for the package
setup(
    name='pylove',
    version=VERSION,
    packages=find_packages(),
    install_requires=requirements,
    author='Catboy',
    description='A description of your package',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/catboy1357/pylove',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ]
)
