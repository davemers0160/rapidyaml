#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

import os
import shutil
import sys

from pathlib import Path
from distutils import log
from setuptools import setup, find_packages
from cmake_build_extension import BuildExtension, CMakeExtension

TOP_DIR = (Path(__file__).parent).resolve()

# where the Python library is actually found
PYTHON_DIR = "api/python"

setup_kw = {}


# read the module description from the README.md file
with open(TOP_DIR / "README.md", "r") as fh:
    setup_kw['long_description'] = fh.read()
    setup_kw['long_description_content_type'] = "text/markdown"


# read the package version when not in a git repository
VERSION_FILE = os.path.join(PYTHON_DIR, 'ryml', 'version.py')
if not (TOP_DIR / '.git').exists() and os.path.exists(VERSION_FILE):
    exec(open(VERSION_FILE).read())
    setup_kw['version'] = version
else:
    setup_kw['use_scm_version'] = {
        "version_scheme": "post-release",
        "local_scheme": "no-local-version",
        "write_to": VERSION_FILE,
    }


# define a CMake package
cmake_args = dict(
    name='ryml.ryml',
    install_prefix='',
    source_dir='',
    cmake_component='python',
    cmake_configure_options=[
        "-DRYML_BUILD_API:BOOL=ON",
        # Force cmake to use the Python interpreter we are currently
        # using to run setup.py
        "-DPython3_EXECUTABLE:FILEPATH=" + sys.executable,
    ],
)


try:
    ext = CMakeExtension(**cmake_args)
    log.info("Using standard CMakeExtension")
except TypeError:
    log.info("Using custom CMakeExtension")
    # If the CMakeExtension doesn't support `cmake_component` then we
    # have to do some manual cleanup.
    del cmake_args['cmake_component']
    ext = CMakeExtension(**cmake_args)
    def _cleanup(path, mandatory):
        if mandatory:
            assert path.exists(), path
        elif not path.exists():
            return
        log.info("Removing everything under: %s", path)
        shutil.rmtree(path)
    _BuildExtension = BuildExtension
    class BuildExtension(_BuildExtension):
        def build_extension(self, ext):
            _BuildExtension.build_extension(self, ext)
            ext_dir = Path(self.get_ext_fullpath(ext.name)).parent.absolute()
            cmake_install_prefix = ext_dir / ext.install_prefix
            assert cmake_install_prefix.exists(), cmake_install_prefix
            try:
                _cleanup(cmake_install_prefix / "lib", mandatory=True)
                _cleanup(cmake_install_prefix / "include", mandatory=True)
                # Windows only
                _cleanup(cmake_install_prefix / "cmake", mandatory=False)
            except:
                log.info('Found following installed files:')
                for f in cmake_install_prefix.rglob("*"):
                    log.info(' - %s', f)
                raise


setup(
    # Package human readable information
    name='rapidyaml',
    description='Rapid YAML - a library to parse and emit YAML, and do it fast',
    url='https://github.com/biojppm/rapidyaml',
    license='MIT',
    license_files=['LICENSE.txt'],
    author="Joao Paulo Magalhaes",
    author_email="dev@jpmag.me",
    # Package contents control
    cmdclass={
        "build_ext": BuildExtension,
    },
    package_dir={"": PYTHON_DIR},
    packages=find_packages( # not working...
        'ryml',
        exclude=[
            "test",
            "build",
            "install",
            "ext/c4core/build",
            "ext/c4core/install"
        ]
    ),
    ext_modules=[ext],
    include_package_data=True,
    # Requirements
    python_requires=">=3.6",
    setup_requires=[
        'setuptools_scm',
        'setuptools-git',
        'setuptools',
    ],
    # Extra arguments
    **setup_kw,
)
