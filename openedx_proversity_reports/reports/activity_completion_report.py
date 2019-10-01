"""
Activity completion report module.
"""
from __future__ import division
import logging

from django.core.exceptions import ObjectDoesNotExist
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import BlockUsageLocator

from openedx_proversity_reports.utils import get_required_activity_dict
from openedx_proversity_reports.edxapp_wrapper.get_block_structure_library import get_course_in_cache
from openedx_proversity_reports.edxapp_wrapper.get_completion_models import get_block_completion_model
from openedx_proversity_reports.edxapp_wrapper.get_courseware_library import get_course_by_id
from openedx_proversity_reports.edxapp_wrapper.get_modulestore import (
    get_modulestore,
    item_not_found_error,
)
from openedx_proversity_reports.edxapp_wrapper.get_student_library import get_user


logger = logging.getLogger(__name__)


class GenerateCompletionReport(object):
    """
    Class to generate the activity completion report.
    """
    course_block_structure = None

    def __init__(self, users, course_key, required_block_ids, block_types, passing_score):
        self.users = users
        self.course_key = course_key
        self.required_block_types = block_types
        self.required_block_ids = self.get_course_required_block_ids(required_block_ids)
        self.passing_score = passing_score


    @classmethod
    def activity_completion_data_per_user(cls, user, course_key, block_types, passing_score):
        """
        Returns the GenerateCompletionReport class by passing a default value to the required_block_ids argument.
        This is intended to use the same logic without change the class it all.
        Pass the users argument as a single user list, this is to maintain the naming convention and
        keep the type of the field, since it is supposed to be a list.
        """
        return cls(
            users=[user],
            course_key=course_key,
            required_block_ids=[],
            block_types=block_types,
            passing_score=passing_score,
        )


    @property
    def matching_blocks_by_type(self):
        """
        Returns blocks matching by self.block_type_filter.
        """
        try:
            block_structure = get_course_in_cache(self.course_key)
            matching_blocks = block_structure.topological_traversal(
                filter_func=self.block_type_filter,
                yield_descendants_of_unyielded=True,
            )
            self.course_block_structure = block_structure
        except item_not_found_error():
            return []

        return list(matching_blocks)


    def block_type_filter(self, block_item):
        """
        Returns True if the block type exists in the self.required_block_types otherwise False.

        Args:
            block_item: Course block item to be matched.
        """
        return True if block_item.block_type in self.required_block_types else False


    def generate_report_data(self):
        """
        Returns a dict with the users data per course.
        """
        activity_completion_data = []
        required_ids = self.required_block_ids

        for user in self.users:
            user, user_profile = get_user(user.email)
            first_name, last_name = get_first_and_last_name(user_profile.name)
            completed_activities = self.get_completed_activities(user)
            last_login = user.last_login
            display_last_login = None

            try:
                user_enrollment = user.courseenrollment_set.get(
                    course_id=self.course_key,
                )
            except ObjectDoesNotExist:
                continue

            # Last login could not be defined for a user.
            if last_login:
                display_last_login = last_login.strftime('%Y/%m/%d %H:%M:%S')

            total_activities = 0
            data = {
                'first_name': first_name,
                'last_name': last_name,
                'email': user.email,
                'first_login': user.date_joined.strftime('%Y/%m/%d %H:%M:%S'),
                'last_login': display_last_login,
                'completed_activities': len(filter_completed_blocks(
                    required_ids,
                    completed_activities,
                )),
                'course_is_complete': is_course_activities_complete(
                    required_ids,
                    completed_activities,
                    self.passing_score,
                ),
                'student_enrollment_id': user_enrollment.id,
            }

            for index, item in enumerate(required_ids, 1):
                state = is_activity_completed(item.block_id, completed_activities)
                total_activities += 1

                data.update({
                    'required_activity_{}'.format(index): state,
                    'required_activity_{}_name'.format(index): self.course_block_structure.get_xblock_field(
                        item,
                        'display_name',
                    ),
                })

            data.update({
                'total_activities': total_activities,
            })

            activity_completion_data.append(data)

        return activity_completion_data


    def get_completed_activities(self, user):
        """
        Returns blocks that have been completed by the user.
        """
        return get_block_completion_model().get_course_completions(user, self.course_key)


    def get_course_required_block_ids(self, required_block_ids):
        """
        Filters the required_block_ids list, and returns
        only the required block ids that belong to the same course key.

        If the self.matching_blocks_by_type is set, it returns a mix with required_block_ids
        which exists in self.matching_blocks_by_type too.

        If required_block_ids is not provided, it returns just the self.matching_blocks_by_type list.

        Args:
            required_block_ids: List of the block location ids.
        Returns:
            required_course_block_ids: List containing only the BlockUsageLocator items.
        """
        matching_blocks_by_type = self.matching_blocks_by_type

        if not required_block_ids:
            return matching_blocks_by_type

        required_course_block_ids = []

        for required_block_id in required_block_ids:
            try:
                block_locator = BlockUsageLocator.from_string(required_block_id)

                if not matching_blocks_by_type and block_locator.course_key == self.course_key:
                    required_course_block_ids.append(block_locator)
                    continue

                if block_locator in matching_blocks_by_type:
                    required_course_block_ids.append(block_locator)
            except InvalidKeyError:
                continue

        return required_course_block_ids


    def get_user_completion_data(self):
        """
        Returns the completion data per course for the class instance user.

        Returns:
            user_activity_completion_data: Dict containing the activity completion data.
        """
        activity_completion_data = self.generate_report_data()

        if not activity_completion_data:
            return {}

        user_activity_completion_data = {
            'total_activities': activity_completion_data[0].get('total_activities', 0),
            'course_is_complete': activity_completion_data[0].get('course_is_complete', False),
            'completed_activities': activity_completion_data[0].get('completed_activities', 0),
        }

        user_activity_completion_data.update(get_required_activity_dict(activity_completion_data[0]))

        return user_activity_completion_data


