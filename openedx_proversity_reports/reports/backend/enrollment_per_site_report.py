"""
Enrollment per site report backend.
"""
from importlib import import_module

from opaque_keys.edx.keys import CourseKey
from rest_framework import status

from openedx_proversity_reports.reports.backend.base import BaseReportBackend
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

    def process_request(self, request, extra_data={}):
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
                'site_name': 'This field is required.',
                'success': False,
                'status': status.HTTP_400_BAD_REQUEST,
            }

        created_on_site_count = user_attribute().objects.filter(name='created_on_site', value=site_name).count()
        # Support backwards compatibility with microsites.
        signup_source_count = user_signup_source().objects.filter(site=site_name).count()

        extra_data.update({'registered_users': created_on_site_count + signup_source_count})

        return super(EnrollmentReportPerSiteBackend, self).process_request(request, extra_data)


def generate_enrollment_per_site_report(course_key, enrolled_users):
    """
    Return the report data.

    Args:
        course_key: Course id string.
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
    opaque_course_key = CourseKey.from_string(course_key)
    report_data = []

    for user in enrolled_users:
        enrollment = get_course_enrollment().objects.filter(
            user__email=user.get('email', ''),
            course_id=opaque_course_key,
        )

        if not enrollment:
            continue

        report_data.append({
            'course': course_key,
            'username': user.get('username', ''),
            'email': user.get('email', ''),
            'date_of_enrollment': str(enrollment[0].created),
            'date_of_registration': user.get('date_joined', ''),
            'role': get_user_role(enrollment[0].user, opaque_course_key),
        })

    return report_data
