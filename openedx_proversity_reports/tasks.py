"""
Task for Openedx Proversity Report plugin.
"""
import json

from celery import task
from celery.exceptions import InvalidTaskError
from celery.states import FAILURE
from django.contrib.auth.models import User
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import status

from openedx_proversity_reports.reports.last_page_accessed import (
    get_last_page_accessed_data,
    get_exit_count_data,
)
from openedx_proversity_reports.reports.enrollment_report import EnrollmentReport
from openedx_proversity_reports.reports.learning_tracker_report import LearningTrackerReport
from openedx_proversity_reports.reports.activity_completion_report import GenerateCompletionReport
from openedx_proversity_reports.reports.last_login_report import LastLoginReport
from openedx_proversity_reports.reports.time_spent_report import get_time_spent_report_data
from openedx_proversity_reports.serializers import ActivityCompletionReportSerializer
from openedx_proversity_reports.utils import (
    generate_report_as_list,
    get_root_block,
    get_enrolled_users,
)

BLOCK_DEFAULT_REPORT_FILTER = ['vertical']


@task(default_retry_delay=5, max_retries=5)  # pylint: disable=not-callable
def generate_completion_report(courses, *args, **kwargs):
    """
    Return the completion data for the given courses
    """
    block_report_filter = kwargs.get('block_report_filter', BLOCK_DEFAULT_REPORT_FILTER)
    data = {}

    for course_id in courses:
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            continue

        # Getting all users enrolled in the course.
        enrolled_users = User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1,
            courseaccessrole__id=None,
            is_staff=0,
        )

        if not enrolled_users:
            break

        block_root = get_root_block(enrolled_users.first(), course_key)
        course_data = generate_report_as_list(enrolled_users, course_key, block_report_filter, block_root)

        data[course_id] = course_data

    return data


@task(default_retry_delay=5, max_retries=5)  # pylint: disable=not-callable
def generate_last_page_accessed_report(courses, *args, **kwargs):
    """
    Return the last page accessed data for the given courses.

    The dictionary contains 'last_page_data' that contains information about the last problem
    or html or video, etc, that user has accessed.
    exit_count_data holds information about all units in the course and the count of how many users are in each unit.
    """
    report_data = {
        'last_page_data': {},
        'exit_count_data': {},
    }

    last_page_data = get_last_page_accessed_data(courses)
    if last_page_data:
        report_data['last_page_data'] = last_page_data
        report_data['exit_count_data'] = get_exit_count_data(last_page_data, courses)

    return report_data


@task(default_retry_delay=5, max_retries=5)  # pylint: disable=not-callable
def generate_time_spent_report(courses, *args, **kwargs):
    """
    Return the time spent data for the given courses.

    Args:
        courses: Course ids list.
    Returns:
        Dict with 'time_spent_data' containing time spent report data.
    """
    time_spent_report_data = get_time_spent_report_data(courses)

    return {
        'time_spent_data': time_spent_report_data if time_spent_report_data else {}
    }


@task(default_retry_delay=5, max_retries=5)  # pylint: disable=not-callable
def generate_learning_tracker_report(courses, *args, **kwargs):
    """
    Return the time spent data for the given courses.

    Args:
        courses: Course ids list.
    Returns:
        Dict with the data for every course.
    """
    data = {}

    for course in courses:
        try:
            data[course] = LearningTrackerReport(course).generate_report()
        except InvalidKeyError:
            continue

    return data


@task(default_retry_delay=5, max_retries=5)  # pylint: disable=not-callable
def generate_enrollment_report(courses, *args, **kwargs):
    """
    Return the enrollment data for the given courses.

    Args:
        courses: Course ids list.
    Returns:
        Dict with the enrollment data for every course.
    """
    data = {}

    for course in courses:
        try:
            data[course] = EnrollmentReport(course).generate_report(**kwargs)
        except InvalidKeyError:
            continue

    return data


@task(default_retry_delay=5, max_retries=5)
def generate_activity_completion_report(courses, *args, **kwargs):
    """
    Returns the activity completion report.
    """
    data = {}
    serialized_data = ActivityCompletionReportSerializer(data=kwargs)

    if not serialized_data.is_valid():
        # Raises the error containing the JsonResponse parameters
        # to be used in the view.
        raise InvalidTaskError(
            json.dumps({
                'data': {
                    'status': FAILURE,
                    'result': serialized_data.errors,
                },
                'status': status.HTTP_400_BAD_REQUEST,
            })
        )

    required_block_ids = serialized_data.data.get('required_activity_ids', [])
    block_types = serialized_data.data.get('block_types', [])
    passing_score = serialized_data.data.get('passing_score', [])

    for course_id in courses:
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            continue

        course_key = CourseKey.from_string(course_id)
        completion_report = GenerateCompletionReport(
            get_enrolled_users(course_key),
            course_key,
            required_block_ids,
            block_types,
            passing_score,
        )
        data[course_id] = completion_report.generate_report_data()


@task(default_retry_delay=5, max_retries=5)  # pylint: disable=not-callable
def generate_last_login_report(courses, *args, **kwargs):
    """
    Return the last login data for the given courses.

    Args:
        courses: Course ids list.
    Returns:
        Dict with the last login data for each course.
    """
    data = {}

    for course in courses:
        try:
            data[course] = LastLoginReport(course).generate_report_data(**kwargs)
        except InvalidKeyError:
            data[course] = ['Invalid course id value.']

    return data
