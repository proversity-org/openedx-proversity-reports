"""
openedx_proversity_reports  API URL Configuration
"""
from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^generate-completion-report$',
        views.GenerateCompletionReportView.as_view(),
        name='generate-completion-report'
    ),
    url(
        r'^completion-report-data$',
        views.CompletionReportView.as_view(),
        name='completion-report-data'
    ),
]
