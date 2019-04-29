""" Backend abstraction """
from importlib import import_module
from django.conf import settings


def get_modulestore(*args, **kwargs):
    """ Get modulestore """

    backend_function = settings.OPR_MODULESTORE
    backend = import_module(backend_function)

    return backend.get_modulestore_backend(*args, **kwargs)
