"""
Last login report backend.
"""
import logging

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx_proversity_reports.edxapp_wrapper.get_student_library import get_course_enrollment


LOG = logging.getLogger(__name__)


class LastLoginReport(object):
    """
    Last login report Class.
    """

    def __init__(self, course_id):
        try:
            self.course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            message = 'Invalid course_id: {} value for last login report'.format(course_id)
            LOG.error(message)
            raise InvalidKeyError(course_id, message)

    def generate_report_data(self, **kwargs):
        """
        Return a List with the information of the last login of the enrolled users.

        kwargs:
            date: Contains the python date format for the last login value.
        Returns:
            List: Containing the users enrolled in the course and their information.
        """
        report_data = []
        course_enrollments = get_course_enrollment().objects.filter(course_id=self.course_key)
        date_format = kwargs.get('date_format', '%Y-%m-%d')

        for enrollment in course_enrollments:
            user_last_login_date = enrollment.user.last_login.strftime(date_format)
            date_of_registration = enrollment.user.date_joined.strftime(date_format)

            report_data.append({
                'username': enrollment.user.username,
                'email': enrollment.user.email,
                'last_login_date': user_last_login_date,
                'date_of_registration': date_of_registration,
            })

        return report_data
