""" Backend abstraction. """
from importlib import import_module
from django.conf import settings


def get_block_completion_model(*args, **kwargs):  # pylint: disable=unused-argument
    """ Get BlockCompletion Class. """

    backend_function = settings.OPR_COMPLETION_MODELS
    backend = import_module(backend_function)

    return backend.BlockCompletion
