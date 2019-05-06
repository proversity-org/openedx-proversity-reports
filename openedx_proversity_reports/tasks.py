"""
Task for Openedx Proversity Report plugin.
"""
from celery import task
from completion.models import BlockCompletion
from django.urls import reverse
from django.contrib.auth.models import User
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx_proversity_reports.utils import generate_report_as_list, get_root_block


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

        staff_users = User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1,
            is_staff=1,
        )
        if not staff_users:
            break
        block_root = get_root_block(staff_users[0], course_key)
        course_data = generate_report_as_list(enrolled_students, course_key, block_report_filter, block_root)

        data[course_id] = course_data

    return data


@task(default_retry_delay=5, max_retries=5)  # pylint: disable=not-callable
def generate_last_page_accessed_report(courses):
    """
    Return the last page accessed data for the given courses
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

        user_data = []
        for user in enrolled_students:
            last_completed_child_position = BlockCompletion.get_latest_block_completed(user, course_key)

            if last_completed_child_position:
                page_url = reverse(
                    'jump_to',
                    kwargs={
                        'course_id': last_completed_child_position.course_key,
                        'location': last_completed_child_position.block_key
                    }
                )
                user_data.append({
                    'username': user.username,
                    'last_time_accessed': str(last_completed_child_position.modified),
                    'page_url': page_url,
                })

        data[course_id] = user_data

    return data
