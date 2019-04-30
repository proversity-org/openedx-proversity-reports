""" Backend abstraction """
from importlib import import_module
from django.conf import settings


def get_staff_or_owner(*args, **kwargs):  # pylint: disable=unused-argument
    """ Get IsStaffOrOwner Class """

    backend_function = settings.OPR_OPENEDX_PERMISSIONS
    backend = import_module(backend_function)

    return backend.IsStaffOrOwner
