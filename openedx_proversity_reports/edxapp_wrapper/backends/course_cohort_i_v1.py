""" Backend abstraction """
from openedx.core.djangoapps.course_groups.cohorts import get_cohort


def get_course_cohort_backend(*args, **kwargs):
    """ Real backend to get course cohorts """
    return get_cohort(*args, **kwargs)
