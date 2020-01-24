""" Backend abstraction """
from openedx.core.djangoapps.user_api.accounts.serializers import (
    UserReadOnlySerializer,
)
from student.auth import user_has_role
from student.models import (
    CourseAccessRole,
    CourseEnrollment,
    UserAttribute,
    UserProfile,
    UserSignupSource,
    get_user,
)
from student.roles import CourseStaffRole


def user_has_role_backend(*args, **kwargs):
    """ Real backend to get user_has_role method. """
    return user_has_role(*args, **kwargs)


def course_staff_role_backend(*args, **kwargs):
    """ Real backend to get course staff role. """
    return CourseStaffRole(*args, **kwargs)


def course_access_role():
    """ Returns CourseAccessRole model. """
    return CourseAccessRole


def user_profile():
    """ Returns UserProfile model. """
    return UserProfile


def course_enrollment():
    """ Returns CourseEnrollment model. """
    return CourseEnrollment


def get_user_helper(*args, **kwargs):
    """ Returns the get_user method. """
    return get_user(*args, **kwargs)


def get_user_readonly_serializer(*args, **kwargs):
    """ Returns the UserReadOnlySerializer. """
    return UserReadOnlySerializer(*args, **kwargs)


def get_user_attribute():
    """ Returns the UserAttribute model. """
    return UserAttribute


def get_user_signup_source():
    """ Returns the UserSignupSource model. """
    return UserSignupSource
