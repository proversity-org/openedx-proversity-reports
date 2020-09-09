# -*- coding: utf-8 -*-
"""
Setup file for openedx-proversity-reports Django plugin.
"""
from __future__ import absolute_import, print_function

import os
import re

from setuptools import setup


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


def load_requirements(*requirements_paths):
    """
    Load all requirements from the specified requirements files.
    Returns a list of requirement strings.
    """
    requirements = set()
    for path in requirements_paths:
        requirements.update(
            line.split('#')[0].strip() for line in open(path).readlines()
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
    install_requires=load_requirements('requirements/base.in'),
)
