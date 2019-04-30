""" Backend abstraction """
from importlib import import_module
from django.conf import settings


def get_course_blocks(*args, **kwargs):
    """ Get course blocks """

    backend_function = settings.OPR_COURSE_BLOCKS
    backend = import_module(backend_function)

    return backend.get_course_blocks_backend(*args, **kwargs)
