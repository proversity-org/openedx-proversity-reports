"""
Production settings for openedx_proversity_reports project.
"""


def plugin_settings(settings):
    """
    Set of plugin settings used by the Open Edx platform.
    More info: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/plugins/README.rst
    """
    settings.OPR_COMPLETION_MODELS = getattr(settings, 'ENV_TOKENS', {}).get(
        'OPR_COMPLETION_MODELS',
        settings.OPR_COMPLETION_MODELS
    )

    settings.OPR_COURSE_BLOCKS = getattr(settings, 'ENV_TOKENS', {}).get(
        'OPR_COURSE_BLOCKS',
        settings.OPR_COURSE_BLOCKS
    )

    settings.OPR_COURSE_COHORT = getattr(settings, 'ENV_TOKENS', {}).get(
        'OPR_COURSE_COHORT',
        settings.OPR_COURSE_COHORT
    )

    settings.OPR_COURSE_TEAMS = getattr(settings, 'ENV_TOKENS', {}).get(
        'OPR_COURSE_TEAMS',
        settings.OPR_COURSE_TEAMS
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

    settings.OPR_STUDENT_LIBRARY = getattr(settings, 'ENV_TOKENS', {}).get(
        'OPR_STUDENT_LIBRARY',
        settings.OPR_STUDENT_LIBRARY
    )

    settings.OPR_SUPPORTED_FIELDS = getattr(settings, 'ENV_TOKENS', {}).get(
        'OPR_SUPPORTED_FIELDS',
        settings.OPR_SUPPORTED_FIELDS
    )

    settings.OPR_GOOGLE_ANALYTICS_VIEW_ID = getattr(settings, 'ENV_TOKENS', {}).get(
        'OPR_GOOGLE_ANALYTICS_VIEW_ID',
        settings.OPR_GOOGLE_ANALYTICS_VIEW_ID
    )

    settings.OPR_GOOGLE_ANALYTICS_CREDENTIALS = getattr(settings, 'AUTH_TOKENS', {}).get(
        'OPR_GOOGLE_ANALYTICS_CREDENTIALS',
        settings.OPR_GOOGLE_ANALYTICS_CREDENTIALS
    )
