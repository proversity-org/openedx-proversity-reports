""" Backend abstraction """
from importlib import import_module
from django.conf import settings


def get_supported_fields(*args, **kwargs):  # pylint: disable=unused-argument
    """ Get SUPPORTED FIELDS """

    backend_function = settings.OPR_SUPPORTED_FIELDS
    backend = import_module(backend_function)

    return backend.SUPPORTED_FIELDS
