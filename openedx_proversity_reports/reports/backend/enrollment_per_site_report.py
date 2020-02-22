"""
Enrollment per site report backend.
"""
from importlib import import_module

from django.conf import settings
from opaque_keys.edx.keys import CourseKey
from rest_framework import status

from openedx_proversity_reports.google_services.bigquery_module import (
    get_google_bigquery_course_id,
    get_google_bigquery_data,
    GoogleBigQueryInformationError,
)
from openedx_proversity_reports.reports.backend.base import BaseReportBackend
from openedx_proversity_reports.edxapp_wrapper.get_courseware_library import student_module
from openedx_proversity_reports.edxapp_wrapper.get_student_library import user_attribute, user_signup_source
from openedx_proversity_reports.utils import get_course_enrollment, get_user_role

SUPPORTED_TASKS_MODULE = 'openedx_proversity_reports.tasks'

class EnrollmentReportPerSiteBackend(BaseReportBackend):
    """
    Report backend class.
    """
    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        # Import the task module directly to avoid circular import.
        super(EnrollmentReportPerSiteBackend, self).__init__(
            generate_report_data_task=getattr(
                import_module(SUPPORTED_TASKS_MODULE),
                'enrollment_per_site_report_task',
                None,
            ),
            user_serializer_fields=['username', 'email', 'date_joined'],
            include_staff_users=True,
            *args,
            **kwargs
        )

    def process_request(self, request, extra_data={}):  # pylint: disable=dangerous-default-value
        """
        Process the enrollment per site report request.
        Obtains the total of users in the provided site.

        Args:
            request: django.http.request.HttpRequest object.
            extra_data: Dict that contains additional data.
        Returns:
            BaseReportBackend.process_response object.
            HTTP_400_BAD_REQUEST object.
        """
        site_name = extra_data.get('site_name', '')

        if not site_name:
            return {
                'site_name': 'missing field.',
                'success': False,
                'status': status.HTTP_400_BAD_REQUEST,
            }

        users_created_on_site = user_attribute().objects.values('user').filter(name='created_on_site', value=site_name)
        # Support backwards compatibility with microsites.
        users_signup_source = user_signup_source().objects.values('user').filter(site=site_name)
        filter_users_on_site = set.union(
            set([created_on_site.get('user', '') for created_on_site in users_created_on_site]),
            set([signup_source.get('user', '') for signup_source in users_signup_source]),
        )

        extra_data.update({'registered_users': len(filter_users_on_site)})

        return super(EnrollmentReportPerSiteBackend, self).process_request(request, extra_data)


def generate_enrollment_per_site_report(course_key, enrolled_users):
    """
    Return the report data.

    Args:
        course_key: Opaque course key object.
        enrolled_users: List that contains information about the enrolled users.
    Returns:
        List of dicts: [{
            course: Course id value.
            username: User name value.
            email: User's email.
            date_of_enrollment: Enrollment date value.
            date_of_registration: Registration date value.
            role: User's course role.
        }]
    """
    report_data = []
    bigquery_data = list(
        get_google_bigquery_data(
            query_string=get_google_bigquery_query(
                course_dataset_name=get_google_bigquery_course_id(course_key),
                course_id=str(course_key),
            ),
        ),
    )

    for user in enrolled_users:
        enrollment = get_course_enrollment().objects.filter(
            user__email=user.get('email', ''),
            course_id=course_key,
        )
        first_student_module_object = student_module().objects.filter(
            student__username=user.get('username', ''),
            course_id=course_key,
        ).order_by('created').first()

        if not enrollment:
            continue

        time_spent_per_user = 0

        for time_spent_data in bigquery_data:
            if time_spent_data.get('username', '') == user.get('username', ''):
                time_spent_per_user = time_spent_data.get('total_time_spent', 0)

        report_data.append({
            'username': user.get('username', ''),
            'email': user.get('email', ''),
            'date_of_enrollment': str(enrollment[0].created),
            'date_of_registration': user.get('date_joined', ''),
            'role': get_user_role(enrollment[0].user, course_key),
            'time_spent': time_spent_per_user,
            'date_of_first_access_to_course': str(
                first_student_module_object.created,
            ) if first_student_module_object else '',
        })

    return report_data


def get_google_bigquery_query(course_dataset_name, course_id):
    """
    Return the Google BigQuery query for the time_on_asset_daily table.

    Args:
        course_dataset_name: Dataset name where the table is stored.
        date: Date to filter the query. Date format: '%Y-%m-%d' e.g. '2019-01-01'
        course_id: Course id string.
    Returns:
        query_string: The query string to make the query.
    Raises:
        GoogleBigQueryInformationError: If OPR_GOOGLE_CLOUD_PROJECT_ID or course_dataset_name
                                        were not provided or are None.
    """
    google_project_id = getattr(settings, 'OPR_GOOGLE_CLOUD_PROJECT_ID', '')
    query_max_result_number = getattr(settings, 'OPR_GOOGLE_BIGQUERY_MAX_NUMBER_RESULTS_PER_QUERY', 1000)

    if not google_project_id or not course_dataset_name:
        raise GoogleBigQueryInformationError('Google cloud project id or course_dataset_name are missing.')

    query_string = """
        SELECT username, SUM(time_umid30) AS total_time_spent
        FROM `{google_project_id}.{bigquery_dataset}.time_on_asset_daily`
        WHERE course_id = '{course_id}'
        AND time_umid30 IS NOT NULL
        GROUP BY username
        LIMIT {max_result_number}
    """.format(
        google_project_id=google_project_id,
        bigquery_dataset=course_dataset_name,
        course_id=course_id,
        max_result_number=query_max_result_number,
    )

    return query_string
