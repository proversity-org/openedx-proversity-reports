""" Backend abstraction """
from lms.djangoapps.teams.models import CourseTeam


def get_course_teams_backend(*args, **kwargs):
    """ Real backend to get course_teams """
    return CourseTeam.objects.filter(*args, **kwargs)
