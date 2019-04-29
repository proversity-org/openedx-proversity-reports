"""
Production settings for openedx_proversity_reports project.
"""


def plugin_settings(settings):
    """
    Set of plugin settings used by the Open Edx platform.
    More info: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/plugins/README.rst
    """
    settings.OPR_COURSE_BLOCKS = getattr(settings, 'ENV_TOKENS', {}).get(
        'OPR_COURSE_BLOCKS',
        settings.OPR_COURSE_BLOCKS
    )

    settings.OPR_EDX_REST_FRAMEWORK_EXTENSIONS = getattr(settings, 'ENV_TOKENS', {}).get(
        'OPR_EDX_REST_FRAMEWORK_EXTENSIONS',
        settings.OPR_EDX_REST_FRAMEWORK_EXTENSIONS
    )

    settings.OPR_MODULESTORE = getattr(settings, 'ENV_TOKENS', {}).get(
        'OPR_MODULESTORE',
        settings.OPR_MODULESTORE
    )

    settings.OPR_OPENEDX_PERMISSIONS = getattr(settings, 'ENV_TOKENS', {}).get(
        'OPR_OPENEDX_PERMISSIONS',
        settings.OPR_OPENEDX_PERMISSIONS
    )

    settings.OPR_SUPPORTED_FIELDS = getattr(settings, 'ENV_TOKENS', {}).get(
        'OPR_SUPPORTED_FIELDS',
        settings.OPR_SUPPORTED_FIELDS
    )
