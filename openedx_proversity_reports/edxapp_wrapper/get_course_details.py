""" Backend abstraction. """
from importlib import import_module
from django.conf import settings


def get_course_details():
    """ Get the course details object. """

    backend_function = settings.OPR_COURSE_DETAILS
    backend = import_module(backend_function)

    return backend.get_course_details()
