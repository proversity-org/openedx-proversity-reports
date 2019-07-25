# -*- coding: utf-8 -*-
"""
Setup file for openedx-proversity-reports Django plugin.
"""
from __future__ import absolute_import, print_function

import os
import re
import subprocess

from setuptools import setup

OPEN_EDX_GINKGO_VERSION = 0.9
OPEN_EDX_HAWTHORN_VERSION = 0.10
OPEN_EDX_IRONWOOD_VERSION = 0.11
REQUIREMENTS_FOLDER_PATH = 'requirements'
OPEN_EDX_PLATFORM_VERSION_ERROR = 'Unable to get the edX platform version'


def get_version():
    """
    Retrieves the version string from __init__.py.
    """
    file_path = os.path.join('openedx_proversity_reports', '__init__.py')
    initfile_lines = open(file_path, 'rt').readlines()
    version_regex = r"^__version__ = ['\"]([^'\"]*)['\"]"
    for line in initfile_lines:
        match_string = re.search(version_regex, line, re.M)
        if match_string:
            return match_string.group(1)
    raise RuntimeError('Unable to find version string in %s.' % (file_path,))


def load_requirements(requirements_folder):
    """
    Load all requirements from the specified requirements files.
    Returns a list of requirement strings.
    """
    edx_platform_version = get_edx_platform_version()

    if edx_platform_version == OPEN_EDX_GINKGO_VERSION:
        requirements_path = '{}/{}'.format(requirements_folder, 'ginkgo.in')
    elif edx_platform_version == OPEN_EDX_HAWTHORN_VERSION:
        requirements_path = '{}/{}'.format(requirements_folder, 'hawthorn.in')
    elif edx_platform_version == OPEN_EDX_IRONWOOD_VERSION:
        requirements_path = '{}/{}'.format(requirements_folder, 'ironwood.in')
    else:
        raise Exception('The currently Open-edX version {} is not supported'.format(edx_platform_version))

    requirements = set()
    requirements.update(
        line.split('#')[0].strip() for line in open(requirements_path).readlines()
        if is_requirement(line)
    )

    return list(requirements)


def is_requirement(line):
    """
    Return True if the requirement line is a package requirement;
    that is, it is not blank, a comment, or editable.
    """
    # Remove whitespace at the start/end of the line
    line = line.strip()

    # Skip blank lines, comments, and editable installs
    return not (
        line == '' or
        line.startswith('-r') or
        line.startswith('#') or
        line.startswith('-e') or
        line.startswith('git+') or
        line.startswith('-c')
    )


def get_edx_platform_version():
    """
    Returns the pip package version for Open-edX.
    """
    FILE_NAME = 'open_edx_version.txt'
    VERSION_KEY_NAME = 'Version'
    command = 'pip show Open-edX > {}'.format(FILE_NAME)

    subprocess.call(command, shell=True)

    version = 0.0

    with open(FILE_NAME, 'r') as file:
        lines = file.readlines()

        for line in lines:
            if line.startswith(VERSION_KEY_NAME):
                name, version = line.split(': ')

                try:
                    version = float(version)
                except ValueError as error:
                    raise ValueError('{} {} '.format(OPEN_EDX_PLATFORM_VERSION_ERROR, error.message))

    os.remove(FILE_NAME)
    return version


setup(
    name='openedx-proversity-reports',
    version=get_version(),
    description='Open edX Proversity additional reports plugin.',
    author='Proversity',
    author_email='info@proversity.org',
    packages=['openedx_proversity_reports'],
    zip_safe=False,
    entry_points={
        "lms.djangoapp": [
            "openedx_proversity_reports = openedx_proversity_reports.apps:OpenEdxProversityReportsConfig"
        ],
    },
    include_package_data=True,
    install_requires=load_requirements(REQUIREMENTS_FOLDER_PATH),
)
