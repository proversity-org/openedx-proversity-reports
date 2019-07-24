"""
Learning Tracker Report Class
"""
import logging

from django.contrib.auth.models import User
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx_proversity_reports.edxapp_wrapper.get_course_cohort import get_course_cohort
from openedx_proversity_reports.edxapp_wrapper.get_course_grade_factory import get_course_grade_factory
from openedx_proversity_reports.edxapp_wrapper.get_course_teams import get_course_teams


LOG = logging.getLogger(__name__)


class LearningTrackerReport(object):
    """
    Learning Tracker Report Class
    """

    def __init__(self, course_id):
        try:
            self.course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            LOG.error('Invalid course_id = %s for learning tracker report', course_id)
            raise InvalidKeyError

    def generate_report(self):
        """
        Returns a List with the metric for every user in the course.
        """
        enrolled_users = User.objects.filter(
            courseenrollment__course_id=self.course_key,
            courseenrollment__is_active=1,
            courseaccessrole__id=None,
            is_staff=0,
        )

        report_data = []

        if not enrolled_users:
            return report_data

        for user in enrolled_users:

            cohort = get_course_cohort(user=user, course_key=self.course_key)
            teams = get_course_teams(membership__user=user, course_id=self.course_key)

            user_data = {
                'username': user.username,
                'email': user.email,
                'user_id': user.id,
                'team': teams[0].name if teams else '',
                'cohort': cohort.name if cohort else '',
                'average_session_length': self._get_average_session_length(user),
                'cumulative_grade': self._get_cumulative_grade(user),
                'has_verified_certificate': self._has_verified_certificate(user),
                'time_bewteen_sessions': self._get_time_bewteen_sessions(user),
                'weekly_clicks': self._get_weekly_clicks(user),
            }

            report_data.append(user_data)

        return report_data

    def _get_average_session_length(self, user):
        """
        Calculate learner metric for "Average Session Length".
        Args:
            user: User Model.
        Returns:
            Float (Average Session Length).
        """
        return 0

    def _get_cumulative_grade(self, user):
        """
        The cumulative grade is the current grade that the student has in the course.
        Args:
            user: User Model.
        Returns:
            Float (cumulative_grade).
        """
        course_grade = get_course_grade_factory().read(user=user, course_key=self.course_key)
        return course_grade.percent

    def _get_time_bewteen_sessions(self, user):
        """
        Calculate learner metrics for "Time between sessions".
        Args:
            user: User Model.
        Returns:
            Float (Time between sessions).
        """
        return 0

    def _get_weekly_clicks(self, user):
        """
        Calculate the Number of times student clicked the edX course card per week.
        Args:
            user: User Model.
        Returns:
            Int (Number of clicks).
        """
        return 0

    def _has_verified_certificate(self, user):
        """
        Calculate whether the student has earned a verified certificate.
        Args:
            user: User Model.
        Returns:
            Boolean (True/False).
        """
        return False
