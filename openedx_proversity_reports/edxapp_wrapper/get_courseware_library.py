""" Backend abstraction. """
from importlib import import_module
from django.conf import settings


def get_course_by_id(*args, **kwargs):
    """ Get the course for the given course id. """

    backend_function = settings.OPR_COURSEWARE_LIBRARY
    backend = import_module(backend_function)

    return backend.get_course_by_id(*args, **kwargs)


def student_module():
    """ Get StudentModule model. """

    backend_function = settings.OPR_COURSEWARE_LIBRARY
    backend = import_module(backend_function)

    return backend.StudentModule
