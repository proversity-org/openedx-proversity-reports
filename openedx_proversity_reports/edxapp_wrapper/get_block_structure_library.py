""" Backend abstraction. """
from importlib import import_module
from django.conf import settings


def get_course_in_cache(*args, **kwargs):
    """ Retuns the block structure for the given course id. """

    backend_function = settings.OPR_BLOCK_STRUCTURE_LIBRARY
    backend = import_module(backend_function)

    return backend.get_course_in_cache(*args, **kwargs)
