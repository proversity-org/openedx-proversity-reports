""" Backend abstraction. """
from importlib import import_module
from django.conf import settings


def get_course_grade_factory(*args, **kwargs):  # pylint: disable=unused-argument
    """ Get CourseGradeFactory Class. """

    backend_function = settings.OPR_COURSE_GRADE_LIBRARY
    backend = import_module(backend_function)

    return backend.CourseGradeFactory()


def get_grading_context(*args, **kwargs):  # pylint: disable=unused-argument
    """ Get grading_context method. """

    backend_function = settings.OPR_COURSE_GRADE_LIBRARY
    backend = import_module(backend_function)

    return backend.grading_context(*args, **kwargs)
