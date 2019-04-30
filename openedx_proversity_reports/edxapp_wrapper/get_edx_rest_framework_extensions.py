""" Backend abstraction """
from importlib import import_module
from django.conf import settings


def get_jwt_authentication(*args, **kwargs):  # pylint: disable=unused-argument
    """ Get JwtAuthentication Class """

    backend_function = settings.OPR_EDX_REST_FRAMEWORK_EXTENSIONS
    backend = import_module(backend_function)

    return backend.JwtAuthentication
