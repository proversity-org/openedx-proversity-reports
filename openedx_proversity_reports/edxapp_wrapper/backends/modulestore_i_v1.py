""" Backend abstraction """
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError


def get_modulestore_backend(*args, **kwargs):  # pylint: disable=unused-argument
    """ Real backend to get modulestore """
    return modulestore()

def get_item_not_found_error():
    """ Real ItemNotFoundError modulestore exception. """
    return ItemNotFoundError
