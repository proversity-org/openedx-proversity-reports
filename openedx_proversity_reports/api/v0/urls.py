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
    url(
        r'^generate-last-page-accessed-report$',
        views.GenerateLastPageReportView.as_view(),
        name='generate-last-page-accessed-report'
    ),
    url(
        r'^last-page-accessed-report-data$',
        views.LastPageReportView.as_view(),
        name='last-page-accessed-report-data'
    ),
]
