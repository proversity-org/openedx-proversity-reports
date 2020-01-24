"""
Module that contains the report backend base class.
"""
from celery import task
from django.conf import settings
from rest_framework import status
from rest_framework.reverse import reverse

from openedx_proversity_reports.edxapp_wrapper.get_student_library import (
    user_readonly_serializer,
)
from openedx_proversity_reports.utils import get_enrolled_users


class BaseReportBackend(object):
    """
    Report backend base class.
    """
    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        self.settings = kwargs.pop('report_settings', {})
        self.course_ids = kwargs.pop('course_ids', [])
        self.course_keys = kwargs.pop('course_keys', [])
        self.limit = kwargs.pop('limit', getattr(settings, 'OPR_DEFAULT_PAGE_RESULTS_LIMIT', 10))
        self.user_serializer_configuration = kwargs.pop('user_serializer_configuration', [])
        self.user_serializer_fields = kwargs.pop('user_serializer_fields', [])
        self.generate_report_data_task = kwargs.pop('generate_report_data_task', generate_report_data)
        self.include_staff_users = kwargs.pop('include_staff_users', False)

    def process_request(self, request, extra_data):
        """
        Process the report generation request.
        Manage the report pagination by the enrolled users.

        Args:
            request: django.http.request.HttpRequest object.
            extra_data: Dict that contains additional data.
        Returns:
            BaseReportBackend.process_response object.
        """
        get_report_data_url = request.build_absolute_uri(reverse('proversity-reports:api:v1:get-report-data'))
        course_report_pages = {}

        for course_key in self.course_keys:
            enrolled_users_pages = self.get_pages_from_enrolled_users(
                enrolled_users=get_enrolled_users(course_key, self.include_staff_users),
            )
            report_pages = []

            for enrolled_users_page in enrolled_users_pages:
                user_serializer = user_readonly_serializer(
                    configuration=self.user_serializer_configuration,
                    custom_fields=self.user_serializer_fields,
                    context={'request': request},
                )
                serialized_enrollments = [user_serializer.to_representation(user) for user in enrolled_users_page]
                report_task = self.generate_report_data_task.delay(
                    extra_data=extra_data,
                    course_key=unicode(course_key),
                    enrolled_users=self.clean_serialized_enrollment_data(serialized_enrollments),
                )

                report_pages.append('{}?task_id={}'.format(get_report_data_url, report_task.id))

            course_report_pages.update({
                str(course_key): report_pages,
            })

        return self.process_response(report_pages=course_report_pages)

    def process_response(self, *args, **kwargs):
        """
        Process the report generation response.

        Kwargs:
            report_pages: Dict that contains the pages of the report.
        Return:
            Dict: {
                data: Contains the course pages for the report.
                success: Indicates a successful request.
                status: HTTP status code.
            }
        """
        return {
            'data': kwargs.pop('report_pages', {}),
            'success': True,
            'status': status.HTTP_202_ACCEPTED,
        }

    def get_pages_from_enrolled_users(self, enrolled_users):
        """
        Return a list of lists of the enrolled users
        organized in groups determined by the requested report limit or the configured limit.

        Args:
            enrolled_users: List of the users enrolled in the course.
        Returns:
            List of list:
                [
                    ['user one', 'user two', 'user three', 'user four'],
                    ['user one', ...], ...
                ]
        """
        max_results_per_page = self.settings.get(
            'max_results_per_page',
            getattr(settings, 'OPR_DEFAULT_PAGE_RESULTS_LIMIT', 10),
        )
        page_limit = self.limit if self.limit <= max_results_per_page else max_results_per_page
        enrolled_users_pages = []

        for cursor_index in range(0, len(enrolled_users), page_limit):
            enrolled_users_pages.append(enrolled_users[cursor_index:cursor_index + page_limit])

        return enrolled_users_pages

    def clean_serialized_enrollment_data(self, serialized_enrollment_data):
        """
        Try converting enrollment data to string values
        to avoid problems when passing the data to Celery.
        """
        clean_data = []

        for user_data in serialized_enrollment_data:
            try:
                clean_data.append({item: str(value) for item, value in user_data.items()})
            except Exception:  # pylint disable:broad-exception
                continue

        return clean_data


@task()
def generate_report_data(*args, **kwargs):  # pylint: disable=unused-argument
    """
    Celery task to generate the report data.
    """
    raise NotImplementedError('Define the task for the requested report data.')
