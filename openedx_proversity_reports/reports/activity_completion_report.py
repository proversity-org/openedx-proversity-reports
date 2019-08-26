"""
Activity completion report module.
"""
import logging

from openedx_proversity_reports.edxapp_wrapper.get_completion_models import \
    get_block_completion_model
from django.core.exceptions import ObjectDoesNotExist
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import BlockUsageLocator

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

    def __init__(self, users, course_key, required_block_ids):
        self.users = users
        self.course_key = course_key
        self.course = get_course_by_id(self.course_key)
        self.required_block_ids = self.get_course_required_block_ids(required_block_ids)


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
                'completed_activities': get_count_required_completed_activities(required_ids, completed_activities),
            }

            for index, item in enumerate(required_ids, 1):
                try:
                    locator = BlockUsageLocator.from_string(item)
                    state = is_activity_completed(locator.block_id, completed_activities)
                    block = get_modulestore().get_item(locator)
                    total_activities += 1
                except item_not_found_error() as item_error:
                    logger.warn(
                        'The block id %s is not valid, error: %s',
                        item,
                        item_error,
                    )
                    continue
                except InvalidKeyError:
                    continue

                data.update({
                    'Required Activity {}'.format(index): state,
                    'Required Activity {} Name'.format(index): block.display_name,
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

        Args:
            required_block_ids: List of the block location ids.
        Returns:
            required_course_block_ids:
                List containing only the block location ids,
                that belong to the same course key.
        """
        required_course_block_ids = []

        for required_block_id in required_block_ids:
            try:
                block_locator = BlockUsageLocator.from_string(required_block_id)

                if block_locator.course_key == self.course_key:
                    required_course_block_ids.append(required_block_id)
            except InvalidKeyError:
                continue

        return required_course_block_ids


def is_activity_completed(block_id, activities):
    """
    Verifies if the block_id exist for the given activity list.
    """
    for activity in activities:
        if block_id == activity.block_id:
            return 'completed'

    return 'not_completed'


def get_count_required_completed_activities(required_ids, activities):
    """
    Returns a counter with the number of required activities completed.
    """
    required_activity_count = 0

    for required_id in required_ids:
        required_block = BlockUsageLocator.from_string(required_id)

        for activity in activities:
            if required_block.block_id == activity.block_id:
                required_activity_count += 1

    return required_activity_count


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
