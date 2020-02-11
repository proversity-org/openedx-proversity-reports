""" Backend abstraction. """
from importlib import import_module
from django.conf import settings


def course_overview():
    """ Get the Course Overview model. """

    backend_function = settings.OPR_COURSE_CONTENT
    backend = import_module(backend_function)

    return backend.CourseOverview
