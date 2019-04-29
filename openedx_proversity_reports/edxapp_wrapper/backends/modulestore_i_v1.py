""" Backend abstraction """
from xmodule.modulestore.django import modulestore


def get_modulestore_backend(*args, **kwargs):  # pylint: disable=unused-argument
    """ Real backend to get modulestore """
    return modulestore()
