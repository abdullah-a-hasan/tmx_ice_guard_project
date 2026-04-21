from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='tmx_ice_guard',
    version='1.0b0',
    description='A library for converting between TMX flavours.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='AAH',
    packages=find_packages(exclude=['*.tests', '*.backup']),
    install_requires=[],
)
