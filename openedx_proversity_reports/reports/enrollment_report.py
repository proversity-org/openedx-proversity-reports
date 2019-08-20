"""
Enrollment Report Class.
"""
import logging

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx_proversity_reports.serializers import EnrollmentReportSerializer
from openedx_proversity_reports.edxapp_wrapper.get_course_details import get_course_details
from openedx_proversity_reports.edxapp_wrapper.get_student_account_library import \
    get_user_salesforce_contact_id
from openedx_proversity_reports.edxapp_wrapper.get_student_library import (
    get_course_enrollment,
    get_user_profile,
)

LOG = logging.getLogger(__name__)


class EnrollmentReport(object):
    """
    EnrollmentReport Class.
    """

    def __init__(self, course_id):
        try:
            self.course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            LOG.error('Invalid course_id = %s for enrollment report', course_id)
            raise InvalidKeyError

    def generate_report(self, **kwargs):
        """
        Returns a List with the enrollments for the given dates.
        """
        course_details = get_course_details().fetch(self.course_key)
        course_start_intake_of_intent = '{} {}'.format(
            course_details.start_date.strftime('%B'),
            course_details.start_date.strftime('%Y'),
        )
        enrollment_serializer = EnrollmentReportSerializer(data=kwargs)
        date_data = enrollment_serializer.validated_data if enrollment_serializer.is_valid() else {}
        updated_at = date_data.get('updated_at', '')
        oldest = date_data.get('oldest', '')
        latest = date_data.get('latest', '')
        course_enrollment_objects = get_course_enrollment().objects
        report_data = []

        if updated_at:
            course_enrollments = course_enrollment_objects.filter(
                created__year=updated_at.year,
                created__month=updated_at.month,
                created__day=updated_at.day,
                course_id=self.course_key,
            )
        elif oldest and latest:
            course_enrollments = course_enrollment_objects.filter(
                created__range=[oldest, latest],
                course_id=self.course_key,
            )
        elif oldest:
            course_enrollments = course_enrollment_objects.filter(
                created__gte=oldest,
                course_id=self.course_key,
            )
        elif latest:
            course_enrollments = course_enrollment_objects.filter(
                created__lte=latest,
                course_id=self.course_key,
            )
        else:
            course_enrollments = course_enrollment_objects.filter(course_id=self.course_key)

        for course_enrollment in course_enrollments:
            user = course_enrollment.user
            contact_id = get_user_salesforce_contact_id().objects.filter(user=user)
            user_profile = get_user_profile().objects.get(user_id=user.id)

            user_data = {
                'username': user.username,
                'full_name': user_profile.name if user_profile else '',
                'email': user.email,
                'user_id': user.id,
                "enrollment_date": str(course_enrollment.created),
                'mode': course_enrollment.mode,
                'is_active': course_enrollment.is_active,
                'contact_id': contact_id[0].contact_id if contact_id else '',
                'intake_of_intent': course_start_intake_of_intent,
            }

            report_data.append(user_data)

        return report_data
