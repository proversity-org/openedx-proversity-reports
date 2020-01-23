#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utils file for Openedx Proversity Reports.
"""
import copy
import logging
from importlib import import_module

from django.conf import settings
from django.contrib.auth.models import User

from openedx_proversity_reports.edxapp_wrapper.get_completion_models import get_block_completion_model
from openedx_proversity_reports.edxapp_wrapper.get_course_blocks import get_course_blocks
from openedx_proversity_reports.edxapp_wrapper.get_course_cohort import get_course_cohort
from openedx_proversity_reports.edxapp_wrapper.get_course_teams import get_course_teams
from openedx_proversity_reports.edxapp_wrapper.get_modulestore import get_modulestore
from openedx_proversity_reports.edxapp_wrapper.get_student_library import course_access_role, get_course_enrollment
from openedx_proversity_reports.edxapp_wrapper.get_supported_fields import get_supported_fields

logger = logging.getLogger(__name__)


def generate_report_as_list(users, course_key, block_report_filter, root_block):
    """
    Returns a list with the user information for every block in block_report_filter.
    """

    def update_user_dict(child, user_data, section=None, subsection=None, vertical=None):
        """
        Returns the complete data for the given values.
        """
        if child.get('type') in block_report_filter:

            type_data = user_data.get(child.get('type'), [])

            child_data = dict(
                name=child.get('display_name'),
                complete=child.get('complete'),
                number=child.get('position_number'),
            )

            if section and section != child:
                child_data['section_name'] = section.get('display_name')
                child_data['section_number'] = section.get('position_number')

            if subsection and subsection != child:
                child_data['subsection_name'] = subsection.get('display_name')
                child_data['subsection_number'] = subsection.get('position_number')

            if vertical and vertical != child:
                child_data['vertical_name'] = vertical.get('display_name')
                child_data['vertical_number'] = vertical.get('position_number')

            type_data.append(child_data)

            user_data[child.get('type')] = type_data

    data = []
    for user in users:
        block_data = copy.deepcopy(root_block)
        mark_blocks_completed(block_data, user, course_key)
        sections = block_data.get('children', [])
        cohort = get_course_cohort(user=user, course_key=course_key)
        user_teams = get_course_teams(membership__user=user, course_id=course_key)

        user_data = dict(
            username=user.username,
            user_id=user.id,
            cohort=cohort.name if cohort else '',
            team=user_teams[0].name if user_teams else '',
        )

        for section in sections:
            update_user_dict(section, user_data)
            for subsection in section.get('children', []):
                update_user_dict(subsection, user_data, section)
                for vertical in subsection.get('children', []):
                    update_user_dict(vertical, user_data, section, subsection)
                    for component in vertical.get('children', []):
                        update_user_dict(component, user_data, section, subsection, vertical)

        data.append(user_data)

    return data


def get_root_block(user, course_key):
    """
    Returns the content course as dict.
    """

    def populate_children(block, all_blocks, counter={}):
        """
        Replace each child id with the full block for the child.

        Given a block, replaces each id in its children array with the full
        representation of that child, which will be looked up by id in the
        passed all_blocks dict. Recursively do the same replacement for children
        of those children.
        """
        children = block.get('children', [])
        block_type = block.get("type")

        if block_type:
            counter[block_type] = counter.get(block_type, -1) + 1
            block['position_number'] = counter[block_type]

        for i in range(len(children)):
            child_id = block['children'][i]
            child_detail = populate_children(all_blocks[child_id], all_blocks, counter)
            block['children'][i] = child_detail

        return block

    block_types_filter = [
        'course',
        'chapter',
        'sequential',
        'vertical',
        'html',
        'problem',
        'video',
        'discussion',
        'drag-and-drop-v2',
        'poll',
        'word_cloud'
    ]

    requested_fields = [
        'children',
        'display_name',
        'type',
        'due',
        'graded',
        'format'
    ]

    usage_key = get_modulestore().make_course_usage_key(course_key)
    blocks = get_course_blocks(user, usage_key)

    if block_types_filter:
        block_keys_to_remove = []
        for block_key in blocks:
            block_type = blocks.get_xblock_field(block_key, 'category')
            if block_type not in block_types_filter:
                block_keys_to_remove.append(block_key)
        for block_key in block_keys_to_remove:
            blocks.remove_block(block_key, keep_descendants=True)

    block_data = {}

    for block_key in blocks:
        block = {
            'block_key': block_key,
            'id': unicode(block_key),
            'block_id': unicode(block_key.block_id),
            'resume_block': False,
            'complete': False
        }
        for supported_field in get_supported_fields():
            if supported_field.requested_field_name in requested_fields:
                field_value = blocks.get_xblock_field(block_key, supported_field.block_field_name)
                if field_value:
                    # only return fields that have data
                    block[supported_field.serializer_field_name] = field_value

        children = blocks.get_children(block_key)
        if children:
            block['children'] = [unicode(child) for child in children]

        block_data[unicode(block_key)] = block

    root_block = populate_children(block_data[unicode(blocks.root_block_usage_key)], block_data)

    return root_block


def mark_blocks_completed(block, user, course_key):
    """
    Walk course tree, marking block completion.
    Mark 'most recent completed block as 'resume_block'
    """
    last_completed_child_position = get_block_completion_model().get_latest_block_completed(user, course_key)

    if last_completed_child_position:
        recurse_mark_complete(
            course_block_completions=get_block_completion_model().get_course_completions(user, course_key),
            latest_completion=last_completed_child_position,
            block=block
        )


def recurse_mark_complete(course_block_completions, latest_completion, block):
    """
    Helper function to walk course tree dict,
    marking blocks as 'complete' and 'last_complete'

    If all blocks are complete, mark parent block complete
    mark parent blocks of 'last_complete' as 'last_complete'
    """
    block_key = block.get('block_key')

    if course_block_completions.get(block_key):
        block['complete'] = True
        if block_key == latest_completion.block_key:
            block['resume_block'] = True

    if block.get('children'):
        for idx in range(len(block['children'])):
            recurse_mark_complete(
                course_block_completions,
                latest_completion,
                block=block['children'][idx]
            )
            if block['children'][idx]['resume_block'] is True:
                block['resume_block'] = True

        completable_blocks = [child for child in block['children'] if child['type'] != 'discussion']
        if len([child['complete'] for child in block['children'] if child['complete']]) == len(completable_blocks):
            block['complete'] = True


def get_staff_user(course_key):
    """
    Returns the first staff user, to get the course structure.

    Args:
        course_key: Course key string.
    Returns:
        The first staff user of the course.
    """
    staff_user = User.objects.filter(
        courseenrollment__course_id=course_key,
        courseenrollment__is_active=1,
        courseaccessrole__role='staff',
    ).first()

    return staff_user


def get_user_role(user, course_key):
    """
    Returns the user string role.
    The default role value is 'student', other roles come from the course_access_role model.

    Args:
        user: Django user to find role.
        course_key: Course key string.
    Returns:
        The user role string.
    """
    user_role = 'student'
    user_course_role = course_access_role().objects.filter(
        user=user,
        course_id=course_key
    )

    if user_course_role:
        user_role = '-'.join([getattr(role, 'role', '') for role in user_course_role])

    return user_role


def get_enrolled_users(course_key, include_staff_users=False):
    """
    Return all the enrolled users for the given course key.

    Args:
        course_key: opaque_keys.edx.keys.CourseKey.
        include_staff_users: True to include course and platform staff users.
    Returns:
        Queryset of Users.
    """
    if include_staff_users:
        return User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1,
        )
    else:
        return User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1,
            courseaccessrole__id=None,
            is_staff=0,
        )


def get_attribute_from_module(module, attribute_name):
    """
    Return the attribute for the given module path and attribute name.

    Args:
        module: String (Module path).
        attribute_name: String (Module attribute).
    Returns:
        Module Attribute.
    """
    module = import_module(module)
    return getattr(module, attribute_name, None)


def get_exisiting_users_by_email(user_email_list):
    """
    Return a list of django.contrib.auth.models.User instances of users
    that exists in the platform.

    Args:
        user_email_list: List containing the emails of the users.
    Returns:
        exisiting_user_list: List containing django.contrib.auth.models.User instances.
    """
    exisiting_user_list = []

    for user_email in user_email_list:
        try:
            exisiting_user_list.append(User.objects.get(email=user_email))
        except User.DoesNotExist:
            continue

    return exisiting_user_list


def get_user_course_enrollments(user):
    """
    Return a list of course keys of the courses where the user is enrolled.

    Args:
        user: django.contrib.auth.models.User instance.
    Returns:
        List containing opaque_keys.edx.keys.CourseKey course instances.
    """
    course_enrollment_objects = get_course_enrollment().objects
    user_course_enrollments = course_enrollment_objects.filter(
        user__id=user.id,
        user__courseaccessrole__id=None,
    )

    return [course_enrollment.course_id for course_enrollment in user_course_enrollments]


def get_required_activity_dict(user_data):
    """
    Create a dict with the required activity data.

    Args:
        user_data: Activity completion report data per course.
    Returns:
        Dict containing activities info.
        {
            'Multiple Choice': 'completed',
            'Image Explorer': 'completed',
            'Video': 'not_completed'
        }
    """
    required_activities_data = {}
    total_activities = user_data.get('total_activities', 0)

    if total_activities:
        total = int(total_activities)
        # Create as many 'required_activity_' as the total number of activities.
        for activity_number in range(1, total + 1): # Plus 1, because the stop argument it's not inclusive.
            required_activity_status = user_data.get('required_activity_{}'.format(activity_number), 'not_completed')
            required_activity_name = user_data.get('required_activity_{}_name'.format(activity_number), '')

            # Let's add the activity number at the end of the name if two or more activities have the same name.
            if required_activity_name in required_activities_data.keys():
                required_activity_name = '{}-{}'.format(required_activity_name, activity_number)

            required_activities_data.update({
                required_activity_name: required_activity_status,
            })

    return required_activities_data


def get_report_backend(requested_report_name):
    """
    Return the correspondent report backend for the requested report.

    Args:
        requested_report_name: Name of the requested report.
    """
    report_name = requested_report_name.replace('-', '_')
    supported_backend_reports = getattr(settings, 'OPR_SUPPORTED_REPORTS_BACKENDS', {})

    if not (supported_backend_reports or report_name in supported_backend_reports):
        logging.warn(
            'Either OPR_SUPPORTED_REPORTS_BACKENDS was not provided or the report backend was not configured.',
        )
        return None

    report_backend_settings = supported_backend_reports.get(report_name, {})
    report_backend_value = report_backend_settings.get('backend', '').split(':')

    try:
        backend_module = import_module(report_backend_value[0])
        report_backend = getattr(backend_module, report_backend_value[-1], None)
    except IndexError:
        logging.warn('Report backend not found. %s', report_backend_value)
        report_backend = None

    return report_backend, report_backend_settings
