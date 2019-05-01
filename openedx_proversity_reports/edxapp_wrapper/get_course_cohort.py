""" Backend abstraction """
from importlib import import_module
from django.conf import settings


def get_course_cohort(*args, **kwargs):
    """ Get course cohorts """

    backend_function = settings.OPR_COURSE_COHORT
    backend = import_module(backend_function)

    return backend.get_course_cohort_backend(*args, **kwargs)
