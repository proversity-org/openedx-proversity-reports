"""
Task for Openedx Proversity Report plugin.
"""
from celery import task
from django.contrib.auth.models import User
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx_proversity_reports.utils import generate_report_as_list


@task(default_retry_delay=5, max_retries=5)  # pylint: disable=not-callable
def generate_completion_report(courses, block_report_filter):
    """
    Return the completion data for the given courses
    """
    data = {}
    for course_id in courses:
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            continue

        # Getting all students enrolled on the course except staff users
        enrolled_students = User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1,
            is_staff=0,
        )
        course_data = generate_report_as_list(enrolled_students, course_key, block_report_filter)

        data[course_id] = course_data

    return data