def is_activity_completed(block_id, activities):
    """
    Verifies if the block_id exist for the given activity list.
    """
    for activity in activities:
        if block_id == activity.block_id:
            return 'completed'

    return 'not_completed'


def get_first_and_last_name(full_name):
    """
    Takes the argument full_name a returns a list with the first name and last name.
    """
    try:
        result = full_name.split(' ', 1)
    except AttributeError:
        return ['', '']
    else:
        if len(result) == 2:
            return result
        return [full_name, full_name]


def is_course_activities_complete(course_blocks, completed_activities, passing_score):
    """
    Verifies if the course is complete depending on the total of the provided course_blocks,
    divided by the total of completed blocks if it is greater than or equal to passing_score.

    PASS = ( COUNT OF BLOCKS COMPLETED / COUNT OF TOTAL COURSE BLOCKS ) >= passing_score

    Args:
        course_blocks: All the required BlockUsageLocator items.
        completed_activities: All the BlockUsageLocator completion items per user.
        passing_score: Percentage of the completed activities.
    Retunrs:
        Boolean: True if the user has completed the course activities
            depending on the calculation, if not False.
    """
    required_completed_activities = filter_completed_blocks(
        course_blocks,
        completed_activities,
    )

    if not required_completed_activities:
        return False

    return (len(required_completed_activities) / len(course_blocks)) >= passing_score


def filter_completed_blocks(required_blocks, completed_activities):
    """
    Filters the activities completed by the required blocks.
    This is in order to get only the completed activities that exists in the
    required blocks.

    Args:
        required_blocks: All the requested BlockUsageLocator items.
        completed_activities: All the completed BlockUsageLocator items per user.
    Returns:
        required_block_filter_list: List with only the completed activities that exists
            in the required_blocks list.
    """
    required_block_filter_list = []

    for activity_block in required_blocks:
        for block_completed in completed_activities:
            if block_completed.block_id == activity_block.block_id:
                required_block_filter_list.append(block_completed)

    return required_block_filter_list
