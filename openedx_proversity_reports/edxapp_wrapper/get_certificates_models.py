""" Backend abstraction. """
from importlib import import_module
from django.conf import settings


def get_certificate_statuses(*args, **kwargs):  # pylint: disable=unused-argument
    """ Get CertificateStatuses class. """

    backend_function = settings.OPR_CERTIFICATES_MODELS
    backend = import_module(backend_function)

    return backend.CertificateStatuses


def get_certificate_status_for_student(*args, **kwargs):  # pylint: disable=unused-argument
    """ Get certificate_status_for_student method. """

    backend_function = settings.OPR_CERTIFICATES_MODELS
    backend = import_module(backend_function)

    return backend.certificate_status_for_student(*args, **kwargs)
