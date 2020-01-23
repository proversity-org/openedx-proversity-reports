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


def get_user(*args, **kwargs):
    """ Returns the get_user method. """

    backend_function = settings.OPR_STUDENT_LIBRARY
    backend = import_module(backend_function)

    return backend.get_user_helper(*args, **kwargs)


def get_course_enrollment():
    """ Get CourseEnrollment model. """

    backend_function = settings.OPR_STUDENT_LIBRARY
    backend = import_module(backend_function)

    return backend.course_enrollment()


def user_readonly_serializer(*args, **kwargs):
    """ Get UserReadOnlySerializer. """

    backend_function = settings.OPR_STUDENT_LIBRARY
    backend = import_module(backend_function)

    return backend.get_user_readonly_serializer(*args, **kwargs)


def user_attribute():
    """ Get the UserAttribute model. """

    backend_function = settings.OPR_STUDENT_LIBRARY
    backend = import_module(backend_function)

    return backend.get_user_attribute()


def user_signup_source():
    """ Get the UserSignupSource model. """

    backend_function = settings.OPR_STUDENT_LIBRARY
    backend = import_module(backend_function)

    return backend.get_user_signup_source()
