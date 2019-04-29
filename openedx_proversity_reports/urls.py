"""
Openedx Proversity Reports URL configuration.
"""
from django.conf.urls import include, url


urlpatterns = [  # pylint: disable=invalid-name
    url(
        r'^api/',
        include('openedx_proversity_reports.api.urls', namespace='api'),
    ),
]
