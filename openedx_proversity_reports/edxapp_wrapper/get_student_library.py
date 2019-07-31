""" Backend abstraction """
from importlib import import_module
from django.conf import settings


def user_has_role(*args, **kwargs):
    """ Get user_has_role method. """

    backend_function = settings.OPR_STUDENT_LIBRARY
    backend = import_module(backend_function)

    return backend.user_has_role_backend(*args, **kwargs)


def get_course_staff_role(*args, **kwargs):
    """ Get staff role. """

    backend_function = settings.OPR_STUDENT_LIBRARY
    backend = import_module(backend_function)

    return backend.course_staff_role_backend(*args, **kwargs)


def course_access_role():
    """ Get CourseAccessRole model. """

    backend_function = settings.OPR_STUDENT_LIBRARY
    backend = import_module(backend_function)

    return backend.course_access_role()


def get_user_profile():
    """ Get UserProfile model. """

    backend_function = settings.OPR_STUDENT_LIBRARY
    backend = import_module(backend_function)

    return backend.user_profile()
