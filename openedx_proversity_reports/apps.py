"""
File configuration for openedx-proversity-reports.
"""
from django.apps import AppConfig


class OpenEdxProversityReportsConfig(AppConfig):
    """
    Plugin app configuration for openedx-proversity-reports
    """
    name = 'openedx_proversity_reports'
    verbose_name = "Open edX Proversity additional reports plugin."

    plugin_app = {
        'settings_config': {
            'lms.djangoapp': {},
            'cms.djangoapp': {},
        },
    }
