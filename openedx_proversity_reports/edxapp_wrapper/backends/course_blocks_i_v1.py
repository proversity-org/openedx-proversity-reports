""" Backend abstraction """
from lms.djangoapps.course_blocks.api import get_course_blocks


def get_course_blocks_backend(*args, **kwargs):
    """ Real backend to get course_blocks """
    return get_course_blocks(*args, **kwargs)
