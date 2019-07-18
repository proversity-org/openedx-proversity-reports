"""
Last page accessed reports.
"""
from django.contrib.auth.models import User
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx_proversity_reports.edxapp_wrapper.get_completion_models import get_block_completion_model
from openedx_proversity_reports.edxapp_wrapper.get_course_blocks import get_course_blocks
from openedx_proversity_reports.edxapp_wrapper.get_course_cohort import get_course_cohort
from openedx_proversity_reports.edxapp_wrapper.get_course_teams import get_course_teams
from openedx_proversity_reports.edxapp_wrapper.get_modulestore import get_modulestore


def get_last_page_accessed_data(course_list):
    """
    Returns a dict with information about the last page accessed
    by the student according to completion model.

    {
        'course-id': [{
            'username': User name,
            'last_time_accessed': Date string,
            'last_page_viewed': String of the problem's parent block tree,
            'block_id': Block id of the lastest block accessed by the student,
            'vertical_block_id': Parent vertical block id,
        }]
    }
    """
    last_page_data = {}

    for course_id in course_list:
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            continue

        # Getting all students enrolled in the course except staff users
        enrolled_students = User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1,
            courseaccessrole__id=None,
            is_staff=0,
        )

        if not enrolled_students:
            continue

        user_data = []
        usage_key = get_modulestore().make_course_usage_key(course_key)
        blocks = get_course_blocks(enrolled_students.first(), usage_key)

        for user in enrolled_students:
            last_completed_child_position = get_block_completion_model().get_latest_block_completed(
                user,
                course_key
            )
            parent_tree_name = ''
            vertical_block_id = ''

            if last_completed_child_position:
                user_course_cohort = get_course_cohort(user=user, course_key=course_key)
                user_course_teams = get_course_teams(membership__user=user, course_id=course_key)
                vertical_blocks = blocks.topological_traversal(
                    filter_func=lambda block_key: block_key.block_type == 'vertical',
                    yield_descendants_of_unyielded=True,
                )

                for vertical in vertical_blocks:
                    for component in blocks.get_children(vertical):
                        if component.block_id == last_completed_child_position.block_key.block_id:
                            parent_tree_name = '-'.join(get_parent_display_names(blocks, component))
                            component_parent = blocks.get_parents(component)
                            vertical_block_id = component_parent[0].block_id

                user_data.append({
                    'username': user.username,
                    'user_cohort': user_course_cohort.name if user_course_cohort else '',
                    'user_teams': user_course_teams[0].name if user_course_teams else '',
                    'last_time_accessed': str(last_completed_child_position.modified),
                    'last_page_viewed': parent_tree_name,
                    'block_id': last_completed_child_position.block_key.block_id,
                    'vertical_block_id': vertical_block_id,
                })

        if user_data:
            last_page_data[course_id] = user_data

    return last_page_data


def get_parent_tree(root_block, unit_block):
    """
    Util function to get the parent block tree of the provided unit_block.
    """
    vertical_parent = root_block.get_parents(unit_block)
    sequential_parent = root_block.get_parents(vertical_parent[0])
    chapter_parent = root_block.get_parents(sequential_parent[0])
    parent_tree = [chapter_parent[0], sequential_parent[0], vertical_parent[0], unit_block]

    return parent_tree


def get_parent_display_names(root_block, component):
    """
    Gets the parent display names of the provided component.
    """
    parent_tree = get_parent_tree(root_block, component)
    display_names = []
    for block in parent_tree:
        display_name = root_block.get_xblock_field(block, 'display_name')
        display_names.append(unicode(display_name))

    return display_names


def get_exit_count_data(last_page_data, course_list):
    """
    Returns a dict containing all units in the each provided course_list.
    Also return how many users are in each unit according to last_page_data data.

    {
        course_id: [{
            'page_title': Chapter-Sequential-Vertical name,
            'vertical_id': Vertical block id,
            'exit_count': Number of users in this unit
        }]
    }
    """

    course_unit_data = {}

    for course_id in course_list:
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            continue

        # Getting just the first enrolled user except staff users.
        enrolled_student = User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1,
            courseaccessrole__id=None,
            is_staff=0,
        ).first()

        if not enrolled_student:
            continue

        usage_key = get_modulestore().make_course_usage_key(course_key)
        blocks = get_course_blocks(enrolled_student, usage_key)
        course_block_data = []

        course_last_page_data = last_page_data.get(course_id)
        if course_last_page_data:
            course_blocks = blocks.topological_traversal()
            course_blocks = list(course_blocks)
            chapter_name = ''
            chapter_position = 0
            sequential_name = ''
            vertical_name = ''
            incremental_vertical_position = 0

            for block in course_blocks:
                if block.block_type == 'chapter':
                    chapter_name = blocks.get_xblock_field(block, 'display_name')
                    chapter_position += 1
                    continue
                if block.block_type == 'sequential':
                    sequential_name = blocks.get_xblock_field(block, 'display_name')
                    continue
                if block.block_type == 'vertical':
                    vertical_name = blocks.get_xblock_field(block, 'display_name')
                    vertical_id = block.block_id
                    page_title = '-'.join([chapter_name, sequential_name, vertical_name])
                    # The vertical position must be only incremental.
                    incremental_vertical_position += 1

                    course_block_data.append({
                        'page_title': unicode(page_title),
                        'vertical_id': vertical_id,
                        'exit_count': 0,
                        'vertical_position': incremental_vertical_position,
                        'chapter_name': '{}-{}'.format(chapter_position, chapter_name),
                    })

        if course_block_data:
            for vertical_block in course_block_data:
                exit_count = vertical_block.get('exit_count')

                for last_page in course_last_page_data:
                    if last_page.get('vertical_block_id') == vertical_block.get('vertical_id'):
                        exit_count += 1
                vertical_block['exit_count'] = exit_count

            course_unit_data[course_id] = course_block_data

    return course_unit_data
