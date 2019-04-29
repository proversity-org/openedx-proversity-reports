"""
Utils file for Openedx Proversity Reports.
"""
from completion.models import BlockCompletion

from openedx_proversity_reports.edxapp_wrapper.get_course_blocks import get_course_blocks
from openedx_proversity_reports.edxapp_wrapper.get_modulestore import get_modulestore
from openedx_proversity_reports.edxapp_wrapper.get_supported_fields import get_supported_fields


def generate_report_as_list(users, course_key, block_report_filter):
    """
    Returns a list with the user information for every block in block_report_filter.
    """

    def verify_name(name, data):
        """
        This verifies if the name is already in use and generates a new one.
        """
        if name in data:
            identifier = name.split('-')[-1]
            try:
                number = int(identifier) + 1
                name = name.replace(identifier, str(number))
            except ValueError:
                name = "{}-{}".format(name, "1")

            name = verify_name(name, data)

        return name

    def update_user_dict(child, user_data, parent=None):
        """
        Returns the complete data for the given values.
        """
        if child.get("type") in block_report_filter:

            if parent:
                name = "{}-{}".format(parent.get('display_name'), child.get('display_name'))
            else:
                name = child.get('display_name')

            aux = user_data.get(child.get('type'), {})
            name = verify_name(name, aux)
            aux[name] = child.get('complete')

            user_data[child.get('type')] = aux

    data = []
    for user in users:
        root_block = get_root_block(user, course_key)
        sections = root_block.get('children', [])
        user_data = dict(
            username=user.username,
            user_id=user.id,
        )

        for section in sections:
            update_user_dict(section, user_data)
            for subsection in section.get('children', []):
                update_user_dict(subsection, user_data, section)
                for vertical in subsection.get('children', []):
                    update_user_dict(vertical, user_data, subsection)
                    for component in vertical.get('children', []):
                        update_user_dict(component, user_data, vertical)

        data.append(user_data)

    return data


def get_root_block(user, course_key):
    """
    Returns the content course as dict.
    """

    def populate_children(block, all_blocks):
        """
        Replace each child id with the full block for the child.

        Given a block, replaces each id in its children array with the full
        representation of that child, which will be looked up by id in the
        passed all_blocks dict. Recursively do the same replacement for children
        of those children.
        """
        children = block.get('children', [])

        for i in range(len(children)):
            child_id = block['children'][i]
            child_detail = populate_children(all_blocks[child_id], all_blocks)
            block['children'][i] = child_detail

        return block

    def mark_blocks_completed(block, user, course_key):
        """
        Walk course tree, marking block completion.
        Mark 'most recent completed block as 'resume_block'

        """
        last_completed_child_position = BlockCompletion.get_latest_block_completed(user, course_key)

        if last_completed_child_position:
            recurse_mark_complete(
                course_block_completions=BlockCompletion.get_course_completions(user, course_key),
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
            if block_key == latest_completion.full_block_key:
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

    mark_blocks_completed(root_block, user, course_key)

    return root_block
