""" Backend abstraction. """
from openedx.core.djangoapps.models.course_details import CourseDetails


def get_course_details():
    """ CourseDetails object. """
    return CourseDetails
