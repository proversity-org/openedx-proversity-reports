""" Backend abstraction """
from student.auth import user_has_role
from student.roles import CourseStaffRole
from student.models import CourseAccessRole


def user_has_role_backend(*args, **kwargs):
    """ Real backend to get user_has_role method. """
    return user_has_role(*args, **kwargs)


def course_staff_role_backend(*args, **kwargs):
    """ Real backend to get course staff role. """
    return CourseStaffRole(*args, **kwargs)


def course_access_role():
    """ Returns CourseAccessRole model. """
    return CourseAccessRole
