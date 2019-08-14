"""
openedx_proversity_reports  API URL Configuration
"""
from django.conf.urls import url

from . import views

REPORT_NAME_PATTERN = r'(?P<report_name>(generate)+[a-z-]+)'

urlpatterns = [
    url(
        r'^{report_name_pattern}$'.format(
            report_name_pattern=REPORT_NAME_PATTERN,
        ),
        views.GenerateReportView.as_view(),
        name='generate-report-view'
    ),
    url(
        r'^get-report-data$',
        views.GetReportView.as_view(),
        name='get-report-data'
    ),
    url(
        r'^salesforce-contact-id$',
        views.SalesforceContactId.as_view(),
        name='salesforce-contact-id',
    ),
]
