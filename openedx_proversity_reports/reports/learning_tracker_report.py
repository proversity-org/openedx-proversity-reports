"""
Learning Tracker Report Class.
"""
import json
import logging
import six
from datetime import timedelta

from django.utils.functional import cached_property
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx_proversity_reports.edxapp_wrapper.get_block_structure_library import get_course_in_cache
from openedx_proversity_reports.edxapp_wrapper.get_certificates_models import (
    get_certificate_statuses,
    get_certificate_status_for_student
)
from openedx_proversity_reports.edxapp_wrapper.get_course_cohort import get_course_cohort
from openedx_proversity_reports.edxapp_wrapper.get_course_grade_library import (
    get_course_grade_factory,
    get_grading_context
)
from openedx_proversity_reports.edxapp_wrapper.get_course_teams import get_course_teams
from openedx_proversity_reports.edxapp_wrapper.get_courseware_library import get_course_by_id
from openedx_proversity_reports.edxapp_wrapper.get_student_library import get_user_profile
from openedx_proversity_reports.utils import get_enrolled_users


LOG = logging.getLogger(__name__)
KEY_SUBSECTION_BLOCK = 'subsection_block'


class LearningTrackerReport(object):
    """
    Learning Tracker Report Class.
    """

    def __init__(self, course_id):
        try:
            self.course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            LOG.error('Invalid course_id = %s for learning tracker report', course_id)
            raise InvalidKeyError

    @cached_property
    def assignments_data(self):
        """
        Cached property that returns the block structure.
        """
        blocks = get_course_in_cache(self.course_key)
        assignments_data = get_grading_context(get_course_by_id(self.course_key), blocks)

        return assignments_data.get('all_graded_subsections_by_type', {})

    def generate_report(self):
        """
        Returns a List with the metric for every user in the course.
        """
        enrolled_users = get_enrolled_users(self.course_key)
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
                'time_between_sessions': self._get_time_bewteen_sessions(user),
                'weekly_clicks': self._get_weekly_clicks(user),
                'number_of_graded_assessment': self._get_number_of_graded_assessment(user),
                'timeliness_of_submissions': self._get_timeliness_of_submissions(user),
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
        user_profile = get_user_profile().objects.get(user_id=user.id)

        try:
            meta = json.loads(user_profile.meta)
            return float(meta.get('avg_session', 0))
        except ValueError:
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

    def _get_number_of_graded_assessment(self, user):
        """
        Number of graded assignment submissions.
        Args:
            user: User Model.
        Returns:
            Int (Number of graded subsection that has an associated assignment type).
        """
        course_grade = get_course_grade_factory().read(user=user, course_key=self.course_key)
        count = 0

        for subsections_info in six.itervalues(self.assignments_data):
            for subsection_info in subsections_info:
                subsection = subsection_info.get(KEY_SUBSECTION_BLOCK)

                if not subsection:
                    continue

                subsection_grade = course_grade.subsection_grade(subsection.location)

                if subsection_grade.attempted_graded:
                    count += 1

        return count

    def _get_time_bewteen_sessions(self, user):
        """
        Calculate learner metrics for "Time between sessions".
        Args:
            user: User Model.
        Returns:
            Float (Time between sessions).
        """
        user_profile = get_user_profile().objects.get(user_id=user.id)

        try:
            meta = json.loads(user_profile.meta)
            return float(meta.get('time_between_sessions', 0))
        except ValueError:
            return 0

    def _get_timeliness_of_submissions(self, user):
        """
        The number of days that user submits assignments before the posted due date.
        Args:
            user: User Model.
        Returns:
            Int (Number of days).
        """
        course_grade = get_course_grade_factory().read(user=user, course_key=self.course_key)

        submissions_timeliness = timedelta()

        for subsections_info in six.itervalues(self.assignments_data):
            for subsection_info in subsections_info:
                subsection = subsection_info.get(KEY_SUBSECTION_BLOCK)

                if not subsection:
                    continue

                subsection_grade = course_grade.subsection_grade(subsection.location)
                first_attempted = subsection_grade.all_total.first_attempted

                if subsection_grade.attempted_graded and subsection.due and first_attempted:
                    submissions_timeliness += subsection.due - first_attempted

        return submissions_timeliness.days

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
        certificate = get_certificate_status_for_student(user, self.course_key)

        if certificate.get('status') in get_certificate_statuses().PASSED_STATUSES:
            return True

        return False
