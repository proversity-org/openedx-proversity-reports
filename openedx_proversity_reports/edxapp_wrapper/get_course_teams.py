""" Backend abstraction """
from importlib import import_module
from django.conf import settings


def get_course_teams(*args, **kwargs):
    """ Get course teams """

    backend_function = settings.OPR_COURSE_TEAMS
    backend = import_module(backend_function)

    return backend.get_course_teams_backend(*args, **kwargs)
